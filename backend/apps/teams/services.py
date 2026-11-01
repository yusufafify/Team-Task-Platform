from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import F, ProtectedError, QuerySet
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.tasks.models import Task
from apps.teams.models import Team, TeamMembership

User = get_user_model()
LEADER = TeamMembership.Role.LEADER


def teams_for(user: User) -> QuerySet[Team]:
    return (
        Team.objects.filter(memberships__user=user)
        .annotate(role=F("memberships__role"))
        .order_by("name", "id")
    )


def get_membership(user: User, team_id: int) -> TeamMembership:
    """Raises 404, not 403, so a stranger can't learn that a team exists."""
    membership = TeamMembership.objects.select_related("team").filter(user=user, team_id=team_id)
    if not (found := membership.first()):
        raise NotFound()
    return found


def require_leader(user: User, team_id: int) -> TeamMembership:
    membership = get_membership(user, team_id)
    if membership.role != LEADER:
        raise PermissionDenied("Only a team leader can do this.")
    return membership


def create_team(actor: User, **fields) -> Team:
    with transaction.atomic():
        team = Team.objects.create(**fields)
        TeamMembership.objects.create(team=team, user=actor, role=LEADER)
    return team


def update_team(actor: User, team: Team, **fields) -> Team:
    require_leader(actor, team.pk)
    for field, value in fields.items():
        setattr(team, field, value)
    team.save(update_fields=list(fields))
    return team


def delete_team(actor: User, team: Team) -> None:
    require_leader(actor, team.pk)
    try:
        team.delete()
    except ProtectedError as error:
        raise ValidationError(
            {"non_field_errors": ["Only a team with no tasks or messages can be deleted."]}
        ) from error


def list_members(user: User, team_id: int) -> QuerySet[TeamMembership]:
    get_membership(user, team_id)
    return (
        TeamMembership.objects.filter(team_id=team_id)
        .select_related("user")
        .order_by("joined_at", "id")
    )


def add_member(actor: User, team_id: int, *, email: str, role: str) -> TeamMembership:
    require_leader(actor, team_id)
    user = User.objects.filter(email=User.objects.normalize_email(email), is_active=True).first()
    if user is None:
        raise ValidationError({"email": ["No account uses this email."]})
    membership, created = TeamMembership.objects.get_or_create(
        team_id=team_id, user=user, defaults={"role": role}
    )
    if not created:
        raise ValidationError({"email": ["This user is already on the team."]})
    return membership


def _ensure_another_leader(team_id: int) -> None:
    # The lock stops two leaders from demoting each other at the same moment.
    leaders = TeamMembership.objects.select_for_update().filter(team_id=team_id, role=LEADER)
    if len(leaders) < 2:
        raise ValidationError({"non_field_errors": ["A team needs at least one leader."]})


def change_member_role(actor: User, team_id: int, user_id: int, *, role: str) -> TeamMembership:
    require_leader(actor, team_id)
    with transaction.atomic():
        membership = get_object_or_404(
            TeamMembership.objects.select_related("user"), team_id=team_id, user_id=user_id
        )
        if membership.role == LEADER and role != LEADER:
            _ensure_another_leader(team_id)
        membership.role = role
        membership.save(update_fields=["role"])
    return membership


def remove_member(actor: User, team_id: int, user_id: int) -> None:
    require_leader(actor, team_id)
    with transaction.atomic():
        membership = get_object_or_404(TeamMembership, team_id=team_id, user_id=user_id)
        if membership.role == LEADER:
            _ensure_another_leader(team_id)
        # Done tasks keep their assignee, because they count toward history and stats.
        Task.objects.filter(team_id=team_id, assignee_id=user_id).exclude(
            status=Task.Status.DONE
        ).update(assignee=None, updated_at=timezone.now())
        membership.delete()

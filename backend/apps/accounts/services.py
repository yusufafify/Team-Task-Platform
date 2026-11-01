from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

User = get_user_model()


def register_user(*, email: str, password: str, first_name: str = "", last_name: str = "") -> User:
    email = User.objects.normalize_email(email)
    candidate = User(email=email, first_name=first_name, last_name=last_name)
    try:
        validate_password(password, candidate)
    except DjangoValidationError as error:
        raise ValidationError({"password": error.messages}) from error
    try:
        with transaction.atomic():
            return User.objects.create_user(
                email, password, first_name=first_name, last_name=last_name
            )
    except IntegrityError as error:
        # The unique constraint, not a prior check, so two racing signups can't both get through.
        raise ValidationError({"email": ["This email is already registered."]}) from error


def revoke_all_tokens(user: User) -> None:
    """The way out of a theft: covers refresh tokens the user no longer holds a copy of."""
    active = OutstandingToken.objects.filter(user=user, blacklistedtoken__isnull=True)
    BlacklistedToken.objects.bulk_create(
        [BlacklistedToken(token=token) for token in active], ignore_conflicts=True
    )

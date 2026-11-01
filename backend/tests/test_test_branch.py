import pytest
from django.db import connection


@pytest.mark.django_db
def test_runs_on_a_temporary_database():
    with connection.cursor() as cursor:
        cursor.execute("select current_database()")
        assert cursor.fetchone()[0].startswith("test_")

import django
import pytest

@pytest.fixture(scope="session", autouse=True)
def django_setup():
    django.setup()

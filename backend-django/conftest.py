import pytest
from rest_framework.test import APIClient
from django.contrib.auth.models import User

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def create_user():
    def _create_user(username='testuser', email='test@example.com', password='password123', is_staff=False):
        user = User.objects.create_user(username=username, email=email, password=password)
        user.is_staff = is_staff
        user.save()
        return user
    return _create_user

@pytest.fixture
def auth_client():
    client = APIClient()
    # Usa o token de dev definido em KeycloakAuthentication
    client.credentials(HTTP_AUTHORIZATION='Bearer dev-token-bypass')
    return client

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User


@pytest.fixture
def create_user(db):
    """Creates a test user."""
    user = User.objects.create_user(username='testuser', password='password123')
    return user


@pytest.fixture
def get_tokens(create_user):
    """Generate access and refresh tokens for the test user."""
    user = create_user
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


@pytest.mark.django_db
def test_jwt_access_token_authentication(create_user, get_tokens):
    """Test JWT Access Token authentication."""
    client = APIClient()
    access_token = get_tokens['access']

    # Add access token to the Authorization header
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

    # Send a request to a protected endpoint
    response = client.get('/protected-endpoint/')  # Replace with your endpoint

    assert response.status_code == 200
    assert response.json() == {"message": "Success"}


@pytest.mark.django_db
def test_jwt_refresh_token(create_user, get_tokens):
    """Test JWT Refresh Token functionality."""
    client = APIClient()
    refresh_token = get_tokens['refresh']

    # Refresh the access token using the refresh token
    response = client.post('/api/token/refresh/', data={'refresh': refresh_token})

    assert response.status_code == 200
    assert 'access' in response.data


@pytest.mark.django_db
def test_invalid_access_token():
    """Test authentication with an invalid access token."""
    client = APIClient()
    invalid_token = "invalid.jwt.token"

    # Add invalid token to the Authorization header
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {invalid_token}')

    # Send a request to a protected endpoint
    response = client.get('/protected-endpoint/')  # Replace with your endpoint

    assert response.status_code == 401
    assert response.data['detail'] == 'Given token not valid for any token type'


@pytest.mark.django_db
def test_invalid_refresh_token():
    """Test refreshing with an invalid refresh token."""
    client = APIClient()
    invalid_refresh_token = "invalid.refresh.token"

    # Attempt to refresh the access token with an invalid refresh token
    response = client.post('/api/token/refresh/', data={'refresh': invalid_refresh_token})

    assert response.status_code == 401
    assert response.data['detail'] == 'Token is invalid or expired'
    

class SampleTestCase(APITestCase):
    def test_example(self):
        self.assertEqual(1 + 1, 2)


class JWTAuthenticationTest(APITestCase):
    def setUp(self):
        # 테스트 유저 생성
        self.username = 'testuser'
        self.password = 'testpassword'
        self.user = User.objects.create_user(username=self.username, password=self.password)

        # 토큰 발행 URL
        self.token_url = '/api/token/'
        self.refresh_url = '/api/token/refresh/'
        self.protected_url = '/api/protected/'

    def test_token_obtain_pair(self):
        """Access Token 및 Refresh Token 발행 테스트"""
        response = self.client.post(self.token_url, {
            'username': self.username,
            'password': self.password
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.access_token = response.data['access']
        self.refresh_token = response.data['refresh']

    def test_protected_view_with_valid_token(self):
        """유효한 Access Token으로 보호된 API에 접근"""
        response = self.client.post(self.token_url, {
            'username': self.username,
            'password': self.password
        })
        access_token = response.data['access']

        # Authorization 헤더에 Access Token 전달
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(self.protected_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_protected_view_with_invalid_token(self):
        """유효하지 않은 Access Token으로 보호된 API에 접근"""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalidtoken')
        response = self.client.get(self.protected_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token(self):
        """Refresh Token을 사용하여 새로운 Access Token 발행"""
        response = self.client.post(self.token_url, {
            'username': self.username,
            'password': self.password
        })
        refresh_token = response.data['refresh']

        response = self.client.post(self.refresh_url, {'refresh': refresh_token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

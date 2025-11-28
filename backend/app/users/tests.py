import pytest
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestUserAuthentication(TestCase):
    """Test user authentication endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_user_registration(self):
        """Test user registration"""
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpass123",
            "password2": "newpass123",
            "first_name": "New",
            "last_name": "User",
        }
        response = self.client.post("/api/v1/users/register/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["username"], "newuser")

    def test_user_login(self):
        """Test user login and JWT token generation"""
        data = {"username": "testuser", "password": "testpass123"}
        response = self.client.post("/api/auth/login/", data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_get_user_profile(self):
        """Test getting user profile"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/v1/users/profile/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "testuser")

    def test_change_password(self):
        """Test password change"""
        self.client.force_authenticate(user=self.user)
        data = {"old_password": "testpass123", "new_password": "newtestpass123"}
        response = self.client.post("/api/v1/users/change-password/", data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify new password works
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newtestpass123"))

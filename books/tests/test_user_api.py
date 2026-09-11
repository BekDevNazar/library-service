from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


registration_url = reverse("users:registration")
token_url = reverse("users:token_obtain_pair")
url_manager = reverse("users:user_manager")


class UserApiTests(APITestCase):
    def test_create_user(self):
        url = reverse("users:registration")

        data = {
            "email": "test@test.com",
            "password": "testpass123",
            "first_name": "Test",
            "last_name": "User",
        }

        response = self.client.post(url, data)

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        user = get_user_model().objects.get(
            email="test@test.com"
        )

        self.assertTrue(
            user.check_password("testpass123")
        )
        self.assertNotEqual(
            user.password,
            "testpass123"
        )

    def test_get_access_refresh_token(self):
        user_data = {
            "email": "test@test.com",
            "password": "testpass123",
            "first_name": "Test",
            "last_name": "User",
        }

        self.client.post(
            registration_url,
            user_data,
        )

        response = self.client.post(
            token_url,
            {
                "email": "test@test.com",
                "password": "testpass123",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_me_not_available_without_jwt(self):

        data = {
            "first_name": "test123"
        }
        response = self.client.patch(url_manager, data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_available_with_jwt(self):
        user_data = {
            "email": "test@test.com",
            "password": "testpass123",
            "first_name": "Test",
            "last_name": "User",
        }

        self.client.post(registration_url, user_data)

        token_response = self.client.post(
            token_url,
            {
                "email": "test@test.com",
                "password": "testpass123",
            },
        )

        access_token = token_response.data["access"]

        self.client.credentials(
            HTTP_AUTHORIZE=f"Bearer {access_token}"
        )

        response_1 = self.client.get(url_manager)

        response_2 = self.client.patch(
            url_manager,
            {
                "first_name": "Test12",
            },
        )

        self.assertEqual(
            response_1.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response_2.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response_2.data["first_name"],
            "Test12",
        )

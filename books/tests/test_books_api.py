from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

from books.models import Book


url = reverse("books:book-list")

class BookTest(APITestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user(
            email="admin@test.com",
            password="test123",
            is_staff=True,
        )

        self.book = Book.objects.create(
            title="1984",
            author="George Orwell",
            cover=Book.CoverChoose.HARD,
            inventory=3,
            daily_fee="2.50",
        )

    def test_get_books_list(self):
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "1984")

    def test_create_book(self):
        self.client.force_authenticate(self.admin)
        data = {
            "title": "Animal Farm",
            "author": "George Orwell",
            "cover": "soft",
            "inventory": 5,
            "daily_fee": "3.00",
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Book.objects.filter(title="Animal Farm").exists()
        )

    def test_cannot_create_book_with_negative_inventory(self):
        self.client.force_authenticate(self.admin)
        data = {
            "title": "Test Book",
            "author": "Test Author",
            "cover": "hard",
            "inventory": -1,
            "daily_fee": "2.00",
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_book_detail(self):
        url_detail = reverse("books:book-detail", args=[self.book.id])

        response = self.client.get(url_detail)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "1984")
        self.assertEqual(response.data["author"], "George Orwell")

    def test_anonymous_cannot_create_book(self):
        data = {
            "title": "Animal Farm",
            "author": "George Orwell",
            "cover": "soft",
            "inventory": 5,
            "daily_fee": "3.00",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

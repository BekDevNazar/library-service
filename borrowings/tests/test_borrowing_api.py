from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from books.models import Book
from borrowings.models import Borrowing


BORROWING_LIST_URL = reverse("borrowings:borrowing-list")


class BorrowingApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="testpass123",
        )

        self.book = Book.objects.create(
            title="1984",
            author="George Orwell",
            cover=Book.CoverChoose.HARD,
            inventory=3,
            daily_fee="2.50",
        )

        self.borrowing = Borrowing.objects.create(
            expected_return_date=timezone.localdate() + timedelta(days=7),
            book=self.book,
            user=self.user,
        )

    def test_get_borrowing_list(self):
        response = self.client.get(BORROWING_LIST_URL)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(len(response.data), 1)

    def test_get_borrowing_detail(self):
        url = reverse(
            "borrowings:borrowing-detail",
            args=[self.borrowing.id],
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data["id"],
            self.borrowing.id,
        )

    def test_borrowing_contains_detailed_book_info(self):
        response = self.client.get(BORROWING_LIST_URL)

        book_data = response.data[0]["book"]

        self.assertEqual(
            book_data["title"],
            "1984",
        )
        self.assertEqual(
            book_data["author"],
            "George Orwell",
        )
        self.assertEqual(
            book_data["inventory"],
            3,
        )

    def test_expected_return_date_cannot_be_before_borrow_date(self):
        borrowing = Borrowing(
            borrow_date=timezone.localdate(),
            expected_return_date=timezone.localdate() - timedelta(days=1),
            book=self.book,
            user=self.user,
        )

        self.assertRaises(ValidationError, borrowing.save)

    def test_actual_return_date_cannot_be_before_borrow_date(self):
        borrowing = Borrowing(
            borrow_date=timezone.localdate(),
            expected_return_date=timezone.localdate() + timedelta(days=7),
            actual_return_date=timezone.localdate() - timedelta(days=1),
            book=self.book,
            user=self.user,
        )

        self.assertRaises(ValidationError, borrowing.save)
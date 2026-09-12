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


def return_borrowing_url(borrowing_id):
    return reverse(
        "borrowings:borrowing-book-return",
        args=[borrowing_id],
    )


class BorrowingApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="testpass123",
        )

        self.other_user = get_user_model().objects.create_user(
            email="test1@test.com",
            password="testpass1123",
        )

        self.book = Book.objects.create(
            title="1984",
            author="George Orwell",
            cover=Book.CoverChoose.HARD,
            inventory=3,
            daily_fee="2.50",
        )
        self.other_borrowing = Borrowing.objects.create(
            borrow_date=timezone.localdate(),
            expected_return_date=timezone.localdate() + timedelta(days=7),
            book=self.book,
            user=self.other_user,
        )
        self.borrowing = Borrowing.objects.create(
            expected_return_date=timezone.localdate() + timedelta(days=7),
            book=self.book,
            user=self.user,
        )
        self.client.force_authenticate(user=self.user)

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

    def test_borrowing_list_not_available_without_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(BORROWING_LIST_URL)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_user_can_see_only_his_borrowing(self):
        response = self.client.get(BORROWING_LIST_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["id"],
            self.borrowing.id,
        )

    def test_user_cannot_use_filter_user_id(self):
        url = f"{BORROWING_LIST_URL}?user_id={self.other_user.id}"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["id"],
            self.borrowing.id,
        )

    def test_admin_can_see_all_borrowings(self):
        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])

        response = self.client.get(BORROWING_LIST_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_admin_can_see_exactly_needed_user(self):
        url = f"{BORROWING_LIST_URL}?user_id={self.other_user.id}"
        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["id"],
            self.other_borrowing.id
        )

    def test_filter_active_borrowings(self):
        Borrowing.objects.create(
            borrow_date=timezone.localdate(),
            expected_return_date=timezone.localdate() + timedelta(days=7),
            actual_return_date=timezone.localdate(),
            book=self.book,
            user=self.user,
        )

        url = f"{BORROWING_LIST_URL}?is_active=true"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["id"],
            self.borrowing.id,
        )

    def test_filter_inactive_borrowings(self):
        returned_borrowing = Borrowing.objects.create(
            borrow_date=timezone.localdate(),
            expected_return_date=timezone.localdate() + timedelta(days=7),
            actual_return_date=timezone.localdate(),
            book=self.book,
            user=self.user,
        )

        url = f"{BORROWING_LIST_URL}?is_active=false"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["id"],
            returned_borrowing.id,
        )

    def test_admin_can_filter_by_user_and_active_status(self):
        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])

        Borrowing.objects.create(
            borrow_date=timezone.localdate(),
            expected_return_date=timezone.localdate() + timedelta(days=7),
            actual_return_date=timezone.localdate(),
            book=self.book,
            user=self.other_user,
        )

        url = (
            f"{BORROWING_LIST_URL}"
            f"?user_id={self.other_user.id}&is_active=true"
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["id"],
            self.other_borrowing.id,
        )

    def test_return_borrowing(self):
        initial_inventory = self.book.inventory

        url = return_borrowing_url(self.borrowing.id)
        response = self.client.post(url)

        self.borrowing.refresh_from_db()
        self.book.refresh_from_db()

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            self.borrowing.actual_return_date,
            timezone.localdate(),
        )
        self.assertEqual(
            self.book.inventory,
            initial_inventory + 1,
        )

    def test_cannot_return_borrowing_twice(self):
        initial_inventory = self.book.inventory
        url = return_borrowing_url(self.borrowing.id)

        first_response = self.client.post(url)
        second_response = self.client.post(url)

        self.book.refresh_from_db()

        self.assertEqual(
            first_response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            second_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            self.book.inventory,
            initial_inventory + 1,
        )

    def test_user_cannot_return_other_user_borrowing(self):
        initial_inventory = self.book.inventory

        url = return_borrowing_url(self.other_borrowing.id)
        response = self.client.post(url)

        self.other_borrowing.refresh_from_db()
        self.book.refresh_from_db()

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertIsNone(
            self.other_borrowing.actual_return_date,
        )
        self.assertEqual(
            self.book.inventory,
            initial_inventory,
        )

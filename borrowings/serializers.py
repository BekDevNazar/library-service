from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from books.models import Book
from books.serializers import BookSerializer
from borrowings.models import Borrowing


class BorrowingReadSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)

    class Meta:
        model = Borrowing
        fields = [
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user",
        ]


class BorrowingCreateSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        book = attrs["book"]
        expected_return_date = attrs["expected_return_date"]

        if book.inventory <= 0:
            raise serializers.ValidationError(
                {"book": "This book is not available."}
            )

        if expected_return_date < timezone.localdate():
            raise serializers.ValidationError(
                {
                    "expected_return_date":
                    "Expected return date cannot be earlier than borrow date."
                }
            )
        return attrs

    def create(self, validated_data):
        with transaction.atomic():
            book = Book.objects.select_for_update().get(pk=validated_data["book"].pk)
            if book.inventory <= 0:
                raise serializers.ValidationError(
                    {"book": "This book is not available."}
                )
            book.inventory -= 1
            book.save(update_fields=["inventory"])
            borrowing = Borrowing.objects.create(
                expected_return_date=validated_data["expected_return_date"],
                book=book,
                user=self.context["request"].user
            )

            return borrowing

    class Meta:
        model = Borrowing
        fields = ["book", "expected_return_date"]

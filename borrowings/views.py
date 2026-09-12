from django.db import transaction
from rest_framework.decorators import action
from rest_framework import mixins, viewsets, status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from rest_framework.response import Response

from books.models import Book
from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingCreateSerializer,
    BorrowingReadSerializer,
)


class BorrowingViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.action == "create":
            return BorrowingCreateSerializer

        return BorrowingReadSerializer

    def get_queryset(self):
        queryset = Borrowing.objects.select_related("book", "user")
        user = self.request.user

        if not user.is_staff:
            queryset = queryset.filter(user=user)

        is_active = self.request.query_params.get("is_active", None)

        if is_active == "true":
            queryset = queryset.filter(actual_return_date__isnull=True)
        elif is_active == "false":
            queryset = queryset.filter(actual_return_date__isnull=False)

        user_id = self.request.query_params.get("user_id", None)
        if user_id and user.is_staff:
            queryset = queryset.filter(user_id=user_id)

        return queryset

    @action(
        methods=["POST"],
        detail=True,
        url_path="return",
    )
    def book_return(self, request, pk=None):
        borrow = self.get_object()

        with transaction.atomic():
            borrow = (
                Borrowing.objects
                .select_for_update()
                .get(pk=borrow.pk)
            )

            if borrow.actual_return_date is not None:
                return Response(
                    {"detail": "This book has already been returned."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            book = (
                Book.objects
                .select_for_update()
                .get(pk=borrow.book_id)
            )

            book.inventory += 1
            book.save(update_fields=["inventory"])

            borrow.actual_return_date = timezone.localdate()
            borrow.save(update_fields=["actual_return_date"])

            serializer = BorrowingReadSerializer(borrow)

            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
            )

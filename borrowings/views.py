from django.contrib.auth.models import AbstractUser
from rest_framework import mixins, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated

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
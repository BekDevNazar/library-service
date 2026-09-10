from rest_framework import viewsets

from books.models import Book
from books.serializers import BookSerializer


class BookViews(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

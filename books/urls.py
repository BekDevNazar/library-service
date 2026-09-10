from django.urls import path
from rest_framework.routers import DefaultRouter

from books.views import BookViews


app_name = "books"
router = DefaultRouter()
router.register("books", BookViews)


urlpatterns = router.urls

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users.views import UserCreateView, ManageUserView


app_name = "users"
urlpatterns = [
    path("", UserCreateView.as_view(), name="registration"),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path("me/", ManageUserView.as_view(), name="user_manager")
]
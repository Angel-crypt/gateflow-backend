from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.users.views import ChangePasswordView, CustomTokenObtainPairView, LogoutView, MeView, UserListCreateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/login/", CustomTokenObtainPairView.as_view()),
    path("auth/refresh/", TokenRefreshView.as_view()),
    path("auth/logout/", LogoutView.as_view()),
    path("auth/me/", MeView.as_view()),
    path("auth/change-password/", ChangePasswordView.as_view()),
    path("api/users/", UserListCreateView.as_view()),
    path("api/destinations/", include("apps.destinations.urls")),
]

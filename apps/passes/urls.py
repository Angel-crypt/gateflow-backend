from django.urls import path

from .views import AccessPassDetailView, AccessPassListCreateView, AccessPassValidateView

urlpatterns = [
    path("", AccessPassListCreateView.as_view()),
    path("<int:pk>/", AccessPassDetailView.as_view()),
    path("validate/", AccessPassValidateView.as_view()),
]
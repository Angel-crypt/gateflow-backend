from django.urls import path

from .views import AccessLogCreateView, AccessLogDetailView, AccessLogListView

urlpatterns = [
    path("", AccessLogListView.as_view()),
    path("create/", AccessLogCreateView.as_view()),
    path("<int:pk>/", AccessLogDetailView.as_view()),
]
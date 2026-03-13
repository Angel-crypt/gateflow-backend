from django.urls import path

from .views import DestinationDetailView, DestinationListCreateView

urlpatterns = [
    path("", DestinationListCreateView.as_view()),
    path("<int:pk>/", DestinationDetailView.as_view()),
]

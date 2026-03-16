from django.urls import path

from .views import DestinationDetailView, DestinationListCreateView, IndustrialParkListView

urlpatterns = [
    path("", DestinationListCreateView.as_view()),
    path("<int:pk>/", DestinationDetailView.as_view()),
    path("parks/", IndustrialParkListView.as_view()),
]

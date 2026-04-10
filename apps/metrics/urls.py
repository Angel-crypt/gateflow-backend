from django.urls import path

from .views import AccessLogMetricsView, AccessTableView, DashboardMetricsView, PassMetricsView

urlpatterns = [
    path("dashboard/", DashboardMetricsView.as_view()),
    path("access-logs/", AccessLogMetricsView.as_view()),
    path("passes/", PassMetricsView.as_view()),
    path("access-table/", AccessTableView.as_view()),
]

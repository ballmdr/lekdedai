from django.urls import path

from qa import views

app_name = "qa"

urlpatterns = [
    path("health/", views.health, name="health"),
    path("metrics/", views.metrics_view, name="metrics"),
]

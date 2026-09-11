from django.urls import path

from qa import views

app_name = "qa"

urlpatterns = [
    path("health/", views.health, name="health"),
    path("metrics/", views.metrics_view, name="metrics"),
    # Task 30: ประตูปิด closed beta
    path("beta/", views.beta_gate, name="beta_gate"),
    path("beta/closed/", views.beta_closed, name="beta_closed"),
]

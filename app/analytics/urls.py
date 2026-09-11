from django.urls import path

from . import views

app_name = "analytics"

urlpatterns = [
    path("analytics/event/", views.collect_event, name="collect_event"),
]

from django.urls import path
from . import views

app_name = 'notebook'

urlpatterns = [
    path('', views.notebook_page, name='index'),
]

from django.urls import path
from . import views

app_name = 'dreams'

urlpatterns = [
    path('', views.dream_form, name='form'),
    path('analyze/', views.analyze_dream, name='analyze'),
]
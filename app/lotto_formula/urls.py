from django.urls import path
from . import views

app_name = 'lotto_formula'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('formula/<int:pk>/', views.FormulaDetailView.as_view(), name='formula_detail'),
    path('calculator/', views.calculator_view, name='calculator'),
    path('api/calculate/', views.calculate_numbers, name='calculate_numbers'),
    path('api/stats/', views.api_stats, name='api_stats'),
    path('api/formula/<int:formula_id>/', views.api_formula_detail, name='api_formula_detail'),
]

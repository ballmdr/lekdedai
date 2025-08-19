from django.urls import path
from . import views

app_name = 'ai_engine'

urlpatterns = [
    path('', views.ai_prediction_page, name='prediction'),
    path('api/predict/', views.api_predict, name='api_predict'),
    path('prediction/<int:prediction_id>/', views.prediction_detail, name='prediction_detail'),
    path('prediction/<int:prediction_id>/feedback/', views.add_feedback, name='add_feedback'),
    path('history/', views.ai_history, name='history'),
    path('accuracy/', views.ai_accuracy, name='accuracy'),
]
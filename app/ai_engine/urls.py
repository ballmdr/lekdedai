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
    
    # New AI Ensemble URLs
    path('ensemble/prediction/<int:prediction_id>/', views.ensemble_prediction_detail, name='ensemble_prediction_detail'),
    path('ensemble/history/', views.ensemble_history, name='ensemble_history'),
    path('data-sources/', views.data_sources, name='data_sources'),
    path('data-source/<int:source_id>/', views.data_source_detail, name='data_source_detail'),
    path('dashboard/', views.system_dashboard, name='dashboard'),
    
    # API endpoints
    path('api/refresh-data-sources/', views.api_refresh_data_sources, name='api_refresh_data_sources'),
    path('api/data-source/<int:source_id>/collect/', views.api_trigger_data_collection, name='api_trigger_data_collection'),
]
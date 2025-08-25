from django.urls import path
from . import views

app_name = 'lotto_stats'

urlpatterns = [
    path('', views.statistics_page, name='statistics'),
    path('api/hot-cold/', views.api_hot_cold_numbers, name='api_hot_cold'),
    path('api/number/<str:number>/', views.api_number_detail, name='api_number_detail'),
    path('api/sync/status/', views.api_sync_status, name='api_sync_status'),
    path('api/sync/data/', views.api_sync_data, name='api_sync_data'),
    path('api/sync/date/', views.api_sync_specific_date, name='api_sync_specific_date'),
]
from django.urls import path
from . import views

app_name = 'lottery_checker'

urlpatterns = [
    path('', views.index, name='index'),
    path('api/lotto/result/', views.lotto_result_api, name='lotto_result_api'),
    path('api/lotto/latest/', views.latest_results_api, name='latest_results_api'),
    path('api/lotto/date/<int:year>/<int:month>/<int:day>/', views.specific_date_api, name='specific_date_api'),
    path('api/lotto/clear/', views.clear_data_api, name='clear_data_api'),
    path('api/lotto/statistics/', views.statistics_api, name='statistics_api'),
    path('api/lotto/check/', views.check_number, name='check_number'),
    path('api/check/', views.check_lottery_quick, name='check_lottery_quick'),
    path('api/lotto/refresh/', views.refresh_lotto_data_api, name='refresh_lotto_data_api'),
    path('api/lotto/bulk-fetch/', views.bulk_fetch_api, name='bulk_fetch_api'),
]

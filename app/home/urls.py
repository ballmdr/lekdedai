from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('api/instant-lucky-numbers/', views.instant_lucky_numbers_api, name='instant_lucky_numbers_api'),
    path('api/recent-news-selection/', views.get_recent_news_for_selection_api, name='recent_news_selection_api'),
    path('api/daily-numbers-status/', views.daily_numbers_status_api, name='daily_numbers_status_api'),
]
# urls.py (โค้ดที่แก้ไขแล้ว)
from django.urls import path
from . import views

app_name = 'news'

urlpatterns = [
    path('', views.news_list, name='news_list'),
    path('article/<str:slug>/', views.article_detail, name='article_detail'), 
    path('lucky-hints/', views.lucky_hints, name='lucky_hints'),
    path('article/<str:slug>/comment/', views.add_comment, name='add_comment'), 
    path('api/analyze/<int:article_id>/', views.analyze_news, name='analyze_news'),
    path('api/insight/<int:article_id>/', views.insight_ai_analysis, name='insight_ai_analysis'),
]
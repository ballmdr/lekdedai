from django.urls import path
from . import views

app_name = 'lucky_spots'

urlpatterns = [
    path('', views.map_view, name='map'),
    path('api/locations/', views.locations_api, name='locations_api'),
    path('api/locations/search/', views.locations_search_api, name='locations_search_api'),
    path('<slug:slug>/', views.location_detail, name='location_detail'),
    path('<slug:slug>/comment/', views.add_comment, name='add_comment'),
]
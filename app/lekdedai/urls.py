from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    path('dreams/', include('dreams.urls')),
    path('lotto_stats/', include('lotto_stats.urls')),
    path('news/', include('news.urls')),
    path('ai/', include('ai_engine.urls')),
    path('lottery_checker/', include('lottery_checker.urls')),
    path('lucky-spots/', include('lucky_spots.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
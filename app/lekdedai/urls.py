from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),                              # Main homepage with lottery predictions
    path('dreams/', include('dreams.urls')),                     # Dream interpretation feature
    path('lotto_stats/', include('lotto_stats.urls')),           # Historical lottery statistics
    path('lotto_formula/', include('lotto_formula.urls')),       # Lottery formula calculator
    path('news/', include('news.urls')),                         # News analysis for lottery numbers
    path('ai/', include('ai_engine.urls')),                      # AI-powered predictions
    path('lottery_checker/', include('lottery_checker.urls')),   # Online lottery checker
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
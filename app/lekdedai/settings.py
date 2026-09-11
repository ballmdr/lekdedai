import os
from pathlib import Path
import dj_database_url
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# Task 22: SECRET_KEY มาจาก env เท่านั้น — ห้ามใช้ค่า default ใน production
SECRET_KEY = os.environ.get('SECRET_KEY', '')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'django-insecure-dev-only-do-not-use-in-production'
    else:
        raise ImproperlyConfigured('SECRET_KEY must be set when DEBUG=False')

# Task 22: host/origin จาก env ตรงกับ domain จริง (default  local เท่านั้น)
ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
    if h.strip()
]
CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',')
    if o.strip()
]

# Task 22: security flags เปิดผ่าน env ใน production เท่านั้น
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'False') == 'True'
SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False') == 'True'
CSRF_COOKIE_SECURE = os.environ.get('CSRF_COOKIE_SECURE', 'False') == 'True'
SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', '0'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get('SECURE_HSTS_INCLUDE_SUBDOMAINS', 'False') == 'True'
SECURE_HSTS_PRELOAD = os.environ.get('SECURE_HSTS_PRELOAD', 'False') == 'True'

# Task 27: security/performance headers ใน production
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'

# Task 31: อยู่หลัง nginx/Cloudflare — เชื่อ X-Forwarded-Proto เพื่อให้ is_secure()/CSRF ถูกต้อง
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Task 27: static caching — WhiteNoise เสิร์ฟ static พร้อม cache นาน
# (production เท่านั้น; DEV ปล่อยให้ Django เสิร์ฟเพื่อ autoreload)
WHITENOISE_MAX_AGE = 0 if DEBUG else 31536000

# Task 30: closed beta — ปิดประตูเว็บจนกว่าจะมี invite code
# BETA_MODE=True หรือ ROLLOUT_STAGE=beta/pct10 จะเปิดประตู (ดู qa/rollout.py)
BETA_MODE = os.environ.get('BETA_MODE', 'False') == 'True'
# รหัสเชิญตั้งต้นจาก env คั่นด้วยจุลภาค (seed ลง DB ตอน redeem อัตโนมัติ)
BETA_INVITE_CODES = [
    c.strip() for c in os.environ.get('BETA_INVITE_CODES', '').split(',') if c.strip()
]
# Task 30: cache สถานะ beta/health กันยิง DB ทุก request (วินาที)
BETA_STATUS_CACHE_SECONDS = int(os.environ.get('BETA_STATUS_CACHE_SECONDS', '60'))

# Task 31: staged rollout — beta -> pct10 -> public + kill switch
ROLLOUT_STAGE = os.environ.get('ROLLOUT_STAGE', 'public').strip().lower()
ROLLOUT_PERCENT = int(os.environ.get('ROLLOUT_PERCENT', '10'))
# ปิดเว็บชั่วคราว (kill switch) — staff ยังเข้าได้ normal user เห็นหน้าปิด
ROLLOUT_KILL_SWITCH = os.environ.get('ROLLOUT_KILL_SWITCH', 'False') == 'True'

# Application definition - เริ่มต้นด้วย apps พื้นฐานก่อน
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Core apps for simplified LekdeDai
    'home',           # Main homepage with lottery numbers
    'dreams',         # Dream interpretation to numbers
    'lotto_stats',    # Historical lottery analysis
    'lotto_formula',  # Lottery formula calculator
    'news',           # News analysis for lottery numbers
    'ai_engine',      # AI-powered predictions
    'lottery_checker', # Online lottery result checker
    'notebook',       # สมุดเลข browser-only (Task 9)
    'qa',             # Quality gate command (Task 21, no models/URLs)
    'analytics',      # Task 28: analytics ขั้นต่ำแบบรักษาความเป็นส่วนตัว
]
# เพิ่มการตั้งค่า Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'qa.middleware.EnsureCsrfCookieMiddleware',  # Task 30: csrftoken cookie สำหรับ analytics
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'qa.middleware.RequestMetricsMiddleware',  # Task 25: นับ request/latency/5xx
    'qa.middleware.BetaAccessMiddleware',      # Task 30: ประตูปิด beta + kill switch
]

ROOT_URLCONF = 'lekdedai.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'qa.context_processors.beta_status',  # Task 30: ประกาศสถานะ beta/kill switch
            ],
        },
    },
]

WSGI_APPLICATION = 'lekdedai.wsgi.application'

# Database
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///db.sqlite3',
        conn_max_age=600
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'th'
TIME_ZONE = 'Asia/Bangkok'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static'] if os.path.exists(BASE_DIR / 'static') else []

# Task 31: production ใช้ hashed static filenames กัน CDN/browser cache เก่าหลัง deploy
# (เปิดผ่าน env STATIC_HASHED=True; dev/test ไม่เปิดเพื่อไม่ให้ต้องมี manifest)
STATIC_HASHED = os.environ.get('STATIC_HASHED', 'False') == 'True'
if STATIC_HASHED:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
        },
    }


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Mock ingestion ใช้ได้เฉพาะ dev/test ที่เปิด flag ชัดเจน ห้ามเปิดใน production
ALLOW_MOCK_INGESTION = os.environ.get('ALLOW_MOCK_INGESTION', 'False') == 'True'

# Task 31: ข่าวต้องผ่านการอนุมัติจาก staff ก่อนเผยแพร่ (ค่าเริ่มต้น = manual approval)
# เปิด auto-publish เฉพาะหลังทดสอบตัวกรองความเกี่ยวข้องกับข่าวจริงและตั้ง precision gate แล้ว
NEWS_AUTO_PUBLISH = os.environ.get('NEWS_AUTO_PUBLISH', 'False') == 'True'

# Task 25: structured logs — console เสมอ + ไฟล์ถ้าตั้ง LOG_FILE;
# production (DEBUG=False) ออก JSON บรรทัดละรายการ
LOG_FILE = os.environ.get('LOG_FILE', '')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} {levelname} {name}: {message}',
            'style': '{',
        },
        'json': {
            '()': 'qa.logging.JSONFormatter',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json' if not DEBUG else 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
if LOG_FILE:
    LOGGING['handlers']['file'] = {
        'class': 'logging.FileHandler',
        'filename': LOG_FILE,
        'formatter': 'json',
    }
    LOGGING['root']['handlers'].append('file')
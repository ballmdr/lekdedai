"""Task 23: rate limit แบบง่ายด้วย Django cache (ไม่เพิ่ม dependency).

ข้อจำกัดที่รู้ชัด: cache เริ่มต้นเป็น local-memory แยกต่อ process
(gunicorn หลาย workers = วงเงินคูณตามจำนวน workers) — ใช้กัน abuse
ระดับพื้นฐาน ไม่ใช่โควต้าเข้มงวด. ถ้าต้องการเข้ม ให้ตั้ง CACHES เป็น Redis.
ปิดได้ด้วย settings.RATELIMIT_ENABLED = False (ใช้ใน tests ที่ยิงถี่โดยตั้งใจ).
"""
import time
from functools import wraps

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse

_PERIODS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


def _parse_rate(rate):
    count, _, period = rate.partition("/")
    count = int(count)
    window = _PERIODS.get(period.strip().lower(), 60)
    if count <= 0 or window <= 0:
        raise ValueError(f"invalid rate: {rate}")
    return count, window


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def ratelimit(rate="60/m", key="ip", redirect_back=False):
    """จำกัดคำขอต่อ IP (fixed window). เกิน -> 429 JSON (หรือ redirect + message).

    ปรับ rate ต่อ view ผ่าน settings.RATELIMIT_OVERRIDES = {"module.view": "3/m"}
    (ใช้ใน tests เป็นหลัก).
    """
    _parse_rate(rate)  # validate default ตั้งแต่ import

    def decorator(view):
        view_name = f"{view.__module__}.{view.__name__}"

        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if not getattr(settings, "RATELIMIT_ENABLED", True):
                return view(request, *args, **kwargs)
            overrides = getattr(settings, "RATELIMIT_OVERRIDES", {})
            limit, window = _parse_rate(overrides.get(view_name, rate))
            now = int(time.time())
            bucket = now // window
            cache_key = (
                f"rl:{view.__module__}.{view.__name__}:{_client_ip(request)}:{bucket}"
            )
            try:
                count = cache.get(cache_key, 0) + 1
                cache.set(cache_key, count, timeout=window + 5)
            except Exception:
                # cache ล้มต้องไม่ล้ม request
                return view(request, *args, **kwargs)
            if count > limit:
                if redirect_back:
                    from django.contrib import messages
                    from django.shortcuts import redirect

                    messages.error(request, "คำขอถี่เกินไป กรุณารอสักครู่แล้วลองใหม่")
                    return redirect(request.META.get("HTTP_REFERER", "/"))
                return JsonResponse(
                    {"success": False, "error": "คำขอถี่เกินไป กรุณารอสักครู่แล้วลองใหม่"},
                    status=429,
                )
            return view(request, *args, **kwargs)

        return wrapper

    return decorator

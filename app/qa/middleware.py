"""Task 25: เก็บสถิติ request (จำนวน/latency/5xx) ลง metrics ภายใน."""
import time

from django.middleware.csrf import get_token
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import urlencode

from qa import metrics
from qa.rollout import (
    gate_enabled,
    get_beta_status,
    kill_switch_on,
    session_allowed,
)


class RequestMetricsMiddleware:
    """นับทุก response (เว้น health/metrics/static) — ไม่แตะ body ไม่เก็บ PII."""

    SKIP_PREFIXES = ("/health/", "/metrics/", "/static/", "/media/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith(self.SKIP_PREFIXES):
            return self.get_response(request)
        started = time.monotonic()
        response = self.get_response(request)
        seconds = time.monotonic() - started
        try:
            match = getattr(request, "resolver_match", None)
            view = match.view_name if match and match.view_name else "unknown"
            status = response.status_code
            bucket = f"{status // 100}xx"
            metrics.incr("requests_total", f"{view}|{bucket}")
            metrics.observe_latency(view, seconds)
            if 500 <= status <= 599:
                metrics.incr("server_errors_total", view)
        except Exception:
            pass
        return response


class EnsureCsrfCookieMiddleware:
    """Task 30: ตั้ง csrftoken cookie บนทุกหน้า GET

    analytics.js ส่ง X-CSRFToken จาก cookie นี้ ถ้าไม่มีจะโดน 403 เงียบ ๆ.
    """

    SKIP_PREFIXES = ("/static/", "/media/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method in ("GET", "HEAD") and not request.path.startswith(
            self.SKIP_PREFIXES
        ):
            get_token(request)
        return self.get_response(request)


class BetaAccessMiddleware:
    """Task 30: ประตูปิด beta + kill switch/P0.

    - เคารพ /beta/, /health/, /metrics/, /admin/, static และ analytics
    - staff ผ่านได้เสมอ, ผู้ใช้ที่ redeem รหัสแล้วผ่านได้
    - pct10 เปิดเฉพาะเซสชันที่ตกใน bucket แบบ deterministic
    """

    EXEMPT_PREFIXES = (
        "/beta/",
        "/health/",
        "/metrics/",
        "/admin/",
        "/static/",
        "/media/",
        "/analytics/event/",
        # หน้าข้อมูล/ติดต่อ เปิดให้คนนอกเข้าถึงได้ (rate limit ที่ view อยู่แล้ว)
        "/contact/",
        "/privacy/",
        "/terms/",
        "/favicon.ico",
        "/robots.txt",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith(self.EXEMPT_PREFIXES):
            return self.get_response(request)

        active_gate = gate_enabled()
        if not active_gate and not kill_switch_on():
            return self.get_response(request)

        status = get_beta_status(use_cache=True)

        is_staff = getattr(request, "user", None) is not None and (
            request.user.is_authenticated and request.user.is_staff
        )

        # P0 / kill switch: หยุดรับทุกคน ยกเว้น staff
        if status["state"] == "closed":
            if is_staff:
                return self.get_response(request)
            return self._redirect_closed(request)

        # ประตู beta: ต้องมีรหัสเชิญหรืออยู่ใน bucket ที่เปิด
        if active_gate and not session_allowed(request):
            return self._redirect_gate(request)

        return self.get_response(request)

    def _redirect_gate(self, request):
        target = reverse("qa:beta_gate")
        nxt = request.get_full_path()
        if nxt and not nxt.startswith("/beta/"):
            target = f"{target}?{urlencode({'next': nxt})}"
        return redirect(target)

    def _redirect_closed(self, request):
        return redirect(reverse("qa:beta_closed"))

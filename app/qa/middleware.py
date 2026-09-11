"""Task 25: เก็บสถิติ request (จำนวน/latency/5xx) ลง metrics ภายใน."""
import time

from qa import metrics


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

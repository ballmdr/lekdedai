"""Task 28: endpoint รับ event — validate whitelist, ไม่เก็บ payload อื่น."""
import logging

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from utils.api import read_json_body
from utils.rate_limit import ratelimit

from .models import AnalyticsEvent

logger = logging.getLogger(__name__)

VALID_EVENTS = {choice[0] for choice in AnalyticsEvent.EVENT_CHOICES}


@ratelimit("120/m")
@require_POST
def collect_event(request):
    """POST /analytics/event/ {name, session_id}

    - name ต้องอยู่ใน whitelist เท่านั้น
    - session_id เป็นสตริงสุ่มจากฝั่ง client (ไม่ผูกตัวตน)
    - ฟิลด์อื่นทั้งหมดถูกละทิ้ง (ไม่เก็บข้อความฝัน/เลข/IP)
    """
    if not getattr(settings, "ANALYTICS_ENABLED", True):
        return JsonResponse({"success": True, "stored": False, "reason": "disabled"})

    data, error_response = read_json_body(request)
    if error_response is not None:
        return error_response

    name = str(data.get("name") or "").strip()
    session_id = str(data.get("session_id") or "").strip()
    if name not in VALID_EVENTS or not session_id:
        return JsonResponse(
            {"success": False, "error": "event ไม่ถูกต้อง"}, status=400
        )

    # Task 28: เก็บเฉพาะ 3 ฟิลด์ที่อนุญาต — ไม่อ่านค่าอื่นเลย
    AnalyticsEvent.objects.create(name=name, session_id=session_id[:32])
    return JsonResponse({"success": True, "stored": True})

"""Task 23: error response + audit log กลาง — 4xx/5xx ห้ามรั่ว stack/key/ข้อความ provider."""
import json
import logging

from django.conf import settings
from django.http import JsonResponse

logger = logging.getLogger(__name__)

GENERIC_500 = "เกิดข้อผิดพลาดในระบบ กรุณาลองใหม่"
MAX_JSON_BODY = 4096


def api_server_error(request, exc, message=GENERIC_500):
    """log ฉบับเต็มไว้ฝั่งเซิร์ฟเวอร์ ตอบกลับแค่ข้อความทั่วไป (dev เห็น detail)."""
    logger.exception("API 500: %s %s", request.method, request.path)
    if settings.DEBUG:
        return JsonResponse(
            {"success": False, "error": f"{message} ({exc})"}, status=500
        )
    return JsonResponse({"success": False, "error": message}, status=500)


def read_json_body(request, bad_message="ข้อมูลที่ส่งมาไม่ถูกต้อง"):
    """อ่าน JSON body แบบจำกัดขนาด คืน (data, None) หรือ (None, error_response)."""
    if len(request.body) > MAX_JSON_BODY:
        return None, JsonResponse(
            {"success": False, "error": "ข้อมูลที่ส่งมาใหญ่เกินไป"}, status=413
        )
    try:
        return json.loads(request.body), None
    except json.JSONDecodeError:
        return None, JsonResponse(
            {"success": False, "error": bad_message}, status=400
        )


def audit(request, action, detail=""):
    """audit trail ฉบับย่อสำหรับ endpoint เปลี่ยนข้อมูล."""
    user = (
        request.user.username
        if getattr(request, "user", None) and request.user.is_authenticated
        else "anonymous"
    )
    logger.info("AUDIT user=%s action=%s %s", user, action, detail)

"""Task 30/31: ประตูปิด beta, สถานะหยุดอัตโนมัติ และ staged rollout.

- stage: `beta` (ต้องมีรหัสเชิญ) -> `pct10` (เปิดบางส่วน) -> `public`
- kill switch: ปิดเว็บชั่วคราวได้ทันทีผ่าน env `ROLLOUT_KILL_SWITCH`
- สถานะหยุดอัตโนมัติ อ่านจาก JobRun / news freshness / SystemFlag(P0)
"""
import hashlib

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

VALID_STAGES = ("beta", "pct10", "public")
BETA_ACCESS_SESSION_KEY = "beta_access"
BETA_CODE_SESSION_KEY = "beta_invite"
BETA_STATUS_CACHE_KEY = "qa:beta_status:v1"


def rollout_stage():
    stage = (getattr(settings, "ROLLOUT_STAGE", "public") or "public").strip().lower()
    return stage if stage in VALID_STAGES else "public"


def kill_switch_on():
    return bool(getattr(settings, "ROLLOUT_KILL_SWITCH", False))


def gate_enabled():
    """ประตู beta ทำงานเมื่อตั้ง BETA_MODE หรือ stage เป็น beta/pct10."""
    if getattr(settings, "BETA_MODE", False):
        return True
    return rollout_stage() in ("beta", "pct10")


def _session_key(request):
    """คีย์ถาวรของเซสชัน (สร้างให้เลยถ้ายังไม่มี ใช้กับ pct10)."""
    if request.session.session_key is None:
        request.session.create()
    return request.session.session_key


def rollout_bucket(request):
    """เลข 0-99 คงที่ต่อเซสชัน ใช้แบ่งผู้ใช้เข้า rollout แบบ deterministic."""
    digest = hashlib.sha256(_session_key(request).encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % 100


def session_allowed(request):
    """ผู้ใช้คนนี้ผ่านประตู beta ได้หรือไม่ (ไม่นับ staff/exempt path)."""
    if getattr(request, "user", None) is not None and request.user.is_authenticated:
        if request.user.is_staff:
            return True
    if request.session.get(BETA_ACCESS_SESSION_KEY):
        return True
    stage = rollout_stage()
    if stage == "beta" or getattr(settings, "BETA_MODE", False):
        return False
    if stage == "pct10":
        percent = int(getattr(settings, "ROLLOUT_PERCENT", 10))
        return rollout_bucket(request) < max(0, min(100, percent))
    return True


def mark_beta_access(request, code):
    """บันทึกว่าเซสชันนี้ผ่านประตูแล้ว + หมุน session key กัน fixation."""
    request.session.cycle_key()
    request.session[BETA_ACCESS_SESSION_KEY] = True
    request.session[BETA_CODE_SESSION_KEY] = code


def redeem_beta_code(raw_code, now=None):
    """ตรวจและใช้รหัสเชิญ — คืน BetaInvite ถ้าสำเร็จ, None ถ้าไม่ผ่าน.

    รหัสที่ประกาศใน settings.BETA_INVITE_CODES จะถูก seed ลง DB อัตโนมัติ
    เมื่อมีการใช้ครั้งแรก เพื่อให้เก็บจำนวนครั้งที่ใช้ได้จริง.
    """
    from qa.models import BetaInvite

    code = (raw_code or "").strip()
    if not code or len(code) > 64:
        return None

    invite = BetaInvite.objects.filter(code__iexact=code).first()
    if invite is None:
        allowed = [str(c).strip() for c in getattr(settings, "BETA_INVITE_CODES", [])]
        if not any(code.lower() == c.lower() for c in allowed if c):
            return None
        invite = BetaInvite.objects.create(code=code, label="env", max_uses=0)

    if not invite.redeem(now):
        return None
    return invite


def _collect_reasons(now):
    """อ่านสัญญาณจาก JobRun/news — คืน list เหตุผล (ไม่ throw)."""
    from qa.jobs import get_job_freshness
    from qa.models import JobRun

    reasons = []

    failed = list(
        JobRun.objects.filter(status="failed").values_list("key", flat=True)[:10]
    )
    if failed:
        reasons.append("job ล้มเหลว: " + ", ".join(failed))

    stale = sorted(
        key for key, info in get_job_freshness().items() if info["is_stale"]
    )
    if stale:
        reasons.append("ข้อมูลล้าสมัย: " + ", ".join(stale))

    try:
        from news.ingestion import get_news_freshness

        news = get_news_freshness()
        if news["failure_newer"]:
            reasons.append("ดึงข่าวล้มเหลว")
        elif news["is_stale"] and news["latest_fetched"] is not None:
            reasons.append("ข่าวล้าสมัย")
    except Exception:
        pass

    return reasons


def compute_beta_status(now=None):
    """คำนวณสถานะสด: open / paused (degraded) / closed (P0 หรือ kill switch)."""
    from qa.models import SystemFlag

    now = now or timezone.now()
    status = {
        "state": "open",
        "label": "เปิดให้ใช้งาน",
        "message": "",
        "reasons": [],
        "gate": gate_enabled(),
        "stage": rollout_stage(),
        "kill_switch": kill_switch_on(),
    }

    if kill_switch_on():
        status.update(
            state="closed",
            label="ปิดระบบชั่วคราว",
            message="ระบบปิดปรับปรุงชั่วคราว กรุณากลับมาใหม่ภายหลัง",
            reasons=["kill switch ถูกเปิด"],
        )
        return status

    p0 = list(
        SystemFlag.objects.filter(is_active=True, level="P0").values_list(
            "key", "message"
        )
    )
    if p0:
        status.update(
            state="closed",
            label="หยุด beta ชั่วคราว",
            message="พบเหตุสำคัญ ระบบหยุดรับผู้ใช้ใหม่ชั่วคราว",
            reasons=[f"{key}: {message}" for key, message in p0],
        )
        return status

    reasons = _collect_reasons(now)
    if reasons:
        status.update(
            state="paused",
            label="เฝ้าระวัง (ระบบ degraded)",
            message="ระบบทำงานแบบจำกัด โปรดตรวจสอบข้อมูลก่อนใช้งาน",
            reasons=reasons,
        )
    return status


def get_beta_status(now=None, use_cache=False):
    """คืนสถานะ beta (มี cache สั้น ๆ ได้เพื่อลด query ตอนเรนเดอร์ทุกหน้า)."""
    if not use_cache:
        return compute_beta_status(now)
    cached = cache.get(BETA_STATUS_CACHE_KEY)
    if cached is not None:
        return cached
    status = compute_beta_status(now)
    cache.set(BETA_STATUS_CACHE_KEY, status, getattr(settings, "BETA_STATUS_CACHE_SECONDS", 60))
    return status

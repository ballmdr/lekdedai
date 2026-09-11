"""Task 30: ประกาศสถานะ beta/kill switch ให้ทุกเทมเพลต (ไม่มี query เมื่อปิด)."""
from qa.rollout import gate_enabled, get_beta_status, kill_switch_on


def beta_status(request):
    # ปิด gate และไม่มี kill switch = ไม่ต้องยิง DB เลย (กัน query budget เพิ่ม)
    if not gate_enabled() and not kill_switch_on():
        return {"beta_status": None}
    return {"beta_status": get_beta_status(use_cache=True)}

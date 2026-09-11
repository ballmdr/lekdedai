"""Task 25: ตัวนับ metrics ภายใน (ไม่เพิ่ม dependency).

ข้อจำกัดที่รู้ชัด: เก็บใน memory ของ process (gunicorn หลาย workers =
เลขแยกกัน) ใช้ดูแนวโน้ม/เฝ้าระวัง ไม่ใช่บิลลิง. ถ้าต้องการรวมข้าม
process ให้ส่งออกไป TSDB ภายนอกแทน (ดู docs/OPERATIONS.md).
"""
import threading

_lock = threading.Lock()
_COUNTERS = {}
_LATENCY = {}


def _labels_key(labels):
    if isinstance(labels, dict):
        return "|".join(f"{k}={v}" for k, v in sorted(labels.items()))
    return str(labels or "")


def incr(name, labels="", amount=1):
    """เพิ่มตัวนับ คืนค่าปัจจุบัน."""
    key = (str(name), _labels_key(labels))
    with _lock:
        _COUNTERS[key] = _COUNTERS.get(key, 0) + amount
        return _COUNTERS[key]


def observe_latency(view, seconds):
    """เก็บผลรวมเวลา + จำนวนครั้ง ไว้คำนวณค่าเฉลี่ยต่อ view."""
    key = str(view or "unknown")
    with _lock:
        total, count = _LATENCY.get(key, (0.0, 0))
        _LATENCY[key] = (total + float(seconds), count + 1)


def snapshot():
    """คืน dict metrics ทั้งหมด: {"counters": {...}, "latency_avg_seconds": {...}}."""
    with _lock:
        counters = {
            f"{name}{{{labels}}}" if labels else name: value
            for (name, labels), value in _COUNTERS.items()
        }
        latency = {
            view: (total / count if count else 0.0)
            for view, (total, count) in _LATENCY.items()
        }
    return {"counters": counters, "latency_avg_seconds": latency}


def reset():
    """ล้างทั้งหมด (ใช้ใน tests)."""
    with _lock:
        _COUNTERS.clear()
        _LATENCY.clear()

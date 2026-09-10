"""รูปแบบวันที่ไทย (เดือนไทย + ปีพุทธศักราช) ใช้ร่วมกันทั้งเว็บ."""

THAI_MONTHS = [
    "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
    "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม",
]


def format_thai_date(value):
    """คืนวันที่แบบไทย เช่น 1 กันยายน 2569"""
    if not value:
        return ""
    return f"{value.day} {THAI_MONTHS[value.month - 1]} {value.year + 543}"


def format_thai_date_short(value):
    """คืนวันที่แบบไทยแบบสั้น เช่น 1 ก.ย. 69"""
    if not value:
        return ""
    return f"{value.day} {THAI_MONTHS[value.month - 1][:4]}. {str(value.year + 543)[-2:]}"

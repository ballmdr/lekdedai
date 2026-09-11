"""Task 31: เมนูหลัก (main navigation) ใช้ร่วมทุกหน้า พร้อม active state.

ไม่ยิง DB — ใช้ request.path เทียบกับ href เพื่อกำหนด active/aria-current.
"""

# (label, href, font-awesome icon)
MAIN_NAV_ITEMS = [
    ("หน้าแรก", "/", "fa-house"),
    ("วิเคราะห์ฝัน", "/dreams/", "fa-moon"),
    ("ตรวจหวย", "/lottery_checker/", "fa-ticket"),
    ("สมุดเลข", "/notebook/", "fa-book"),
    ("สถิติ", "/lotto_stats/", "fa-chart-simple"),
    ("ข่าวหวย", "/news/", "fa-newspaper"),
    ("AI ทำนาย", "/ai/", "fa-brain"),
    ("สูตรหวย", "/lotto_formula/", "fa-calculator"),
]


def _is_active(path, href):
    if href == "/":
        return path == "/"
    return path.startswith(href)


def main_nav(request):
    """คืน list ของเมนูหลักพร้อม flag active (ไม่แตะ DB)."""
    path = getattr(request, "path", "/") or "/"
    items = [
        {"label": label, "href": href, "icon": icon, "active": _is_active(path, href)}
        for label, href, icon in MAIN_NAV_ITEMS
    ]
    return {"main_nav": items}

"""Task 16: ทะเบียนแหล่งข่าวที่อนุมัติ (version-controlled source of truth).

ทุก URL ในไฟล์นี้ผ่านการยืนยันว่าดึงได้จริงด้วย feedparser แล้ว (ดู Task 16):
- thairath-rss: https://www.thairath.co.th/rss/news (20 ข่าว)
- inn-rss: https://www.innnews.co.th/feed/ (8 ข่าว, INN News)
ห้ามเพิ่ม URL ที่ยังไม่เคยทดสอบดึงจริง.
นโยบายเก็บเนื้อหา: เก็บเฉพาะพาดหัว+สรุป+ลิงก์กลับต้นฉบับ ไม่เก็บบทความเต็ม,
เคารพ robots.txt และเงื่อนไขลิขสิทธิ์ของแต่ละสำนัก (ใส่ attribution + ลิงก์กลับเสมอ).
"""

REGISTRY_VERSION = "1.0"

DEFAULT_FETCH_POLICY = {
    "store": "headline+summary+link",
    "fulltext": False,
    "respect_robots": True,
    "link_back": True,
}

SOURCE_REGISTRY = [
    {
        "key": "internal-news",
        "name": "ข่าวในระบบ LekdeDai",
        "source_type": "news",
        "category": "internal",
        "url": "/news/",
        "attribution": "ระบบ LekdeDai",
        "fetch_policy": {
            "store": "articles",
            "fulltext": True,
            "respect_robots": True,
            "link_back": False,
            "note": "ข้อมูลของระบบเอง",
        },
        "license_status": "approved",
        "license_note": "เนื้อหาของระบบเอง เผยแพร่ได้เต็ม",
        "is_active": True,
        "scraping_interval": 3,
    },
    {
        "key": "thairath-rss",
        "name": "ไทยรัฐ RSS",
        "source_type": "news",
        "category": "rss",
        "url": "https://www.thairath.co.th/rss/news",
        "attribution": "ไทยรัฐออนไลน์",
        "fetch_policy": dict(DEFAULT_FETCH_POLICY),
        "license_status": "approved",
        "license_note": (
            "RSS สาธารณะ เก็บเฉพาะพาดหัว+สรุป+ลิงก์กลับ "
            "(ไม่เก็บเนื้อหาเต็ม) ตรวจสอบ feed จริงแล้ว"
        ),
        "is_active": True,
        "scraping_interval": 6,
    },
    {
        "key": "inn-rss",
        "name": "INN News RSS",
        "source_type": "news",
        "category": "rss",
        "url": "https://www.innnews.co.th/feed/",
        "attribution": "สำนักข่าว INN",
        "fetch_policy": dict(DEFAULT_FETCH_POLICY),
        "license_status": "approved",
        "license_note": (
            "RSS สาธารณะ เก็บเฉพาะพาดหัว+สรุป+ลิงก์กลับ "
            "(ไม่เก็บเนื้อหาเต็ม) ตรวจสอบ feed จริงแล้ว"
        ),
        "is_active": True,
        "scraping_interval": 6,
    },
    {
        "key": "thairath-local",
        "name": "ไทยรัฐ ภูมิภาค (fallback)",
        "source_type": "news",
        "category": "category_page",
        "url": "https://www.thairath.co.th/news/local/all-latest",
        "attribution": "ไทยรัฐออนไลน์",
        "fetch_policy": dict(
            DEFAULT_FETCH_POLICY,
            note="fallback เมื่อ RSS ใช้ไม่ได้ (Task 18 เปิดใช้)",
        ),
        "license_status": "approved",
        "license_note": (
            "ขูดเฉพาะพาดหัว+สรุป+ลิงก์กลับเมื่อ RSS ใช้ไม่ได้ "
            "เคารพ robots.txt ตรวจสอบ selector จริงแล้ว"
        ),
        "is_active": False,
        "scraping_interval": 12,
    },
]

# แถว seed รุ่นเก่าที่ใช้งานจริงไม่ได้ (ขูดเพจที่ต้องล็อกอิน/ไม่มี API) — seed จะปิดไว้
LEGACY_INACTIVE_NAMES = [
    "Facebook - กลุมหวย",
    "Twitter - #หวย #เลขเด็ด",
]

"""Task 9: สมุดเลข browser-only — server ส่งแค่งวดให้ผูก ที่เหลืออยู่บนอุปกรณ์ผู้ใช้."""
import json
from datetime import date

from django.shortcuts import render

from utils.lottery_dates import LOTTERY_DATES
from utils.thai_date import format_thai_date


def notebook_page(request):
    """หน้าสมุดเลข: ฟอร์ม + รายการ (CRUD เกิดใน browser ผ่าน localStorage).

    งวดเริ่มต้น = งวดถัดไป (ผู้ใช้มักจดเลขรองวดหน้า) พร้อมงวดล่วงหน้าและงวดที่ผ่านมา.
    """
    upcoming = LOTTERY_DATES.get_upcoming_draw_dates(3)
    past = LOTTERY_DATES.get_dropdown_options(limit=24)

    options = []
    seen = set()
    for iso in upcoming:
        d = date.fromisoformat(iso)
        options.append({
            "value": iso,
            "label": format_thai_date(d),
            "is_special": False,
        })
        seen.add(iso)
    for opt in past:
        if opt["value"] not in seen:
            options.append(opt)
            seen.add(opt["value"])

    default_draw = upcoming[0] if upcoming else (options[0]["value"] if options else "")

    return render(request, 'notebook/notebook.html', {
        'draw_options_json': json.dumps(options, ensure_ascii=False),
        'default_draw': default_draw,
        'page_title': 'สมุดเลขของฉัน - จดที่มาและตรวจผล',
        'meta_description': 'สมุดจดเลขส่วนตัว บันทึกที่มา เหตุผล และงวด โดยไม่ต้องสมัครสมาชิก',
    })

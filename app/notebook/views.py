"""Task 9: สมุดเลข browser-only — server ส่งแค่งวดให้ผูก ที่เหลืออยู่บนอุปกรณ์ผู้ใช้."""
import json

from django.shortcuts import render

from utils.lottery_dates import LOTTERY_DATES


def notebook_page(request):
    """หน้าสมุดเลข: ฟอร์ม + รายการ (CRUD เกิดใน browser ผ่าน localStorage)."""
    draw_options = LOTTERY_DATES.get_dropdown_options(limit=24)
    return render(request, 'notebook/notebook.html', {
        'draw_options_json': json.dumps(draw_options, ensure_ascii=False),
        'page_title': 'สมุดเลขของฉัน - จดที่มาและตรวจผล',
        'meta_description': 'สมุดจดเลขส่วนตัว บันทึกที่มา เหตุผล และงวด โดยไม่ต้องสมัครสมาชิก',
    })

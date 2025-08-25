#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug Latest Data - ตรวจสอบข้อมูลล่าสุดใน lottery_checker
"""

import os
import sys
import django

# เพิ่ม path ของ Django project
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lekdedai.settings')
django.setup()

from lottery_checker.models import LottoResult
from lottery_checker.lotto_service import LottoService
from datetime import datetime, date

def debug_latest_data():
    """ตรวจสอบข้อมูลล่าสุดใน lottery_checker"""
    print("🔍 ตรวจสอบข้อมูลล่าสุดใน lottery_checker")
    print("=" * 50)
    
    # ข้อมูลล่าสุด 5 รายการ
    latest_results = LottoResult.objects.order_by('-draw_date')[:5]
    
    for result in latest_results:
        print(f"\n📅 วันที่: {result.draw_date}")
        print(f"📊 ข้อมูล: {result.result_data}")
        
        # ตรวจสอบว่ามีข้อมูลรางวัลหรือไม่
        if isinstance(result.result_data, dict):
            if 'first' in result.result_data and result.result_data['first']:
                print("✅ มีข้อมูลรางวัล")
            elif 'response' in result.result_data and result.result_data['response']:
                print("✅ มีข้อมูลรางวัลใน response")
            else:
                print("❌ ไม่มีข้อมูลรางวัล")
        else:
            print("❌ ข้อมูลไม่ใช่ dict")
    
    print("\n" + "=" * 50)
    print("🧪 ทดสอบการดึงข้อมูลใหม่")
    
    # ทดสอบการดึงข้อมูลใหม่
    service = LottoService()
    today = date.today()
    
    print(f"📡 ทดสอบดึงข้อมูลวันที่ {today.strftime('%d/%m/%Y')}")
    result = service.get_or_fetch_result(
        date=today.day,
        month=today.month,
        year=today.year
    )
    
    if result['success']:
        print(f"✅ สำเร็จ: {result['message']}")
        print(f"📊 ข้อมูล: {result['data']}")
        
        # ตรวจสอบว่ามีข้อมูลรางวัลหรือไม่
        if isinstance(result['data'], dict):
            if 'first' in result['data'] and result['data']['first']:
                print("✅ มีข้อมูลรางวัล")
            elif 'response' in result['data'] and result['data']['response']:
                print("✅ มีข้อมูลรางวัลใน response")
            else:
                print("❌ ไม่มีข้อมูลรางวัล")
    else:
        print(f"❌ ไม่สำเร็จ: {result['error']}")

if __name__ == "__main__":
    debug_latest_data()

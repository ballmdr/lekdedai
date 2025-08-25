#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ตรวจสอบข้อมูลจริงใน lottery_checker
"""

import os
import sys
import django

# เพิ่ม path ของ Django project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ตั้งค่า Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lekdedai.settings')
django.setup()

from lottery_checker.models import LottoResult
from datetime import datetime

def check_real_data():
    """ตรวจสอบข้อมูลจริงใน lottery_checker"""
    print("🔍 ตรวจสอบข้อมูลจริงใน lottery_checker...")
    
    # ดึงข้อมูลทั้งหมด
    all_results = LottoResult.objects.all()
    print(f"📊 จำนวนข้อมูลทั้งหมด: {all_results.count()}")
    
    if all_results.count() == 0:
        print("❌ ไม่มีข้อมูลใน lottery_checker")
        return
    
    # ตรวจสอบข้อมูลล่าสุด 3 รายการ
    recent_results = all_results.order_by('-draw_date')[:3]
    
    for i, result in enumerate(recent_results, 1):
        print(f"\n📅 ข้อมูลที่ {i}: {result.draw_date}")
        print(f"   แหล่งข้อมูล: {result.source}")
        print(f"   ประเภทข้อมูล: {type(result.result_data)}")
        
        if isinstance(result.result_data, dict):
            print(f"   คีย์ที่มี: {list(result.result_data.keys())}")
            
            # ตรวจสอบแต่ละคีย์
            for key, value in result.result_data.items():
                print(f"     {key}: {type(value)} = {value}")
                
                # ตรวจสอบโครงสร้างลึก
                if isinstance(value, dict):
                    print(f"       คีย์ย่อย: {list(value.keys())}")
                    if 'first' in value:
                        print(f"       รางวัลที่ 1: {value['first']}")
                elif isinstance(value, list):
                    print(f"       จำนวนรายการ: {len(value)}")
                    if value:
                        print(f"       รายการแรก: {value[0]} (ประเภท: {type(value[0])})")
        else:
            print(f"   ข้อมูล: {result.result_data}")
    
    # ตรวจสอบข้อมูลที่มีรางวัลที่ 1
    print(f"\n🔍 ตรวจสอบข้อมูลที่มีรางวัลที่ 1...")
    
    for result in all_results:
        if isinstance(result.result_data, dict):
            # ตรวจสอบรูปแบบต่างๆ
            if 'first' in result.result_data:
                first_data = result.result_data['first']
                print(f"📅 {result.draw_date}: พบ 'first' = {first_data}")
            elif 'response' in result.result_data and result.result_data['response']:
                response_data = result.result_data['response']
                if isinstance(response_data, dict) and 'first' in response_data:
                    print(f"📅 {result.draw_date}: พบ 'first' ใน response = {response_data['first']}")
            elif 'data' in result.result_data and result.result_data['data']:
                data = result.result_data['data']
                if isinstance(data, dict) and 'first' in data:
                    print(f"📅 {result.draw_date}: พบ 'first' ใน data = {data['first']}")

def test_data_conversion():
    """ทดสอบการแปลงข้อมูล"""
    print(f"\n🧪 ทดสอบการแปลงข้อมูล...")
    
    # ดึงข้อมูลตัวอย่าง
    sample_result = LottoResult.objects.first()
    if not sample_result:
        print("❌ ไม่มีข้อมูลให้ทดสอบ")
        return
    
    print(f"📅 ข้อมูลตัวอย่าง: {sample_result.draw_date}")
    print(f"   ข้อมูลดิบ: {sample_result.result_data}")
    
    # ทดสอบการแปลงแบบต่างๆ
    from lotto_stats.lotto_sync_service import LottoSyncService
    
    service = LottoSyncService()
    converted = service._convert_lotto_data(sample_result)
    
    print(f"   ข้อมูลที่แปลงแล้ว: {converted}")

if __name__ == "__main__":
    try:
        check_real_data()
        test_data_conversion()
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        import traceback
        traceback.print_exc()

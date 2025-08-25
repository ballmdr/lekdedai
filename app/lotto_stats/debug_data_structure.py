#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ตรวจสอบโครงสร้างข้อมูลใน lottery_checker
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

def inspect_data_structure():
    """ตรวจสอบโครงสร้างข้อมูล"""
    print("🔍 ตรวจสอบโครงสร้างข้อมูลใน lottery_checker...")
    
    # ดึงข้อมูลทั้งหมด
    all_results = LottoResult.objects.all()
    print(f"📊 จำนวนข้อมูลทั้งหมด: {all_results.count()}")
    
    if all_results.count() == 0:
        print("❌ ไม่มีข้อมูลใน lottery_checker")
        return
    
    # ตรวจสอบข้อมูลล่าสุด 5 รายการ
    recent_results = all_results.order_by('-draw_date')[:5]
    
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
                elif isinstance(value, list):
                    print(f"       จำนวนรายการ: {len(value)}")
                    if value:
                        print(f"       รายการแรก: {value[0]} (ประเภท: {type(value[0])})")
        else:
            print(f"   ข้อมูล: {result.result_data}")
    
    # ตรวจสอบรูปแบบข้อมูลที่พบ
    print(f"\n🔍 วิเคราะห์รูปแบบข้อมูล...")
    
    # หาคีย์ที่พบบ่อยที่สุด
    key_patterns = {}
    for result in all_results:
        if isinstance(result.result_data, dict):
            for key in result.result_data.keys():
                key_patterns[key] = key_patterns.get(key, 0) + 1
    
    print("คีย์ที่พบบ่อยที่สุด:")
    for key, count in sorted(key_patterns.items(), key=lambda x: x[1], reverse=True):
        print(f"  {key}: {count} ครั้ง")
    
    # ตรวจสอบรูปแบบของรางวัลที่ 1
    first_prize_patterns = {}
    for result in all_results:
        if isinstance(result.result_data, dict):
            first_data = result.result_data.get('first', None)
            if first_data:
                if isinstance(first_data, dict):
                    first_prize_patterns['dict'] = first_prize_patterns.get('dict', 0) + 1
                elif isinstance(first_data, str):
                    first_prize_patterns['string'] = first_prize_patterns.get('string', 0) + 1
                else:
                    first_prize_patterns[str(type(first_data))] = first_prize_patterns.get(str(type(first_data)), 0) + 1
    
    print(f"\nรูปแบบของรางวัลที่ 1:")
    for pattern, count in first_prize_patterns.items():
        print(f"  {pattern}: {count} ครั้ง")

def test_conversion():
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
        inspect_data_structure()
        test_conversion()
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        import traceback
        traceback.print_exc()

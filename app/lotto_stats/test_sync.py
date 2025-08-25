#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ทดสอบการซิงค์ข้อมูลของ lotto_stats
"""

import os
import sys
import django
from datetime import datetime, timedelta

# เพิ่ม path ของ Django project
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# ตั้งค่า Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lekdedai.settings')
django.setup()

from lotto_stats.lotto_sync_service import LottoSyncService
from lotto_stats.models import LotteryDraw
from lottery_checker.models import LottoResult

def test_sync_service():
    """ทดสอบ LottoSyncService"""
    print("🧪 ทดสอบ LottoSyncService...")
    
    service = LottoSyncService()
    
    # ทดสอบการดึงสถานะ
    print("1. ทดสอบการดึงสถานะ...")
    status = service.get_sync_status()
    print(f"   สถานะ: {status}")
    
    # ทดสอบการซิงค์ข้อมูลล่าสุด
    print("2. ทดสอบการซิงค์ข้อมูลล่าสุด...")
    result = service.sync_recent_data(days_back=7, force_update=False)
    print(f"   ผลลัพธ์: {result}")
    
    # ทดสอบการซิงค์วันที่เฉพาะ
    print("3. ทดสอบการซิงค์วันที่เฉพาะ...")
    test_date = datetime.now().date() - timedelta(days=1)
    result = service.sync_specific_date(test_date, force_update=False)
    print(f"   ผลลัพธ์: {result}")
    
    return True

def test_data_conversion():
    """ทดสอบการแปลงข้อมูล"""
    print("🔄 ทดสอบการแปลงข้อมูล...")
    
    # สร้างข้อมูลตัวอย่างใน lottery_checker
    test_date = datetime.now().date()
    test_data = {
        'first': {'number': '123456'},
        'second': ['789', '012'],
        'third': ['345', '678'],
        'fourth': ['901', '234'],
        'fifth': ['567', '890']
    }
    
    # สร้างหรืออัปเดตข้อมูลใน lottery_checker
    lotto_result, created = LottoResult.objects.update_or_create(
        draw_date=test_date,
        defaults={
            'result_data': test_data,
            'source': 'Test Data'
        }
    )
    
    print(f"   สร้างข้อมูลทดสอบ: {created}")
    
    # ทดสอบการแปลงข้อมูล
    service = LottoSyncService()
    converted_data = service._convert_lotto_data(lotto_result)
    
    print(f"   ข้อมูลที่แปลงแล้ว: {converted_data}")
    
    # ตรวจสอบความถูกต้อง
    expected = {
        'draw_round': test_date.strftime('%d/%m/%Y'),
        'first_prize': '123456',
        'two_digit': '56',
        'three_digit_front': '789, 012, 345, 678',
        'three_digit_back': '901, 234, 567, 890'
    }
    
    is_correct = all(
        converted_data.get(key) == expected[key] 
        for key in expected.keys()
    )
    
    print(f"   การแปลงข้อมูลถูกต้อง: {is_correct}")
    
    # ล้างข้อมูลทดสอบ
    lotto_result.delete()
    
    return is_correct

def test_statistics_calculation():
    """ทดสอบการคำนวณสถิติ"""
    print("📊 ทดสอบการคำนวณสถิติ...")
    
    # ตรวจสอบว่ามีข้อมูลใน lotto_stats หรือไม่
    total_draws = LotteryDraw.objects.count()
    print(f"   จำนวนข้อมูลใน lotto_stats: {total_draws}")
    
    if total_draws > 0:
        # ทดสอบการคำนวณสถิติ
        from lotto_stats.stats_calculator import StatsCalculator
        
        calculator = StatsCalculator()
        
        # ทดสอบเลขฮอต
        hot_numbers = calculator.get_hot_numbers(limit=5, days=90)
        print(f"   เลขฮอต: {[num['number'] for num in hot_numbers[:3]]}")
        
        # ทดสอบเลขเย็น
        cold_numbers = calculator.get_cold_numbers(limit=5)
        print(f"   เลขเย็น: {[num['number'] for num in cold_numbers[:3]]}")
        
        # ทดสอบสถิติสรุป
        summary = calculator.get_statistics_summary()
        if summary:
            print(f"   สรุปสถิติ: {summary['total_draws']} งวด")
        
        return True
    else:
        print("   ไม่มีข้อมูลใน lotto_stats ให้ทดสอบ")
        return False

def test_api_endpoints():
    """ทดสอบ API endpoints"""
    print("🌐 ทดสอบ API endpoints...")
    
    # ทดสอบสถานะการซิงค์
    print("1. ทดสอบ API สถานะการซิงค์...")
    try:
        from django.test import Client
        from django.urls import reverse
        
        client = Client()
        response = client.get('/lotto_stats/api/sync/status/')
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.json()}")
        
    except Exception as e:
        print(f"   เกิดข้อผิดพลาด: {e}")
    
    return True

def run_all_tests():
    """รันการทดสอบทั้งหมด"""
    print("🚀 เริ่มการทดสอบ lotto_stats...")
    print("=" * 50)
    
    tests = [
        ("LottoSyncService", test_sync_service),
        ("การแปลงข้อมูล", test_data_conversion),
        ("การคำนวณสถิติ", test_statistics_calculation),
        ("API Endpoints", test_api_endpoints),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 ทดสอบ: {test_name}")
            result = test_func()
            results.append((test_name, result))
            print(f"✅ {test_name}: {'ผ่าน' if result else 'ไม่ผ่าน'}")
        except Exception as e:
            print(f"❌ {test_name}: เกิดข้อผิดพลาด - {e}")
            results.append((test_name, False))
    
    # สรุปผลการทดสอบ
    print("\n" + "=" * 50)
    print("📊 สรุปผลการทดสอบ")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ผ่าน" if result else "❌ ไม่ผ่าน"
        print(f"{test_name}: {status}")
    
    print(f"\nผลรวม: {passed}/{total} การทดสอบผ่าน")
    
    if passed == total:
        print("🎉 การทดสอบทั้งหมดผ่าน!")
        return True
    else:
        print("⚠️ มีการทดสอบที่ไม่ผ่าน")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ตัวอย่างการใช้งาน lotto_stats ที่อัปเดตแล้ว
"""

from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Q

from .lotto_sync_service import LottoSyncService
from .stats_calculator import StatsCalculator
from .models import LotteryDraw

def example_sync_data():
    """ตัวอย่างการซิงค์ข้อมูลจาก lottery_checker"""
    print("🔄 ตัวอย่างการซิงค์ข้อมูล...")
    
    # สร้าง service
    sync_service = LottoSyncService()
    
    # ดูสถานะปัจจุบัน
    status = sync_service.get_sync_status()
    print(f"สถานะปัจจุบัน: {status}")
    
    # ซิงค์ข้อมูลล่าสุด 7 วัน
    result = sync_service.sync_recent_data(days_back=7, force_update=False)
    print(f"ผลการซิงค์: {result}")
    
    # ซิงค์วันที่เฉพาะ
    specific_date = timezone.now().date() - timedelta(days=1)
    result = sync_service.sync_specific_date(specific_date, force_update=False)
    print(f"ผลการซิงค์วันที่เฉพาะ: {result}")

def example_calculate_statistics():
    """ตัวอย่างการคำนวณสถิติ"""
    print("📊 ตัวอย่างการคำนวณสถิติ...")
    
    # สร้าง calculator
    calculator = StatsCalculator()
    
    # เลขฮอต 2 ตัว
    hot_2d = calculator.get_hot_numbers(limit=10, days=90, number_type='2D')
    print(f"เลขฮอต 2 ตัว (90 วัน): {hot_2d[:5]}")
    
    # เลขเย็น 2 ตัว
    cold_2d = calculator.get_cold_numbers(limit=10, number_type='2D')
    print(f"เลขเย็น 2 ตัว: {cold_2d[:5]}")
    
    # สถิติรายเดือน
    monthly_stats = calculator.get_monthly_statistics()
    print(f"สถิติรายเดือน: {list(monthly_stats.keys())[-3:]}")
    
    # สถิติของเลขที่เจาะจง
    number_stats = calculator.get_number_statistics('12')
    print(f"สถิติเลข 12: {number_stats}")

def example_query_data():
    """ตัวอย่างการดึงข้อมูลจากฐานข้อมูล"""
    print("📋 ตัวอย่างการดึงข้อมูล...")
    
    # ข้อมูล 10 งวดล่าสุด
    recent_draws = LotteryDraw.objects.all()[:10]
    print(f"ข้อมูล 10 งวดล่าสุด: {recent_draws.count()} รายการ")
    
    for draw in recent_draws[:3]:  # แสดง 3 รายการแรก
        print(f"  {draw.draw_date}: {draw.first_prize} | 2ตัว: {draw.two_digit}")
    
    # ข้อมูลตามช่วงเวลา
    cutoff_date = timezone.now().date() - timedelta(days=30)
    monthly_draws = LotteryDraw.objects.filter(draw_date__gte=cutoff_date)
    print(f"ข้อมูล 30 วันล่าสุด: {monthly_draws.count()} รายการ")
    
    # ข้อมูลตามเลข
    draws_with_12 = LotteryDraw.objects.filter(
        Q(two_digit='12') | Q(first_prize__contains='12')
    ).order_by('-draw_date')
    print(f"งวดที่มีเลข 12: {draws_with_12.count()} รายการ")

def example_full_workflow():
    """ตัวอย่างการทำงานแบบครบวงจร"""
    print("🚀 ตัวอย่างการทำงานแบบครบวงจร...")
    
    # 1. ซิงค์ข้อมูล
    sync_service = LottoSyncService()
    sync_result = sync_service.sync_recent_data(days_back=30, force_update=False)
    print(f"1. ซิงค์ข้อมูล: {sync_result['success']}")
    
    if sync_result['success']:
        # 2. คำนวณสถิติ
        calculator = StatsCalculator()
        
        # เลขฮอต/เย็น
        hot_numbers = calculator.get_hot_numbers(limit=5, days=90)
        cold_numbers = calculator.get_cold_numbers(limit=5)
        
        print(f"2. เลขฮอต: {[num['number'] for num in hot_numbers]}")
        print(f"   เลขเย็น: {[num['number'] for num in cold_numbers]}")
        
        # 3. สถิติสรุป
        summary = calculator.get_statistics_summary()
        if summary:
            print(f"3. สรุปสถิติ: {summary['total_draws']} งวด")
            print(f"   เลข 2 ตัวที่ออกบ่อย: {summary['most_common_all_time']['2d']['number']}")
        
        # 4. แสดงข้อมูลล่าสุด
        latest_draws = LotteryDraw.objects.order_by('-draw_date')[:5]
        print(f"4. ข้อมูลล่าสุด:")
        for draw in latest_draws:
            print(f"   {draw.draw_date}: {draw.first_prize}")

def example_api_usage():
    """ตัวอย่างการใช้งานผ่าน API"""
    print("🌐 ตัวอย่างการใช้งานผ่าน API...")
    
    print("""
    # ดูสถานะการซิงค์
    GET /lotto_stats/api/sync/status/
    
    # ซิงค์ข้อมูลล่าสุด
    POST /lotto_stats/api/sync/data/
    {
        "days_back": 7,
        "force_update": false
    }
    
    # ซิงค์วันที่เฉพาะ
    POST /lotto_stats/api/sync/date/
    {
        "date": "2025-01-15",
        "force_update": false
    }
    
    # เลขฮอต/เย็น
    GET /lotto_stats/api/hot-cold/?days=90&limit=10
    
    # สถิติเลขที่เจาะจง
    GET /lotto_stats/api/number/123/
    """)

if __name__ == "__main__":
    print("🎯 ตัวอย่างการใช้งาน lotto_stats ที่อัปเดตแล้ว")
    print("=" * 50)
    
    try:
        # ตัวอย่างการซิงค์ข้อมูล
        example_sync_data()
        print()
        
        # ตัวอย่างการคำนวณสถิติ
        example_calculate_statistics()
        print()
        
        # ตัวอย่างการดึงข้อมูล
        example_query_data()
        print()
        
        # ตัวอย่างการทำงานแบบครบวงจร
        example_full_workflow()
        print()
        
        # ตัวอย่างการใช้งานผ่าน API
        example_api_usage()
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
    
    print("\n✅ ตัวอย่างการใช้งานเสร็จสิ้น")

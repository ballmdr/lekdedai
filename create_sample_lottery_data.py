#!/usr/bin/env python3
"""
สร้างข้อมูลจำลองหวยใน LotteryDraw เพื่อทดสอบการทำงานของ lotto_stats
"""
import os
import sys
import django
from datetime import date, timedelta
import random

# Setup Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from lotto_stats.models import LotteryDraw

def generate_lottery_numbers():
    """สุ่มเลขรางวัล"""
    # รางวัลที่ 1
    first_prize = str(random.randint(100000, 999999))
    
    # เลข 2 ตัวท้าย
    two_digit = first_prize[-2:]
    
    # เลข 3 ตัวหน้า (2 รางวัล)
    three_front = [str(random.randint(100, 999)) for _ in range(2)]
    
    # เลข 3 ตัวหลัง (2 รางวัล)  
    three_back = [str(random.randint(100, 999)) for _ in range(2)]
    
    return {
        'first_prize': first_prize,
        'two_digit': two_digit,
        'three_digit_front': ', '.join(three_front),
        'three_digit_back': ', '.join(three_back)
    }

def create_sample_data():
    """สร้างข้อมูลจำลอง"""
    print("🎲 สร้างข้อมูลจำลองหวยใน LotteryDraw...")
    
    # ล้างข้อมูลเดิม
    LotteryDraw.objects.all().delete()
    print("🗑️ ล้างข้อมูลเดิม")
    
    # สร้างข้อมูล 90 วันล่าสุด (เฉพาะวันที่ 1 และ 16)
    today = date.today()
    created_count = 0
    
    for days_back in range(365):  # ย้อนหลัง 1 ปี
        current_date = today - timedelta(days=days_back)
        
        # เฉพาะวันที่ 1 และ 16 ของทุกเดือน (วันที่หวยออก)
        if current_date.day in [1, 16]:
            lottery_data = generate_lottery_numbers()
            
            LotteryDraw.objects.create(
                draw_date=current_date,
                draw_round=f"{current_date.strftime('%d/%m/%Y')}",
                **lottery_data
            )
            
            created_count += 1
            print(f"✅ สร้างข้อมูลงวดวันที่ {current_date.strftime('%d/%m/%Y')}: {lottery_data['first_prize']}")
            
            if created_count >= 50:  # จำกัดจำนวน
                break
    
    print(f"\n🎉 สร้างข้อมูลจำลองเสร็จสิ้น: {created_count} รายการ")
    
    # แสดงสถิติ
    total_draws = LotteryDraw.objects.count()
    latest_draw = LotteryDraw.objects.order_by('-draw_date').first()
    oldest_draw = LotteryDraw.objects.order_by('draw_date').first()
    
    print(f"📊 สถิติข้อมูล:")
    print(f"   จำนวนรวม: {total_draws} รายการ")
    print(f"   วันที่ล่าสุด: {latest_draw.draw_date if latest_draw else 'ไม่มี'}")
    print(f"   วันที่เก่าสุด: {oldest_draw.draw_date if oldest_draw else 'ไม่มี'}")

if __name__ == '__main__':
    create_sample_data()
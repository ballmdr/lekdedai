from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from collections import Counter
import json

from .models import LotteryDraw, NumberStatistics, HotColdNumber
from .stats_calculator import StatsCalculator

def statistics_page(request):
    """หน้าแสดงสถิติหวย"""
    # ดึงข้อมูล 10 งวดล่าสุด
    recent_draws = LotteryDraw.objects.all()[:10]
    
    # คำนวณสถิติ
    calculator = StatsCalculator()
    
    # เลขฮอต/เย็น
    hot_numbers = calculator.get_hot_numbers(limit=10, days=90)
    cold_numbers = calculator.get_cold_numbers(limit=10)
    
    # สถิติรายเดือน
    monthly_stats = calculator.get_monthly_statistics()
    
    # เตรียมข้อมูลสำหรับ Chart.js
    hot_numbers_labels = json.dumps([item['number'] for item in hot_numbers])
    hot_numbers_data = json.dumps([item['count'] for item in hot_numbers])
    
    cold_numbers_labels = json.dumps([item['number'] for item in cold_numbers])
    cold_numbers_data = json.dumps([item['days'] for item in cold_numbers])
    
    # สถิติรายเดือน
    monthly_labels = json.dumps(list(monthly_stats.keys())[-12:])
    monthly_data = json.dumps([data['most_common_2d']['count'] if data['most_common_2d'] else 0 
                              for data in list(monthly_stats.values())[-12:]])
    
    # สถิติเพิ่มเติม
    stats_summary = calculator.get_statistics_summary()
    
    context = {
        'recent_draws': recent_draws,
        'hot_numbers': hot_numbers[:5],
        'cold_numbers': cold_numbers[:5],
        'hot_numbers_labels': hot_numbers_labels,
        'hot_numbers_data': hot_numbers_data,
        'cold_numbers_labels': cold_numbers_labels,
        'cold_numbers_data': cold_numbers_data,
        'monthly_labels': monthly_labels,
        'monthly_data': monthly_data,
        'stats_summary': stats_summary,
    }
    
    return render(request, 'lotto_stats/statistics.html', context)

def api_hot_cold_numbers(request):
    """API สำหรับดึงเลขฮอต/เย็น"""
    days = int(request.GET.get('days', 90))
    limit = int(request.GET.get('limit', 10))
    
    calculator = StatsCalculator()
    
    data = {
        'hot_2d': calculator.get_hot_numbers(limit=limit, days=days, number_type='2D'),
        'hot_3d': calculator.get_hot_numbers(limit=limit, days=days, number_type='3D'),
        'cold_2d': calculator.get_cold_numbers(limit=limit, number_type='2D'),
        'cold_3d': calculator.get_cold_numbers(limit=limit, number_type='3D'),
        'updated_at': timezone.now().isoformat()
    }
    
    return JsonResponse(data)

def api_number_detail(request, number):
    """API สำหรับดูรายละเอียดของเลข"""
    try:
        # ดึงประวัติการออกของเลข
        draws_with_number = []
        
        if len(number) == 2:
            # เลข 2 ตัว
            draws = LotteryDraw.objects.filter(
                Q(two_digit=number) | 
                Q(first_prize__contains=number)
            ).order_by('-draw_date')[:20]
            
            for draw in draws:
                draws_with_number.append({
                    'date': draw.draw_date.strftime('%d/%m/%Y'),
                    'type': 'เลขท้าย 2 ตัว' if draw.two_digit == number else 'ในรางวัลที่ 1',
                    'first_prize': draw.first_prize
                })
        
        # คำนวณสถิติ
        calculator = StatsCalculator()
        stats = calculator.get_number_statistics(number)
        
        return JsonResponse({
            'number': number,
            'statistics': stats,
            'recent_appearances': draws_with_number
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
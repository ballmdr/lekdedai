from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from collections import Counter
import json
import logging
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required

from .models import LotteryDraw, NumberStatistics, HotColdNumber
from .stats_calculator import StatsCalculator
from .lotto_sync_service import LottoSyncService

logger = logging.getLogger(__name__)

def statistics_page(request):
    """หน้าแสดงสถิติหวย"""
    # ดึงข้อมูล 10 งวดล่าสุด
    recent_draws = LotteryDraw.objects.order_by('-draw_date')[:10]
    
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
    
    # ข้อมูลสำหรับ table และ heatmap แทน chart
    monthly_data_with_labels = []
    for month, data in list(monthly_stats.items())[-12:]:
        count = data['most_common_2d']['count'] if data['most_common_2d'] else 0
        monthly_data_with_labels.append((month, count))
    
    # สถิติเพิ่มเติม
    stats_summary = calculator.get_statistics_summary()
    
    # สถิติใหม่
    running_number_stats = calculator.get_running_number_stats()
    double_number_stats = calculator.get_double_number_stats()
    sequential_number_stats = calculator.get_sequential_number_stats()
    
    # สถานะการซิงค์ข้อมูล
    sync_service = LottoSyncService()
    sync_status = sync_service.get_sync_status()
    
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
        'monthly_data_with_labels': monthly_data_with_labels, # เพิ่มข้อมูลสำหรับ table และ heatmap
        'monthly_stats': monthly_stats,
        'stats_summary': stats_summary,
        'running_number_stats': running_number_stats,
        'double_number_stats': double_number_stats,
        'sequential_number_stats': sequential_number_stats,
        'sync_status': sync_status,
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

def api_sync_status(request):
    """API สำหรับดูสถานะการซิงค์ข้อมูล"""
    try:
        sync_service = LottoSyncService()
        status = sync_service.get_sync_status()
        
        # ตรวจสอบว่า status เป็น dict หรือไม่
        if not isinstance(status, dict):
            return JsonResponse({
                'success': False,
                'error': 'Invalid response format from sync service'
            }, status=500)
        
        return JsonResponse({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        logger.error(f"Error in api_sync_status: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_POST
@staff_member_required
def api_sync_data(request):
    """API สำหรับซิงค์ข้อมูลจาก lottery_checker"""
    try:
        data = json.loads(request.body)
        days_back = data.get('days_back', 7)
        force_update = data.get('force_update', False)
        
        sync_service = LottoSyncService()
        result = sync_service.sync_recent_data(days_back, force_update)
        
        # ตรวจสอบว่า result เป็น dict หรือไม่
        if not isinstance(result, dict):
            return JsonResponse({
                'success': False,
                'error': 'Invalid response format from sync service'
            }, status=500)
        
        # ตรวจสอบว่า result มี key ที่จำเป็นหรือไม่
        if 'success' not in result:
            result['success'] = True  # ถ้าไม่มี success ให้เพิ่มเข้าไป
        
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        logger.error(f"Error in api_sync_data: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_POST
@staff_member_required
def api_sync_specific_date(request):
    """API สำหรับซิงค์ข้อมูลวันที่เฉพาะ"""
    try:
        data = json.loads(request.body)
        date_str = data.get('date')  # Format: 'YYYY-MM-DD'
        force_update = data.get('force_update', False)
        
        if not date_str:
            return JsonResponse({
                'success': False,
                'error': 'กรุณาระบุวันที่'
            }, status=400)
        
        sync_service = LottoSyncService()
        result = sync_service.sync_specific_date(date_str, force_update)
        
        # ตรวจสอบว่า result เป็น dict หรือไม่
        if not isinstance(result, dict):
            return JsonResponse({
                'success': False,
                'error': 'Invalid response format from sync service'
            }, status=500)
        
        # ตรวจสอบว่า result มี key ที่จำเป็นหรือไม่
        if 'success' not in result:
            result['success'] = True  # ถ้าไม่มี success ให้เพิ่มเข้าไป
        
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        logger.error(f"Error in api_sync_specific_date: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
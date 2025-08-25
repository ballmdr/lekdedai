from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import datetime
import json
import logging

from .models import LottoResult
from .lotto_service import LottoService
from utils.lottery_dates import LOTTERY_DATES

logger = logging.getLogger(__name__)

def index(request):
    """หน้าแรกสำหรับตรวจสอบหวย"""
    # ดึงข้อมูลหวยล่าสุด 5 วัน
    latest_results = LottoResult.objects.all()[:5]
    
    # ดึงตัวเลือกวันที่หวยออกสำหรับ dropdown
    draw_date_options = LOTTERY_DATES.get_dropdown_options(limit=50)
    
    context = {
        'latest_results': latest_results,
        'draw_date_options': draw_date_options,
        'title': 'ตรวจสอบหวย'
    }
    
    return render(request, 'lottery_checker/index.html', context)

@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def lotto_result_api(request):
    """API endpoint สำหรับดึงข้อมูลหวย"""
    
    # Handle CORS preflight
    if request.method == "OPTIONS":
        response = JsonResponse({})
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        return response
    
    try:
        # Parse JSON data
        data = json.loads(request.body)
        date = data.get('date')
        month = data.get('month')
        year = data.get('year')
        
        if not all([date, month, year]):
            return JsonResponse({
                'error': 'กรุณาระบุ date, month, และ year',
                'success': False
            }, status=400)
        
        # ใช้ LottoService
        service = LottoService()
        result = service.get_or_fetch_result(date, month, year)
        
        response = JsonResponse(result)
        response["Access-Control-Allow-Origin"] = "*"
        return response
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON',
            'success': False
        }, status=400)
    except Exception as e:
        logger.error(f"Error in lotto_result_api: {e}")
        return JsonResponse({
            'error': 'Internal server error',
            'success': False
        }, status=500)

def latest_results_api(request):
    """API endpoint สำหรับดึงข้อมูลหวยล่าสุด"""
    try:
        days_back = int(request.GET.get('days', 7))
        service = LottoService()
        results = service.get_latest_results(days_back)
        
        return JsonResponse(results)
        
    except Exception as e:
        logger.error(f"Error in latest_results_api: {e}")
        return JsonResponse({
            'error': 'Internal server error',
            'success': False
        }, status=500)

def specific_date_api(request, year, month, day):
    """API endpoint สำหรับดึงข้อมูลหวยวันที่เฉพาะ"""
    try:
        service = LottoService()
        result = service.get_or_fetch_result(day, month, year)
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error in specific_date_api: {e}")
        return JsonResponse({
            'error': 'Internal server error',
            'success': False
        }, status=500)

def clear_data_api(request):
    """API endpoint สำหรับล้างข้อมูลทั้งหมด"""
    try:
        service = LottoService()
        success = service.clear_all_data()
        
        if success:
            return JsonResponse({
                'success': True,
                'message': 'ล้างข้อมูลทั้งหมดสำเร็จ'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'ไม่สามารถล้างข้อมูลได้'
            }, status=500)
        
    except Exception as e:
        logger.error(f"Error in clear_data_api: {e}")
        return JsonResponse({
            'error': 'Internal server error',
            'success': False
        }, status=500)

def statistics_api(request):
    """API endpoint สำหรับดึงสถิติข้อมูล"""
    try:
        service = LottoService()
        stats = service.get_statistics()
        
        return JsonResponse(stats)
        
    except Exception as e:
        logger.error(f"Error in statistics_api: {e}")
        return JsonResponse({
            'error': 'Internal server error',
            'success': False
        }, status=500)

def check_number(request):
    """ตรวจสอบเลขหวย"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            check_date = data.get('date')
            check_month = data.get('month')
            check_year = data.get('year')
            check_number = data.get('number')
            
            if not all([check_date, check_month, check_year, check_number]):
                return JsonResponse({
                    'error': 'กรุณาระบุข้อมูลครบถ้วน',
                    'success': False
                }, status=400)
            
            # ใช้ LottoService ดึงข้อมูล
            service = LottoService()
            result = service.get_or_fetch_result(check_date, check_month, check_year)
            
            if not result['success']:
                return JsonResponse(result)
            
            # ตรวจสอบเลข
            lotto_data = result['data']
            all_numbers = []
            
            # ดึงเลขรางวัลทั้งหมด
            if isinstance(lotto_data, dict):
                for prize_type, numbers in lotto_data.items():
                    if isinstance(numbers, list):
                        all_numbers.extend(numbers)
                    elif isinstance(numbers, str):
                        all_numbers.append(numbers)
            
            # ตรวจสอบว่าเลขที่ตรวจสอบอยู่ในรายการหรือไม่
            is_winner = str(check_number) in all_numbers
            
            # หาประเภทรางวัล
            prize_type = None
            if is_winner:
                for prize_type_name, numbers in lotto_data.items():
                    if isinstance(numbers, list) and str(check_number) in numbers:
                        prize_type = prize_type_name
                        break
                    elif isinstance(numbers, str) and str(check_number) == numbers:
                        prize_type = prize_type_name
                        break
            
            return JsonResponse({
                'success': True,
                'is_winner': is_winner,
                'prize_type': prize_type,
                'check_number': check_number,
                'draw_date': f"{check_date:02d}/{check_month:02d}/{check_year}",
                'source': result['source']
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Invalid JSON',
                'success': False
            }, status=400)
        except Exception as e:
            logger.error(f"Error in check_number: {e}")
            return JsonResponse({
                'error': 'Internal server error',
                'success': False
            }, status=500)
    
    return JsonResponse({
        'error': 'Method not allowed',
        'success': False
    }, status=405)

@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def refresh_lotto_data_api(request):
    """API endpoint สำหรับอัปเดตข้อมูลหวยจาก API กองสลากใหม่"""
    
    # Handle CORS preflight
    if request.method == "OPTIONS":
        response = JsonResponse({})
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        return response
    
    try:
        # Parse JSON data
        data = json.loads(request.body)
        date = data.get('date')
        month = data.get('month')
        year = data.get('year')
        
        if not all([date, month, year]):
            return JsonResponse({
                'error': 'กรุณาระบุ date, month, และ year',
                'success': False
            }, status=400)
        
        # ใช้ LottoService เพื่ออัปเดตข้อมูล
        service = LottoService()
        result = service.refresh_data_from_api(date, month, year)
        
        response = JsonResponse(result)
        response["Access-Control-Allow-Origin"] = "*"
        return response
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON',
            'success': False
        }, status=400)
    except Exception as e:
        logger.error(f"Error in refresh_lotto_data_api: {e}")
        return JsonResponse({
            'error': 'Internal server error',
            'success': False
        }, status=500)

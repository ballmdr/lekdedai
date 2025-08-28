from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import datetime, date, timedelta
import json
import logging
import time

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

@csrf_exempt
@require_http_methods(["POST"])
def check_lottery_quick(request):
    """API สำหรับตรวจหวยด่วนในหน้าแรก - ใช้ผลหวยงวดล่าสุด"""
    try:
        data = json.loads(request.body)
        lottery_number = data.get('lottery_number', '').strip()
        
        if not lottery_number:
            return JsonResponse({
                'success': False,
                'error': 'กรุณากรอกเลขสลากที่ต้องการตรวจ'
            })
        
        if not lottery_number.isdigit():
            return JsonResponse({
                'success': False,
                'error': 'กรุณากรอกเฉพาะตัวเลข'
            })
        
        if len(lottery_number) != 6:
            return JsonResponse({
                'success': False,
                'error': 'กรุณากรอกเลข 6 หลัก'
            })
        
        # ดึงผลหวยงวดล่าสุด
        latest_result = LottoResult.objects.filter(is_valid=True).order_by('-draw_date').first()
        
        if not latest_result:
            return JsonResponse({
                'success': False,
                'error': 'ไม่พบข้อมูลผลหวยล่าสุด'
            })
        
        # ตรวจสอบเลข
        result_data = latest_result.result_data
        if not isinstance(result_data, dict):
            return JsonResponse({
                'success': False,
                'error': 'ข้อมูลผลหวยไม่ถูกต้อง'
            })
        
        # เก็บผลการตรวจสอบ
        prizes_won = []
        is_winner = False
        
        # ตรวจสอบรางวัลต่างๆ
        for prize_type, numbers in result_data.items():
            if isinstance(numbers, list):
                for number in numbers:
                    if str(number) == lottery_number:
                        prizes_won.append(prize_type)
                        is_winner = True
            elif isinstance(numbers, str):
                if numbers == lottery_number:
                    prizes_won.append(prize_type)
                    is_winner = True
        
        # ตรวจสอบเลข 2 ตัวท้าย และ 3 ตัวท้าย
        last_2_digits = lottery_number[-2:]
        last_3_digits = lottery_number[-3:]
        
        # ตรวจสอบกับรางวัลที่ 1 สำหรับเลข 2 ตัวและ 3 ตัวท้าย
        if 'first' in result_data and isinstance(result_data['first'], list):
            for first_prize in result_data['first']:
                if str(first_prize)[-2:] == last_2_digits:
                    prizes_won.append('เลข 2 ตัวท้าย')
                    is_winner = True
                if str(first_prize)[-3:] == last_3_digits:
                    prizes_won.append('เลข 3 ตัวท้าย')
                    is_winner = True
        
        # สร้างข้อความผลลัพธ์
        if is_winner:
            prize_names = {
                'first': 'รางวัลที่ 1',
                'second': 'รางวัลที่ 2', 
                'third': 'รางวัลที่ 3',
                'fourth': 'รางวัลที่ 4',
                'fifth': 'รางวัลที่ 5',
                'เลข 2 ตัวท้าย': 'เลข 2 ตัวท้าย',
                'เลข 3 ตัวท้าย': 'เลข 3 ตัวท้าย'
            }
            
            won_prizes = []
            for prize in prizes_won:
                won_prizes.append(prize_names.get(prize, prize))
            
            message = f"🎉 ยินดีด้วย! เลข {lottery_number} ถูกรางวัล: {', '.join(won_prizes)}"
        else:
            message = f"เลข {lottery_number} ไม่ถูกรางวัล งวดวันที่ {latest_result.formatted_date}"
        
        return JsonResponse({
            'success': True,
            'result': {
                'is_winner': is_winner,
                'message': message,
                'lottery_number': lottery_number,
                'draw_date': latest_result.formatted_date,
                'prizes_won': prizes_won
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'ข้อมูลที่ส่งมาไม่ถูกต้อง'
        })
    except Exception as e:
        logger.error(f"Error in check_lottery_quick: {e}")
        return JsonResponse({
            'success': False,
            'error': 'เกิดข้อผิดพลาดในระบบ'
        })

@csrf_exempt
@require_http_methods(["POST"])
def bulk_fetch_api(request):
    """API สำหรับดึงข้อมูลจาก GLO API ตั้งแต่ 1 มกราคม 2567 (2024)"""
    try:
        data = json.loads(request.body)
        start_date_str = data.get('start_date', '2024-01-01')
        end_date_str = data.get('end_date', None)
        force_update = data.get('force_update', False)
        delay_seconds = data.get('delay_seconds', 1)  # หน่วงเวลาระหว่างการเรียก API
        
        # แปลงวันที่
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            end_date = date.today()
        
        service = LottoService()
        valid_dates = []
        fetched_count = 0
        error_count = 0
        results = []
        
        current_date = start_date
        
        while current_date <= end_date:
            try:
                # ตรวจสอบว่ามีข้อมูลอยู่แล้วหรือไม่
                existing = LottoResult.objects.filter(draw_date=current_date).exists()
                
                if not existing or force_update:
                    logger.info(f"Fetching data for {current_date}")
                    
                    # เรียก API ดึงข้อมูล
                    result = service.get_or_fetch_result(
                        current_date.day, 
                        current_date.month, 
                        current_date.year
                    )
                    
                    # ตรวจสอบว่าได้ข้อมูลรางวัลจริงหรือไม่
                    if result.get('success') and result.get('data'):
                        result_data = result['data']
                        has_lottery_data = _has_valid_lottery_data(result_data)
                        
                        if has_lottery_data:
                            valid_dates.append(current_date.strftime('%Y-%m-%d'))
                            fetched_count += 1
                            results.append(f"✅ {current_date}: พบข้อมูลรางวัล")
                        else:
                            results.append(f"⚠️ {current_date}: ไม่มีข้อมูลรางวัล")
                    else:
                        error_count += 1
                        results.append(f"❌ {current_date}: {result.get('error', 'ไม่สามารถดึงข้อมูลได้')}")
                    
                    # หน่วงเวลาเพื่อไม่ให้ request มากเกินไป
                    if delay_seconds > 0:
                        time.sleep(delay_seconds)
                else:
                    results.append(f"⏭️ {current_date}: มีข้อมูลอยู่แล้ว")
                
            except Exception as e:
                error_count += 1
                results.append(f"❌ {current_date}: เกิดข้อผิดพลาด - {str(e)}")
                logger.error(f"Error fetching {current_date}: {e}")
            
            # เลื่อนไปวันถัดไป
            current_date += timedelta(days=1)
        
        return JsonResponse({
            'success': True,
            'message': f'ดึงข้อมูลเสร็จสิ้น: {fetched_count} สำเร็จ, {error_count} ไม่สำเร็จ',
            'fetched_count': fetched_count,
            'error_count': error_count,
            'valid_dates': valid_dates,
            'total_days': (end_date - start_date).days + 1,
            'results': results[:50]  # จำกัดผลลัพธ์เพื่อไม่ให้ response ใหญ่เกินไป
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON',
            'success': False
        }, status=400)
    except Exception as e:
        logger.error(f"Error in bulk_fetch_api: {e}")
        return JsonResponse({
            'error': str(e),
            'success': False
        }, status=500)

def _has_valid_lottery_data(result_data):
    """ตรวจสอบว่าข้อมูลมีรางวัลจริงหรือไม่"""
    if not isinstance(result_data, dict):
        return False
    
    # ตรวจสอบรูปแบบต่างๆ
    if 'response' in result_data and result_data['response']:
        response_data = result_data['response']
        if isinstance(response_data, dict) and 'result' in response_data:
            result = response_data['result']
            if isinstance(result, dict) and 'data' in result and result['data']:
                data = result['data']
                if isinstance(data, dict) and 'first' in data and data['first']:
                    first_data = data['first']
                    if isinstance(first_data, dict) and 'number' in first_data:
                        numbers = first_data['number']
                        if isinstance(numbers, list) and len(numbers) > 0:
                            return True
    
    return False

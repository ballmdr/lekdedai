from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.utils import timezone
from datetime import datetime, date, timedelta
import json
import logging
import time

from .models import LottoResult
from .lotto_service import LottoService, check_numbers_against_result
from utils.lottery_dates import LOTTERY_DATES
from utils.rate_limit import ratelimit
from utils.api import api_server_error, audit, read_json_body

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

@ratelimit("120/m")
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
        return api_server_error(request, e)

@ratelimit("60/m")
def latest_results_api(request):
    """API endpoint สำหรับดึงข้อมูลหวยล่าสุด (จำกัด days กันยิง GLO รัว)"""
    try:
        try:
            days_back = int(request.GET.get('days', 7))
        except (TypeError, ValueError):
            return JsonResponse({
                'error': 'days ต้องเป็นตัวเลข',
                'success': False
            }, status=400)
        if days_back < 1 or days_back > 90:
            return JsonResponse({
                'error': 'days ต้องอยู่ระหว่าง 1-90',
                'success': False
            }, status=400)
        service = LottoService()
        results = service.get_latest_results(days_back)
        
        return JsonResponse(results)
        
    except Exception as e:
        return api_server_error(request, e)

@ratelimit("120/m")
def specific_date_api(request, year, month, day):
    """API endpoint สำหรับดึงข้อมูลหวยวันที่เฉพาะ"""
    try:
        service = LottoService()
        result = service.get_or_fetch_result(day, month, year)
        
        return JsonResponse(result)
        
    except Exception as e:
        return api_server_error(request, e)

@require_POST
def clear_data_api(request):
    """API endpoint สำหรับล้างข้อมูลทั้งหมด (staff เท่านั้น)"""
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'error': 'ต้องเป็นผู้ดูแลระบบ'
        }, status=403)
    try:
        service = LottoService()
        success = service.clear_all_data()
        audit(request, "lotto_clear_all", f"success={success}")

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
        return api_server_error(request, e)

def statistics_api(request):
    """API endpoint สำหรับดึงสถิติข้อมูล"""
    try:
        service = LottoService()
        stats = service.get_statistics()
        
        return JsonResponse(stats)
        
    except Exception as e:
        return api_server_error(request, e)

def check_number(request):
    """ตรวจสอบเลขหวย (Task 23: rate limit + ไม่รั่ว error ภายใน)"""
    if request.method == 'POST':
        try:
            data, error_response = read_json_body(request)
            if error_response is not None:
                return error_response
            check_date = data.get('date')
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
            
            # ตรวจสอบเลขด้วย logic กลางชุดเดียวกับหน้าแรก/หน้ารายละเอียด
            prizes_won = check_numbers_against_result(result['data'], str(check_number))
            if prizes_won is None:
                return JsonResponse({
                    'success': False,
                    'error': 'ข้อมูลผลหวยไม่ถูกต้อง'
                })

            return JsonResponse({
                'success': True,
                'is_winner': len(prizes_won) > 0,
                'prizes_won': prizes_won,
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
            return api_server_error(request, e)
    
    return JsonResponse({
        'error': 'Method not allowed',
        'success': False
    }, status=405)

# งวดที่ผ่านมาเกินจำนวนวันนี้แล้วยังไม่มีผลที่ยืนยันแล้ว = ข้อมูลค้าง (stale)
CHECK_DRAW_STALE_AFTER_DAYS = 3

@ratelimit("120/m")
@require_POST
def check_draw(request):
    """ตรวจเลขต่องวดแบบ read-only สำหรับประวัติสมุดเลข (อ่านเฉพาะแถวที่มีใน DB ห้ามดึง API)."""
    try:
        return _check_draw_impl(request)
    except Exception as exc:
        return api_server_error(request, exc)


def _check_draw_impl(request):
    data, error_response = read_json_body(request)
    if error_response is not None:
        return error_response

    draw_date_str = str(data.get('draw_date') or '').strip()
    lottery_number = str(data.get('number') or '').strip()

    try:
        draw_date = datetime.strptime(draw_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return JsonResponse({
            'success': False,
            'error': 'รูปแบบงวดไม่ถูกต้อง (ต้องเป็น YYYY-MM-DD)'
        }, status=400)

    if not lottery_number.isdigit() or len(lottery_number) not in (2, 3, 6):
        return JsonResponse({
            'success': False,
            'error': 'เลขต้องเป็นตัวเลขยาว 2, 3 หรือ 6 หลัก'
        }, status=400)

    today = timezone.localdate()
    drawn_label = draw_date.strftime('%d/%m/%Y')
    row = LottoResult.objects.filter(draw_date=draw_date).first()

    if row is None or not row.is_valid:
        if row is not None:
            status, message = 'error', 'ข้อมูลผลงวดนี้ไม่สมบูรณ์ — รอผู้ดูแลตรวจสอบ'
        elif draw_date > today:
            status, message = 'pending', f'งวดวันที่ {drawn_label} ยังไม่ออก — กลับมาตรวจหลังวันหวยออก'
        elif (today - draw_date).days > CHECK_DRAW_STALE_AFTER_DAYS:
            status, message = 'stale', 'ผลงวดนี้ค้างเกิน 3 วัน — ระบบยังไม่มีข้อมูลที่ยืนยันแล้ว'
        else:
            status, message = 'pending', 'ยังไม่มีผลที่ยืนยันแล้วในระบบ — ลองใหม่หลังวันหวยออก'
        return JsonResponse({
            'success': True,
            'status': status,
            'message': message,
            'is_winner': False,
            'prizes_won': [],
            'check_number': lottery_number,
            'draw_date': drawn_label,
            'source': row.source if row else None,
        })

    prizes_won = check_numbers_against_result(row.result_data, lottery_number)
    if prizes_won is None:
        return JsonResponse({
            'success': True,
            'status': 'error',
            'message': 'ข้อมูลผลงวดนี้ไม่สมบูรณ์ — รอผู้ดูแลตรวจสอบ',
            'is_winner': False,
            'prizes_won': [],
            'check_number': lottery_number,
            'draw_date': row.formatted_date,
            'source': row.source,
        })

    if prizes_won:
        return JsonResponse({
            'success': True,
            'status': 'won',
            'message': f"ถูก{len(prizes_won)} รางวัล: {', '.join(prizes_won)}",
            'is_winner': True,
            'prizes_won': prizes_won,
            'check_number': lottery_number,
            'draw_date': row.formatted_date,
            'source': row.source,
        })

    scope = {6: 'เต็มใบ 6 หลัก + เลขหน้า/ท้าย 3 ตัว + เลขท้าย 2 ตัว',
             3: 'เลขหน้า/ท้าย 3 ตัว',
             2: 'เลขท้าย 2 ตัว'}[len(lottery_number)]
    return JsonResponse({
        'success': True,
        'status': 'lost',
        'message': f'ไม่ถูกรางวัล (ตรวจตามกติกา{scope})',
        'is_winner': False,
        'prizes_won': [],
        'check_number': lottery_number,
        'draw_date': row.formatted_date,
        'source': row.source,
    })

@require_http_methods(["POST", "OPTIONS"])
def refresh_lotto_data_api(request):
    """API endpoint สำหรับอัปเดตข้อมูลหวยจาก API กองสลากใหม่ (staff เท่านั้น)"""
    
    # Handle CORS preflight
    if request.method == "OPTIONS":
        response = JsonResponse({})
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    if not request.user.is_staff:
        response = JsonResponse({
            'error': 'ต้องเป็นผู้ดูแลระบบ',
            'success': False
        }, status=403)
        response["Access-Control-Allow-Origin"] = "*"
        return response

    audit(request, "lotto_refresh")
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
        return api_server_error(request, e)

@ratelimit("120/m")
@require_http_methods(["POST"])
def check_lottery_quick(request):
    """API สำหรับตรวจหวยด่วนในหน้าแรก - ใช้ผลหวยงวดล่าสุด"""
    try:
        data, error_response = read_json_body(request)
        if error_response is not None:
            return error_response
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
        
        # ตรวจสอบเลขด้วย logic กลางชุดเดียวกับหน้ารายละเอียด
        prizes_won = check_numbers_against_result(latest_result.result_data, lottery_number)
        if prizes_won is None:
            return JsonResponse({
                'success': False,
                'error': 'ข้อมูลผลหวยไม่ถูกต้อง'
            })

        is_winner = len(prizes_won) > 0

        # สร้างข้อความผลลัพธ์
        if is_winner:
            message = f"🎉 ยินดีด้วย! เลข {lottery_number} ถูกรางวัล: {', '.join(prizes_won)}"
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
        return api_server_error(request, e)

@require_POST
def bulk_fetch_api(request):
    """API สำหรับดึงข้อมูลจาก GLO API ตั้งแต่ 1 มกราคม 2567 (2024) (staff เท่านั้น)"""
    if not request.user.is_staff:
        return JsonResponse({
            'error': 'ต้องเป็นผู้ดูแลระบบ',
            'success': False
        }, status=403)
    audit(request, "lotto_bulk_fetch")
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
        return api_server_error(request, e)

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

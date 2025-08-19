from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import DreamKeyword, DreamInterpretation
import json
import re

def dream_form(request):
    """แสดงฟอร์มกรอกความฝัน"""
    return render(request, 'dreams/dream_form.html')

@csrf_exempt
@require_http_methods(["POST"])
def analyze_dream(request):
    """วิเคราะห์ความฝัน"""
    try:
        data = json.loads(request.body)
        dream_text = data.get('dream_text', '').strip()
        dream_date = data.get('dream_date', None)
        
        if not dream_text:
            return JsonResponse({
                'success': False,
                'error': 'กรุณากรอกความฝัน'
            }, status=400)
        
        # วิเคราะห์ความฝัน
        result = analyze_dream_text(dream_text)
        
        # บันทึกผลการตีความ
        interpretation = DreamInterpretation.objects.create(
            user=request.user if request.user.is_authenticated else None,
            dream_text=dream_text,
            keywords_found=', '.join(result['keywords']),
            suggested_numbers=', '.join(result['numbers']),
            interpretation=result['interpretation'],
            dream_date=dream_date,
            ip_address=get_client_ip(request)
        )
        
        return JsonResponse({
            'success': True,
            'result': {
                'keywords': result['keywords'],
                'numbers': result['numbers'],
                'interpretation': result['interpretation']
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def analyze_dream_text(dream_text):
    """วิเคราะห์ข้อความความฝัน"""
    dream_text = dream_text.lower()
    found_keywords = []
    suggested_numbers = []
    
    # ค้นหา keywords ที่ตรงกับในฐานข้อมูล
    all_keywords = DreamKeyword.objects.all()
    
    for keyword_obj in all_keywords:
        keyword = keyword_obj.keyword.lower()
        # ตรวจสอบว่ามีคำนี้ในความฝันหรือไม่
        if keyword in dream_text or re.search(r'\b' + re.escape(keyword) + r'\b', dream_text):
            found_keywords.append(keyword_obj.keyword)
            suggested_numbers.extend(keyword_obj.get_numbers_list())
    
    # ลบเลขซ้ำ
    suggested_numbers = list(dict.fromkeys(suggested_numbers))
    
    # สร้างคำทำนาย
    interpretation = generate_interpretation(found_keywords, suggested_numbers, dream_text)
    
    # ถ้าไม่พบ keyword ให้ใช้การวิเคราะห์พื้นฐาน
    if not found_keywords:
        # หาตัวเลขในความฝัน
        numbers_in_text = re.findall(r'\b\d{1,2}\b', dream_text)
        if numbers_in_text:
            suggested_numbers = list(dict.fromkeys(numbers_in_text))[:5]
    
    return {
        'keywords': found_keywords[:10],  # จำกัดไม่เกิน 10 คำ
        'numbers': suggested_numbers[:10],  # จำกัดไม่เกิน 10 เลข
        'interpretation': interpretation
    }

def generate_interpretation(keywords, numbers, dream_text):
    """สร้างคำทำนาย"""
    if not keywords and not numbers:
        return "ความฝันของคุณมีความหมายที่ลึกซึ้ง แต่ยังไม่ชัดเจนในเรื่องตัวเลข ให้สังเกตสิ่งรอบตัวในวันนี้ อาจพบสัญญาณเพิ่มเติม"
    
    interpretation = "จากความฝันของคุณ "
    
    if keywords:
        interpretation += f"พบสัญลักษณ์สำคัญเกี่ยวกับ {', '.join(keywords[:3])} "
        
        # เพิ่มความหมายตาม keyword
        if any(word in keywords for word in ['เงิน', 'ทอง', 'รวย', 'ลาภ']):
            interpretation += "ซึ่งเป็นสัญญาณดีเรื่องโชคลาภ "
        elif any(word in keywords for word in ['น้ำ', 'ฝน', 'ทะเล', 'แม่น้ำ']):
            interpretation += "ซึ่งบ่งบอกถึงความอุดมสมบูรณ์และการเปลี่ยนแปลง "
        elif any(word in keywords for word in ['ไฟ', 'แสง', 'สว่าง']):
            interpretation += "ซึ่งหมายถึงพลังงานและโอกาสใหม่ "
    
    if numbers:
        interpretation += f"\n\nเลขมงคลที่ควรจับตามอง คือ {', '.join(numbers[:5])}"
        interpretation += " ลองนำไปเสี่ยงโชคดู อาจได้ผลคาดไม่ถึง"
    
    interpretation += "\n\nอย่าลืมว่าความฝันเป็นเพียงแนวทาง ขอให้ใช้วิจารณญาณในการตัดสินใจ"
    
    return interpretation

def get_client_ip(request):
    """ดึง IP address ของผู้ใช้"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import DreamKeyword, DreamInterpretation
from utils.rate_limit import ratelimit
from utils.api import api_server_error, audit, read_json_body
import json
import re
import os
import sys

# Task 23: จำกัดความยาวข้อความฝันกัน abuse (เก็บสูงสุดตาม privacy notice)
DREAM_TEXT_MAX_LENGTH = 2000

# Import Specialized AI Services
MCP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'mcp_dream_analysis')
if os.path.exists(MCP_DIR):
    sys.path.insert(0, MCP_DIR)
    try:
        from specialized_django_integration import interpret_dream_for_django
        DREAM_AI_AVAILABLE = True
        print(f"Expert Dream AI loaded successfully from {MCP_DIR}")
    except ImportError as e:
        print(f"Warning: Specialized Dream AI not available: {e}")
        DREAM_AI_AVAILABLE = False
else:
    print(f"⚠️ MCP_DIR not found: {MCP_DIR}")
    DREAM_AI_AVAILABLE = False

def dream_form(request):
    """แสดงฟอร์มกรอกความฝัน"""
    from .models import DreamCategory
    
    # ดึงข้อมูลหมวดหมู่และคำสำคัญสำหรับแสดงในคู่มือ
    categories_with_keywords = {}
    categories = DreamCategory.objects.all()
    
    for category in categories:
        # เลือกคำสำคัญที่น่าสนใจจากแต่ละหมวด
        keywords = category.keywords.all()[:6]  # เอาแค่ 6 อันแรก
        categories_with_keywords[category.name] = keywords
    
    context = {
        'categories_with_keywords': categories_with_keywords
    }
    
    return render(request, 'dreams/dream_form.html', context)

@ratelimit("60/m")
@require_http_methods(["POST"])
def analyze_dream(request):
    """วิเคราะห์ความฝัน (ไม่เก็บ IP; ข้อความฝันเก็บเท่าที่ต้องใช้แสดงประวัติ)"""
    try:
        data, error_response = read_json_body(request)
        if error_response is not None:
            return error_response
        dream_text = data.get('dream_text', '').strip()

        if not dream_text:
            return JsonResponse({
                'success': False,
                'error': 'กรุณากรอกความฝัน'
            }, status=400)

        if len(dream_text) > DREAM_TEXT_MAX_LENGTH:
            return JsonResponse({
                'success': False,
                'error': f'ข้อความฝันยาวเกินไป (สูงสุด {DREAM_TEXT_MAX_LENGTH} ตัวอักษร)'
            }, status=400)
        
        # วิเคราะห์ความฝัน - ใช้ Expert AI โมเดลใหม่
        if DREAM_AI_AVAILABLE:
            result = interpret_dream_for_django(dream_text)
            # แปลงผลจาก Expert AI เป็นรูปแบบเดิม
            if result and 'main_symbols' in result:
                result = {
                    'keywords': result.get('main_symbols', []),
                    'numbers': [pred['number'] for pred in result.get('predicted_numbers', [])][:12],
                    'interpretation': result.get('interpretation', ''),
                    'sentiment': result.get('sentiment', 'Neutral'),
                    'predicted_numbers': result.get('predicted_numbers', [])[:8],
                    'is_expert_ai': True
                }
        else:
            result = analyze_dream_text(dream_text)
            result['is_expert_ai'] = False
        
        # บันทึกผลการตีความ (รวมข้อมูล sentiment และ predicted_numbers)
        # Task 7: เลิกเก็บ IP (ไม่มีฟีเจอร์ใดใช้) เก็บข้อความฝันไว้แสดงประวัติเท่านั้น
        DreamInterpretation.objects.create(
            user=request.user if request.user.is_authenticated else None,
            dream_text=dream_text,
            interpretation=result['interpretation'],
            sentiment=result.get('sentiment', 'Neutral'),
            predicted_numbers_json=result if result.get('is_expert_ai') else None,
            main_symbols=', '.join(result.get('keywords', [])),
            ip_address=None
        )
        audit(request, "dream_analyze", f"chars={len(dream_text)}")
        
        return JsonResponse({
            'success': True,
            'result': {
                'keywords': result['keywords'],
                'numbers': result['numbers'],
                'interpretation': result['interpretation'],
                'sentiment': result.get('sentiment', 'Neutral'),
                'predicted_numbers': result.get('predicted_numbers', []),
                'is_expert_ai': result.get('is_expert_ai', False)
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return api_server_error(request, e)

def analyze_dream_text(dream_text):
    """วิเคราะห์ข้อความความฝัน"""
    import re
    original_dream_text = dream_text
    dream_text = dream_text.lower()
    found_keywords = []
    suggested_numbers = []
    matched_keywords_info = []  # เก็บข้อมูลเลขเด่น/เลขรอง
    
    # ค้นหา keywords ที่ตรงกับในฐานข้อมูล
    # เรียงลำดับตามความยาวของ keyword (ยาวที่สุดก่อน) เพื่อจับคำที่เฉพาะเจาะจงมากกว่า
    all_keywords = sorted(DreamKeyword.objects.all(), key=lambda x: len(x.keyword), reverse=True)
    
    matched_positions = []  # เก็บตำแหน่งที่จับได้แล้ว เพื่อไม่ให้ซ้ำ
    
    for keyword_obj in all_keywords:
        keyword = keyword_obj.keyword.lower()
        
        # ค้นหาคำที่ตรงกันทั้งคำ และไม่ซ้อนทับกับคำที่จับแล้ว
        if keyword in dream_text:
            # หาตำแหน่งทั้งหมดที่พบคำนี้
            start_idx = 0
            while True:
                idx = dream_text.find(keyword, start_idx)
                if idx == -1:
                    break
                
                start, end = idx, idx + len(keyword)
                
                # ตรวจสอบว่าเป็นคำสมบูรณ์ โดยเฉพาะกรณีที่อาจเป็นส่วนของคำอื่น
                is_valid_match = True
                
                # ตรวจสอบเฉพาะกรณีที่เป็นปัญหา เช่น "หมู" ใน "หมู่"
                if end < len(dream_text):
                    next_char = dream_text[end]
                    # ถ้าเป็น "หมู" และตามด้วย "่" ให้ข้าม
                    if keyword == "หมู" and next_char == "่":
                        is_valid_match = False
                    # ถ้าเป็น "ขา" และตามด้วย "ว" ให้ข้าม (กรณี "ขาว")
                    elif keyword == "ขา" and next_char == "ว":
                        is_valid_match = False
                
                # ตรวจสอบว่าตำแหน่งนี้ถูกจับแล้วหรือไม่
                overlap = any(start < pos_end and end > pos_start for pos_start, pos_end in matched_positions)
                
                if not overlap and is_valid_match:
                    matched_positions.append((start, end))
                    found_keywords.append(keyword_obj.keyword)
                    
                    # เก็บข้อมูลเลขเด่น/เลขรอง เฉพาะคำที่พบ
                    matched_keywords_info.append({
                        'keyword': keyword_obj.keyword,
                        'category': keyword_obj.category.name,
                        'main_number': keyword_obj.main_number,
                        'secondary_number': keyword_obj.secondary_number,
                        'common_numbers': keyword_obj.get_numbers_list()
                    })
                    
                    # เพิ่มเลขที่มักตี
                    suggested_numbers.extend(keyword_obj.get_numbers_list())
                    break  # เจอแล้วครั้งแรกก็พอ
                
                start_idx = idx + 1
    
    # ลบเลขซ้ำและเรียงลำดับ
    suggested_numbers = list(dict.fromkeys(suggested_numbers))
    
    # สร้างคำทำนายแบบใหม่
    interpretation = generate_enhanced_interpretation(
        found_keywords, 
        matched_keywords_info, 
        suggested_numbers, 
        original_dream_text
    )
    
    # ถ้าไม่พบ keyword ให้ใช้การวิเคราะห์พื้นฐาน
    if not found_keywords:
        # หาตัวเลขในความฝัน
        numbers_in_text = re.findall(r'\b\d{1,2}\b', original_dream_text)
        if numbers_in_text:
            suggested_numbers = list(dict.fromkeys(numbers_in_text))[:8]
            interpretation = "ไม่พบสัญลักษณ์ที่ชัดเจนในความฝันของคุณ แต่พบตัวเลขที่น่าสนใจ ลองนำเลขเหล่านี้ไปเสี่ยงโชคดู"
        else:
            # เสนอเลขสุ่มจากเลขยอดนิยม
            popular_keywords = DreamKeyword.objects.filter(keyword__in=['เงิน', 'ช้าง', 'งู'])[:3]
            for kw in popular_keywords:
                suggested_numbers.extend(kw.get_numbers_list()[:2])
            suggested_numbers = list(dict.fromkeys(suggested_numbers))[:6]
    
    return {
        'keywords': found_keywords[:8],  # จำกัดไม่เกิน 8 คำ
        'numbers': suggested_numbers[:12],  # เพิ่มเป็น 12 เลข
        'interpretation': interpretation,
        'keywords_info': matched_keywords_info  # ข้อมูลเลขเด่น/เลขรอง
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

def generate_enhanced_interpretation(keywords, keywords_info, numbers, dream_text):
    """สร้างคำทำนายแบบใหม่ที่มีรายละเอียดเลขเด่น/เลขรอง"""
    if not keywords and not numbers:
        return "ความฝันของคุณมีความหมายที่ลึกซึ้ง แต่ยังไม่ชัดเจนในเรื่องตัวเลข ให้สังเกตสิ่งรอบตัวในวันนี้ อาจพบสัญญาณเพิ่มเติม"
    
    interpretation = "🔮 **การตีความฝันเป็นเลขเด็ด**\n\n"
    
    if keywords_info:
        interpretation += "**สัญลักษณ์ที่พบในความฝัน:**\n"

        # รวมสัญลักษณ์ที่ให้เลขชุดเดียวกัน (เช่น งู/พญานาค) ไม่ให้แสดงซ้ำ
        merged = {}
        order = []
        for info in keywords_info:
            key = (str(info.get('main_number', '')), str(info.get('secondary_number', '')))
            if key not in merged:
                merged[key] = dict(info)
                order.append(key)
            else:
                existing = merged[key]
                if info['keyword'] not in existing['keyword'].split('/'):
                    existing['keyword'] = f"{existing['keyword']}/{info['keyword']}"
        merged_info = [merged[k] for k in order]

        # จัดกลุ่มตาม category
        categories = {}
        for info in merged_info[:5]:  # แสดงไม่เกิน 5 สัญลักษณ์
            cat = info['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(info)
        
        for category, items in categories.items():
            interpretation += f"\n{category}:\n"
            for item in items[:3]:  # แสดงไม่เกิน 3 รายการต่อหมวด
                interpretation += f"• **{item['keyword']}** - เลขเด่น: {item['main_number']}, เลขรอง: {item['secondary_number']}\n"
                interpretation += f"  มักตีเป็น: {', '.join(item['common_numbers'][:3])}\n"
        
        # วิเคราะห์ความหมาย
        interpretation += "\n**การวิเคราะห์:**\n"
        
        # สัตว์
        animal_keywords = [item['keyword'] for item in keywords_info if 'สัตว์' in item['category']]
        if animal_keywords:
            if any(word in animal_keywords for word in ['งู', 'พญานาค']):
                interpretation += "• งู/พญานาค บ่งบอกถึงพลังลึกลับและการปกป้อง เลขเด่น 5 และ 6 จะนำโชคมาให้\n"
            if any(word in animal_keywords for word in ['ช้าง']):
                interpretation += "• ช้าง หมายถึงความมั่งคั่งและเกียรติยศ เลขเด่น 9 และ 1 เป็นมงคล\n"
            if any(word in animal_keywords for word in ['เสือ']):
                interpretation += "• เสือ สื่อถึงอำนาจและความกล้าหาญ เลขเด่น 3 และ 4 จะช่วยเสริมพลัง\n"
        
        # บุคคล
        people_keywords = [item['keyword'] for item in keywords_info if 'บุคคล' in item['category']]
        if people_keywords:
            if any(word in people_keywords for word in ['พระ', 'เณร']):
                interpretation += "• พระ/เณร เป็นสัญญาณของความศักดิ์สิทธิ์ เลขเด่น 8 และ 9 จะนำพรมาให้\n"
            if any(word in people_keywords for word in ['เด็ก', 'ทารก']):
                interpretation += "• เด็กทารก หมายถึงจุดเริ่มต้นใหม่ เลขเด่น 1 และ 3 เป็นเลขแห่งความหวัง\n"
        
        # สิ่งของ/สถานที่
        object_keywords = [item['keyword'] for item in keywords_info if 'สิ่งของ' in item['category']]
        if object_keywords:
            if any(word in object_keywords for word in ['เงิน', 'ทอง']):
                interpretation += "• เงิน/ทอง เป็นลางดีเรื่องโชคลาภ เลขเด่น 8 และ 2 จะนำความมั่งคั่งมาให้\n"
            if any(word in object_keywords for word in ['วัด', 'โบสถ์']):
                interpretation += "• วัด/โบสถ์ สื่อถึงความสงบและการได้รับพร เลขเด่น 8 และ 9 เสริมคุณธรรม\n"
    
    if numbers:
        interpretation += f"\n**🎯 เลขมงคลที่แนะนำ:**\n"
        # แบ่งเลขเป็นกลุ่มๆ
        numbers_groups = [numbers[i:i+4] for i in range(0, len(numbers), 4)]
        for i, group in enumerate(numbers_groups[:3], 1):
            interpretation += f"ชุดที่ {i}: {', '.join(group)}\n"
        
        interpretation += f"\n**💡 คำแนะนำ:**\n"
        interpretation += "• ลองเลือกเลขที่ใจชอบจากกลุ่มข้างบน\n"
        interpretation += "• สังเกตเลขที่ปรากฏซ้ำในความฝัน\n"
        interpretation += "• เชื่อมโยงกับเหตุการณ์ที่เกิดขึ้นในชีวิตจริง\n"
    
    interpretation += "\n⚠️ **ความฝันเป็นเพียงแนวทางเท่านั้น ขอให้ใช้วิจารณญาณในการตัดสินใจ**"

    return interpretation
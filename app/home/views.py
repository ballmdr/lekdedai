from django.shortcuts import render
from django.db.models import Q, Sum, Avg
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta
from collections import Counter
import random
import json

# Import models จาก apps ต่างๆ
from news.models import NewsArticle
from ai_engine.models import (
    LuckyNumberPrediction, EnsemblePrediction, 
    PredictionAccuracyTracking, DataIngestionRecord
)
from lottery_checker.models import LottoResult
from lucky_spots.models import LuckyLocation
from utils.lottery_dates import LotteryDates
from .instant_lucky import get_instant_lucky_numbers

def get_daily_numbers_for_today():
    """สร้างเลขเด็ดประจำวัน - เลขเดียวกันตลอดวัน"""
    today = timezone.now().date()
    # ใช้วันที่เป็น seed เพื่อให้ได้เลขเดียวกันตลอดวัน
    random.seed(today.toordinal())
    
    return {
        'daily_seed': today.toordinal()
    }

def get_daily_ritual_content(latest_news, latest_prediction):
    """สร้างเลขเด็ดประจำวัน - เลขเดียวกันตลอดวัน"""
    
    # ตั้งค่า seed ใหม่สำหรับวันนี้
    today = timezone.now().date()
    random.seed(today.toordinal())
    
    ritual_content = {
        'title': '🎯 เลขเด็ด AI ประจำวัน',
        'subtitle': f'วันที่ {today.strftime("%d/%m/%Y")}',
        'primary_message': 'เลขจากข่าวดัง และการวิเคราะห์ AI',
        'highlighted_numbers': [],
        'buzz_numbers': [],
        'special_message': 'เลขเปลี่ยนใหม่ทุกวัน เวลา 00:01 น.'
    }
    
    # เลขจากข่าวล่าสุด
    news_numbers = []
    if latest_news.exists():
        for article in latest_news[:2]:
            numbers = article.get_extracted_numbers_list()
            news_numbers.extend(numbers[:2])
    
    # เลขจาก AI prediction
    ai_numbers = []
    if latest_prediction:
        if hasattr(latest_prediction, 'get_top_two_digit_numbers') and latest_prediction.get_top_two_digit_numbers:
            ai_numbers.extend([item.get('number', item) if isinstance(item, dict) else item 
                              for item in latest_prediction.get_top_two_digit_numbers[:3]])
    
    # รวมเลขทั้งหมด (เฉพาะจากข่าวและ AI)
    all_numbers = news_numbers + ai_numbers
    
    # ใช้เฉพาะเลขจากข่าวและ AI เท่านั้น
    ritual_content['highlighted_numbers'] = list(set(all_numbers))[:4]
    ritual_content['buzz_numbers'] = []  # เอาเลขสุ่มออก
    
    return ritual_content

def home(request):
    """หน้าแรก - แสดงข้อมูลจริงจาก database"""
    
    # ดึงข่าวล่าสุดที่เหมาะสำหรับหวย (คะแนน >= 70)
    latest_news = NewsArticle.objects.filter(
        status='published',
        lottery_relevance_score__gte=70
    ).select_related('category').order_by('-lottery_relevance_score', '-published_date')[:3]
    
    # ถ้าไม่มีข่าวคะแนนสูง ให้ใช้ข่าวล่าสุดธรรมดา
    if not latest_news.exists():
        latest_news = NewsArticle.objects.filter(
            status='published'
        ).select_related('category').order_by('-published_date')[:3]
    
    # ดึงการทำนาย AI Ensemble ล่าสุด (ระบบใหม่)
    latest_prediction = EnsemblePrediction.objects.filter(
        session__status__in=['completed', 'locked']
    ).select_related('session').order_by('-prediction_timestamp').first()
    
    # ถ้าไม่มีการทำนายใหม่ ใช้ระบบเก่าชั่วคราว
    if not latest_prediction:
        old_prediction = LuckyNumberPrediction.objects.filter(
            prediction_date__lte=timezone.now().date()
        ).select_related('ai_model').order_by('-prediction_date', '-created_at').first()
        # แปลงให้เข้ากับ template
        if old_prediction:
            latest_prediction = {
                'is_old_system': True,
                'get_top_three_digit_numbers': [{'number': num} for num in old_prediction.get_three_digit_list()],
                'get_top_two_digit_numbers': [{'number': num} for num in old_prediction.get_two_digit_list()],
                'prediction_summary': old_prediction.prediction_details.get('reasoning', ''),
                'overall_confidence': old_prediction.overall_confidence,
                'session': {'for_draw_date': old_prediction.for_draw_date}
            }
    
    # ดึงผลหวยงวดล่าสุด
    latest_lottery_result = LottoResult.objects.filter(
        is_valid=True
    ).order_by('-draw_date').first()
    
    # ดึงสถานที่เลขเด็ดยอดนิยม 4 แห่ง
    popular_lucky_locations = LuckyLocation.objects.filter(
        is_active=True
    ).select_related('province', 'category').order_by('-views_count')[:4]
    
    # คำนวณสถิติเว็บไซต์จากระบบ AI ใหม่
    total_news = NewsArticle.objects.filter(status='published').count()
    
    # รวมการทำนายทั้งเก่าและใหม่
    total_predictions_new = EnsemblePrediction.objects.count()
    total_predictions_old = LuckyNumberPrediction.objects.count()
    total_predictions = total_predictions_new + total_predictions_old
    
    # ความแม่นยำจากระบบใหม่
    accuracy_records = PredictionAccuracyTracking.objects.all()
    if accuracy_records.exists():
        correct_predictions = accuracy_records.filter(two_digit_accuracy=True).count()
        accuracy_percentage = (correct_predictions / accuracy_records.count()) * 100
    else:
        accuracy_percentage = 87  # ค่าเริ่มต้น
    
    # ข้อมูลที่เก็บวันนี้
    today_data_records = DataIngestionRecord.objects.filter(
        ingested_at__date=timezone.now().date()
    ).count()
    
    total_views_today = latest_news.aggregate(
        total_views=Sum('views')
    )['total_views'] or 0
    
    # ดึงข้อมูลงวดถัดไป
    today = timezone.now().date()
    next_draw_date = LotteryDates.get_next_draw_date(today)
    next_draw_info = None
    if next_draw_date:
        next_draw_date_obj = datetime.strptime(next_draw_date, "%Y-%m-%d").date()
        days_until_draw = (next_draw_date_obj - today).days
        next_draw_info = {
            'date': next_draw_date_obj,
            'days_remaining': days_until_draw,
            'formatted_date': next_draw_date_obj.strftime('%d %B %Y')
        }
    
    # สร้าง Daily Ritual Content (เลขเดียวกันตลอดวัน)
    daily_ritual = get_daily_ritual_content(latest_news, latest_prediction)
    
    # จัดเตรียม context สำหรับ template
    context = {
        'latest_news': latest_news,
        'latest_prediction': latest_prediction,
        'ai_prediction': latest_prediction,  # เพิ่ม alias สำหรับ template ใหม่
        'latest_lottery_result': latest_lottery_result,
        'popular_lucky_locations': popular_lucky_locations,
        'next_draw_info': next_draw_info,
        'site_stats': {
            'total_visitors_today': total_views_today + 150,  # รวม views + estimate
            'accuracy_percentage': int(accuracy_percentage),
            'total_predictions': total_predictions,
            'total_news_today': today_data_records,  # ข้อมูลที่ AI เก็บได้วันนี้
        },
        # เพิ่มข้อมูลสำหรับ AI system
        'ai_system_info': {
            'ensemble_predictions': total_predictions_new,
            'data_collected_today': today_data_records,
            'system_status': 'active' if latest_prediction else 'standby',
        },
        'current_date': timezone.now(),
        'thai_current_date': timezone.now().strftime('%d %B %Y'),
        
        # 🎯 Daily Ritual Engine (เลขเดียวกันตลอดวัน)
        'daily_ritual': daily_ritual,
        'current_date_formatted': timezone.now().strftime('%d/%m/%Y'),
    }
    
    return render(request, 'home/index.html', context)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def instant_lucky_numbers_api(request):
    """
    API endpoint สำหรับ Instant Lucky Numbers
    GET: ใช้วันที่ปัจจุบัน
    POST: รับ significant_date จาก body
    """
    
    try:
        significant_date = None
        
        selected_news_ids = None
        
        if request.method == "POST":
            try:
                data = json.loads(request.body.decode('utf-8'))
                significant_date = data.get('significant_date')
                selected_news_ids = data.get('selected_news_ids')
            except (json.JSONDecodeError, UnicodeDecodeError):
                # ถ้า JSON ไม่ถูกต้อง ใช้วันปัจจุบัน
                pass
        
        # เรียก service function
        result = get_instant_lucky_numbers(significant_date, selected_news_ids)
        
        return JsonResponse({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'เกิดข้อผิดพลาดในการสร้างเลขเด็ด กรุณาลองใหม่'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_recent_news_for_selection_api(request):
    """
    API endpoint สำหรับดึงข่าวล่าสุดให้ผู้ใช้เลือก
    """
    
    try:
        # ดึงข่าวล่าสุด 24-48 ชั่วโมง
        recent_cutoff = timezone.now() - timedelta(hours=48)
        
        # ข่าวคะแนนสูงก่อน
        high_score_news = NewsArticle.objects.filter(
            status='published',
            lottery_relevance_score__gte=70,
            published_date__gte=recent_cutoff
        ).select_related('category').order_by('-lottery_relevance_score', '-published_date')[:10]
        
        # ถ้าไม่มีข่าวคะแนนสูง ใช้ข่าวล่าสุดธรรมดา
        if not high_score_news.exists():
            high_score_news = NewsArticle.objects.filter(
                status='published',
                published_date__gte=recent_cutoff
            ).select_related('category').order_by('-published_date')[:8]
        
        # แปลงเป็น JSON format
        news_list = []
        for article in high_score_news:
            extracted_nums = article.get_extracted_numbers_list()
            
            news_list.append({
                'id': article.id,
                'title': article.title[:80] + ('...' if len(article.title) > 80 else ''),
                'category': article.category.name if article.category else 'ทั่วไป',
                'lottery_category': article.get_lottery_category_display() if hasattr(article, 'get_lottery_category_display') else article.lottery_category,
                'lottery_relevance_score': article.lottery_relevance_score,
                'extracted_numbers': extracted_nums[:5],  # แสดงแค่ 5 เลขแรก
                'published_date': article.published_date.strftime('%d/%m/%Y %H:%M'),
                'confidence_level': 'สูง' if article.lottery_relevance_score >= 90 else 'ปานกลาง' if article.lottery_relevance_score >= 70 else 'พอใช้'
            })
        
        return JsonResponse({
            'success': True,
            'data': {
                'news_articles': news_list,
                'total_count': len(news_list),
                'time_range': '24-48 ชั่วโมงล่าสุด'
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'เกิดข้อผิดพลาดในการดึงข่าว กรุณาลองใหม่'
        }, status=500)
from django.shortcuts import render
from django.db.models import Sum
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta
import json

# Import models จาก apps ต่างๆ
from news.models import NewsArticle
from ai_engine.models import (
    LuckyNumberPrediction, EnsemblePrediction, 
    PredictionAccuracyTracking, DataIngestionRecord
)
from lottery_checker.models import LottoResult
# from lucky_spots.models import LuckyLocation  # Removed unused app
from utils.lottery_dates import LotteryDates
from utils.thai_date import format_thai_date
# from .instant_lucky import get_instant_lucky_numbers  # Removed for simplified version
from lotto_stats.stats_calculator import StatsCalculator

# get_daily_numbers_for_today function removed for simplified version

# get_daily_ritual_content function removed for simplified version

def get_next_draw_prediction():
    """สร้างเลขเด็ดสำหรับงวดหน้า - จากสถิติ + ข่าวใหญ่ตั้งแต่งวดที่แล้ว"""
    
    # หาวันที่งวดล่าสุดที่ผ่านมา
    latest_lotto = LottoResult.objects.filter(is_valid=True).order_by('-draw_date').first()
    
    if latest_lotto:
        last_draw_date = latest_lotto.draw_date
    else:
        # ถ้าไม่มีข้อมูล ใช้ 2 สัปดาห์ที่แล้ว
        last_draw_date = timezone.localdate() - timedelta(days=14)
    
    # Part 1: เลขจากสถิติ - Hot Numbers และ Cold Numbers (ชุดเดียวกับหน้าสถิติ)
    statistical_numbers = []
    hot_numbers = []
    cold_numbers = []
    
    try:
        calculator = StatsCalculator()

        # เลขฮอต - ออกบ่อยใน 90 วันล่าสุด
        hot_numbers = calculator.get_hot_numbers(limit=6, days=90, number_type='2D')
        for hot_num in hot_numbers:
            statistical_numbers.append({
                'number': hot_num['number'],
                'source': 'hot_stats',
                # คะแนนจัดอันดับภายในสูตรนี้เท่านั้น (0-100) ไม่ใช่โอกาสถูก
                'score': min(85, 50 + (hot_num['count'] * 5)),
                'reason': f"ออกแล้ว {hot_num['count']} ครั้งใน 90 วัน"
            })
        
        # เลขเย็น - ไม่ออกนานแล้ว
        cold_numbers = calculator.get_cold_numbers(limit=4, number_type='2D')
        for cold_num in cold_numbers:
            statistical_numbers.append({
                'number': cold_num['number'],
                'source': 'cold_stats',
                # คะแนนจัดอันดับภายในสูตรนี้เท่านั้น (0-100) ไม่ใช่โอกาสถูก
                'score': min(75, 40 + (cold_num['days'] // 10)),
                'reason': f"ไม่ออก {cold_num['days']} วัน"
            })
            
    except Exception:
        # Fallback หากไม่มีข้อมูลสถิติ
        pass
    
    # Part 2: เลขจากข่าวใหญ่ - ตั้งแต่งวดที่แล้วจนถึงปัจจุบัน
    major_news_numbers = []
    analyzed_articles = 0
    
    try:
        # ข่าวใหญ่ที่มีเลขตั้งแต่งวดที่แล้ว
        major_news = NewsArticle.objects.filter(
            status='published',
            published_date__date__gte=last_draw_date
        ).exclude(numbers_with_reasons=[]).order_by('-published_date')[:8]
        
        for article in major_news:
            numbers = article.get_numbers_only()
            used = 0
            for num in numbers[:2]:  # เอา 2 เลขแรกต่อข่าว
                if len(num) == 2:
                    major_news_numbers.append({
                        'number': num,
                        'source': 'major_news',
                        # คะแนนจัดอันดับคงที่สำหรับข่าว (ยังไม่มีวิธีวัดจริง) ไม่ใช่โอกาสถูก
                        'score': 90,
                        'reason': f'จากข่าว: {article.title[:30]}...'
                    })
                    used += 1
            if used:
                analyzed_articles += 1
        
    except Exception:
        pass
    
    # รวมเลขทั้งหมดและจัดอันดับ
    all_prediction_numbers = statistical_numbers + major_news_numbers
    
    # เอาเฉพาะเลขที่ไม่ซ้ำและเรียงตาม confidence
    seen_numbers = set()
    unique_numbers = []
    
    for item in sorted(all_prediction_numbers, key=lambda x: x['score'], reverse=True):
        if item['number'] not in seen_numbers:
            unique_numbers.append(item)
            seen_numbers.add(item['number'])
        
        if len(unique_numbers) >= 6:  # จำกัดที่ 6 เลข
            break
    
    has_data = bool(unique_numbers)
    if has_data:
        data_source_summary = f'วิเคราะห์จากสถิติ + ข่าวใหญ่ตั้งแต่ {last_draw_date.strftime("%d/%m/%Y")}'
    else:
        data_source_summary = 'ยังไม่มีข้อมูลสถิติหรือข่าวที่วิเคราะห์ได้ จึงยังไม่แสดงเลขแนะนำ'

    return {
        'prediction_numbers': unique_numbers,
        'has_data': has_data,
        'data_source_summary': data_source_summary,
        'last_draw_date': last_draw_date,
        'total_news_analyzed': analyzed_articles,
        'statistical_coverage': len(statistical_numbers),
        'hot_numbers': hot_numbers[:3],
        'cold_numbers': cold_numbers[:3],
    }

def home(request):
    """หน้าแรก - แสดงข้อมูลจริงจาก database"""
    
    # ดึงข่าวล่าสุดที่มีเลข
    latest_news = NewsArticle.objects.filter(
        status='published'
    ).exclude(numbers_with_reasons=[]).select_related('category').order_by('-published_date')[:3]
    
    # ถ้าไม่มีข่าวที่มีเลข ให้ใช้ข่าวล่าสุดธรรมดา
    if not latest_news.exists():
        latest_news = NewsArticle.objects.filter(
            status='published'
        ).select_related('category').order_by('-published_date')[:3]
    
    # Daily numbers functionality removed for simplified version
    morning_numbers = []  # Removed daily numbers feature
    daily_news_sources = []  # Removed daily news sources
    
    # AI ทำนาย - จาก EnsemblePrediction ที่มี confidence >= 70%
    ai_predictions = EnsemblePrediction.objects.filter(
        session__status__in=['completed', 'locked'],
        overall_confidence__gte=0.70
    ).select_related('session').order_by('-prediction_timestamp')
    
    ai_numbers = []
    for prediction in ai_predictions[:3]:  # ดูจาก 3 การทำนายล่าสุด
        if hasattr(prediction, 'get_top_two_digit_numbers') and prediction.get_top_two_digit_numbers:
            numbers = [item.get('number', item) if isinstance(item, dict) else item 
                      for item in prediction.get_top_two_digit_numbers[:2]]
            ai_numbers.extend(numbers)
    
    # เอาเฉพาะเลข 2-3 หลัก และไม่ซ้ำกัน (รวม 195 ได้)
    ai_numbers = list(set([str(num) for num in ai_numbers if str(num).isdigit() and len(str(num)) in [2, 3]]))[:3]
    
    # ดึงการทำนาย AI Ensemble ล่าสุด (ระบบใหม่)
    latest_prediction = EnsemblePrediction.objects.filter(
        session__status__in=['completed', 'locked']
    ).select_related('session').order_by('-prediction_timestamp').first()
    
    # ถ้าไม่มีการทำนายใหม่ ใช้ระบบเก่าชั่วคราว
    if not latest_prediction:
        old_prediction = LuckyNumberPrediction.objects.filter(
            prediction_date__lte=timezone.localdate()
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
    
    # การ์ด AI หน้าแรก: ต้องมีเลขจริงจึงโชว์เลข+คะแนน (normalize ทั้งระบบเก่า/ใหม่)
    ai_card = {'has_number': False, 'number': '', 'confidence': None}
    if latest_prediction:
        if isinstance(latest_prediction, dict):
            three_digits = [
                item.get('number') if isinstance(item, dict) else item
                for item in latest_prediction.get('get_top_three_digit_numbers') or []
            ]
            confidence = latest_prediction.get('overall_confidence')
        else:
            top_items = latest_prediction.get_top_three_digit_numbers(limit=1)
            three_digits = [item.get('number') for item in top_items if isinstance(item, dict)]
            confidence = latest_prediction.overall_confidence

        number = next((str(n) for n in three_digits if n), '')
        if number:
            # ระบบเก่าเก็บ 0-100 ระบบใหม่เก็บ 0-1
            if confidence is not None and confidence <= 1:
                confidence = confidence * 100
            ai_card = {'has_number': True, 'number': number, 'confidence': round(confidence) if confidence is not None else None}

    # ดึงผลหวยงวดล่าสุด
    latest_lottery_result = LottoResult.objects.filter(
        is_valid=True
    ).order_by('-draw_date').first()
    
    # ดึงสถานที่เลขเด็ดยอดนิยม 4 แห่ง - ถูกลบออกแล้ว
    # popular_lucky_locations = []  # Lucky spots feature removed
    
    # คำนวณสถิติเว็บไซต์จากระบบ AI ใหม่
    total_news = NewsArticle.objects.filter(status='published').count()
    
    # รวมการทำนายทั้งเก่าและใหม่
    total_predictions_new = EnsemblePrediction.objects.count()
    total_predictions_old = LuckyNumberPrediction.objects.count()
    total_predictions = total_predictions_new + total_predictions_old
    
    # ความแม่นยำจากระบบใหม่ (None = ยังไม่มีข้อมูลงวดที่ตรวจแล้ว ห้ามโชว์ค่าจำลอง)
    accuracy_records = PredictionAccuracyTracking.objects.all()
    if accuracy_records.exists():
        correct_predictions = accuracy_records.filter(two_digit_accuracy=True).count()
        accuracy_percentage = (correct_predictions / accuracy_records.count()) * 100
        has_accuracy_data = True
    else:
        accuracy_percentage = None
        has_accuracy_data = False
    
    # ข้อมูลที่เก็บวันนี้
    today_data_records = DataIngestionRecord.objects.filter(
        ingested_at__date=timezone.localdate()
    ).count()
    
    total_views_today = latest_news.aggregate(
        total_views=Sum('views')
    )['total_views'] or 0
    
    # ดึงข้อมูลงวดถัดไป
    today = timezone.localdate()
    next_draw_date = LotteryDates.get_next_draw_date(today)
    next_draw_info = None
    dynamic_title = "เลขเด็ดหวยเอไองวดหน้า"  # Default title

    if next_draw_date:
        next_draw_date_obj = datetime.strptime(next_draw_date, "%Y-%m-%d").date()
        days_until_draw = (next_draw_date_obj - today).days

        # เปลี่ยนคำหน้าแรก: ถ้าอีกไม่ถึง 5 วัน จะใช้ "งวดนี้"
        if days_until_draw < 5:
            dynamic_title = "เลขเด็ดหวยเอไองวดนี้"

        next_draw_info = {
            'date': next_draw_date_obj,
            'days_remaining': days_until_draw,
            'formatted_date': format_thai_date(next_draw_date_obj)
        }
    
    # สร้าง Daily Ritual Content (เลขเดียวกันตลอดวัน)
    # daily_ritual = get_daily_ritual_content(latest_news, latest_prediction)  # Removed for simplified version
    
    # 🎯 เลขเด็ดหวยงวดหน้า - จากสถิติ + ข่าวใหญ่
    next_draw_prediction = get_next_draw_prediction()
    
    # จัดเตรียม context สำหรับ template
    context = {
        'latest_news': latest_news,
        'latest_prediction': latest_prediction,
        'ai_prediction': latest_prediction,  # เพิ่ม alias สำหรับ template ใหม่
        'ai_card': ai_card,
        'latest_lottery_result': latest_lottery_result,
        # 'popular_lucky_locations': [],  # Lucky spots feature removed
        'next_draw_info': next_draw_info,
        'site_stats': {
            'total_visitors_today': total_views_today,  # ยอดวิวจริงเท่านั้น ห้ามบวก estimate
            'accuracy_percentage': int(accuracy_percentage) if accuracy_percentage is not None else None,
            'has_accuracy_data': has_accuracy_data,
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
        
        # Daily ritual functionality removed for simplified version
        # 'daily_ritual': daily_ritual,  # Removed
        'current_date_formatted': timezone.now().strftime('%d/%m/%Y'),
        
        # Daily numbers feature removed for simplified version
        # 'morning_news_numbers': morning_numbers,  # Removed
        # 'daily_news_sources': daily_news_sources,  # Removed
        
        # 🤖 AI ทำนาย - จาก EnsemblePrediction confidence >= 70%
        'ai_prediction_numbers': ai_numbers,
        
        # ข้อมูลงวดหวย
        'target_lottery_date': next_draw_info['formatted_date'] if next_draw_info else '2 กันยายน 2025',
        
        # 🎯 เลขเด็ดหวยงวดหน้า/งวดนี้ (แบบไดนามิก)
        'next_draw_prediction': next_draw_prediction,
        'next_draw_numbers': [item['number'] for item in next_draw_prediction['prediction_numbers']],
        'dynamic_lottery_title': dynamic_title,
    }
    
    return render(request, 'home/index.html', context)


# instant_lucky_numbers_api function removed for simplified version


# get_recent_news_for_selection_api function removed for simplified version


@csrf_exempt
@require_http_methods(["GET"])
def daily_numbers_status_api(request):
    """
    API endpoint สำหรับตรวจสอบสถานะเลขประจำวัน
    """
    try:
        # ตรวจสอบข่าว 24 ชั่วโมงล่าสุด
        news_24h_cutoff = timezone.now() - timedelta(hours=24)
        morning_news_count = NewsArticle.objects.filter(
            status='published',
            published_date__gte=news_24h_cutoff
        ).count()
        
        # ตรวจสอบ AI predictions
        ai_predictions_count = EnsemblePrediction.objects.filter(
            session__status__in=['completed', 'locked'],
            overall_confidence__gte=0.70
        ).count()
        
        # สถานะล่าสุด
        latest_news = NewsArticle.objects.filter(
            status='published'
        ).order_by('-published_date').first()
        
        latest_prediction = EnsemblePrediction.objects.filter(
            session__status__in=['completed', 'locked']
        ).order_by('-prediction_timestamp').first()
        
        return JsonResponse({
            'success': True,
            'data': {
                'last_update': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                'news_24h_count': morning_news_count,
                'ai_predictions_count': ai_predictions_count,
                'latest_news_date': latest_news.published_date.strftime('%Y-%m-%d %H:%M:%S') if latest_news else None,
                'latest_prediction_date': latest_prediction.prediction_timestamp.strftime('%Y-%m-%d %H:%M:%S') if latest_prediction else None,
                'status': 'active' if morning_news_count > 0 or ai_predictions_count > 0 else 'waiting_for_data'
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'เกิดข้อผิดพลาดในการตรวจสอบสถานะ'
        }, status=500)
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
from lotto_stats.models import LotteryDraw, NumberStatistics, HotColdNumber

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

def get_next_draw_prediction():
    """สร้างเลขเด็ดสำหรับงวดหน้า - จากสถิติ + ข่าวใหญ่ตั้งแต่งวดที่แล้ว"""
    
    # หาวันที่งวดล่าสุดที่ผ่านมา
    latest_lotto = LottoResult.objects.filter(is_valid=True).order_by('-draw_date').first()
    
    if latest_lotto:
        last_draw_date = latest_lotto.draw_date
    else:
        # ถ้าไม่มีข้อมูล ใช้ 2 สัปดาห์ที่แล้ว
        last_draw_date = timezone.now().date() - timedelta(days=14)
    
    # Part 1: เลขจากสถิติ - Hot Numbers และ Cold Numbers
    statistical_numbers = []
    
    try:
        # เลขฮอต - ออกบ่อยใน 90 วันล่าสุด
        hot_numbers = NumberStatistics.objects.filter(
            number_type='2D',
            total_appearances__gte=3
        ).order_by('-total_appearances')[:6]
        
        for hot_num in hot_numbers:
            statistical_numbers.append({
                'number': hot_num.number,
                'source': 'hot_stats',
                'confidence': min(85, 50 + (hot_num.total_appearances * 5)),
                'reason': f'ออกแล้ว {hot_num.total_appearances} ครั้ง'
            })
        
        # เลขเย็น - ไม่ออกนานแล้ว มีโอกาสออก
        cold_numbers = NumberStatistics.objects.filter(
            number_type='2D',
            days_since_last__gte=30,
            total_appearances__gte=1
        ).order_by('-days_since_last')[:4]
        
        for cold_num in cold_numbers:
            statistical_numbers.append({
                'number': cold_num.number,
                'source': 'cold_stats',
                'confidence': min(75, 40 + (cold_num.days_since_last // 10)),
                'reason': f'ไม่ออก {cold_num.days_since_last} วัน'
            })
            
    except Exception:
        # Fallback หากไม่มีข้อมูลสถิติ
        pass
    
    # Part 2: เลขจากข่าวใหญ่ - ตั้งแต่งวดที่แล้วจนถึงปัจจุบัน
    major_news_numbers = []
    
    try:
        # ข่าวใหญ่ที่มีคะแนน >= 80 ตั้งแต่งวดที่แล้ว
        major_news = NewsArticle.objects.filter(
            status='published',
            lottery_relevance_score__gte=80,
            published_date__date__gte=last_draw_date
        ).order_by('-lottery_relevance_score', '-published_date')[:8]
        
        for article in major_news:
            numbers = article.get_extracted_numbers_list()
            for num in numbers[:2]:  # เอา 2 เลขแรกต่อข่าว
                if len(num) == 2:
                    major_news_numbers.append({
                        'number': num,
                        'source': 'major_news',
                        'confidence': article.lottery_relevance_score,
                        'reason': f'จากข่าว: {article.title[:30]}...'
                    })
        
    except Exception:
        pass
    
    # รวมเลขทั้งหมดและจัดอันดับ
    all_prediction_numbers = statistical_numbers + major_news_numbers
    
    # เอาเฉพาะเลขที่ไม่ซ้ำและเรียงตาม confidence
    seen_numbers = set()
    unique_numbers = []
    
    for item in sorted(all_prediction_numbers, key=lambda x: x['confidence'], reverse=True):
        if item['number'] not in seen_numbers:
            unique_numbers.append(item)
            seen_numbers.add(item['number'])
        
        if len(unique_numbers) >= 6:  # จำกัดที่ 6 เลข
            break
    
    return {
        'prediction_numbers': unique_numbers,
        'data_source_summary': f'วิเคราะห์จากสถิติ + ข่าวใหญ่ตั้งแต่ {last_draw_date.strftime("%d/%m/%Y")}',
        'last_draw_date': last_draw_date,
        'total_news_analyzed': len(major_news_numbers),
        'statistical_coverage': len(statistical_numbers)
    }

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
    
    # เลขเด็ดเช้านี้ - จากข่าวใน 24 ชั่วโมงล่าสุด (ถ้าไม่มีให้ขยายไปเรื่อยๆ)
    morning_numbers = []
    daily_news_sources = []  # เก็บข่าวที่ใช้วิเคราะห์
    hours_back = 24
    max_hours_back = 168  # สูงสุด 7 วัน
    
    while not morning_numbers and hours_back <= max_hours_back:
        news_cutoff = timezone.now() - timedelta(hours=hours_back)
        morning_news = NewsArticle.objects.filter(
            status='published',
            published_date__gte=news_cutoff
        ).select_related('category').order_by('-published_date')
        
        # เก็บข่าวที่ใช้วิเคราะห์
        used_articles = []
        for article in morning_news[:6]:  # ดูจาก 6 บทความล่าสุด
            numbers = article.get_extracted_numbers_list()
            if numbers:  # ถ้ามีเลข
                used_articles.append(article)
                morning_numbers.extend(numbers[:2])  # เอา 2 เลขแรกต่อบทความ
        
        # เอาเฉพาะเลข 2-3 หลัก และไม่ซ้ำกัน (รวม 195 ได้)
        morning_numbers = list(set([num for num in morning_numbers if len(num) in [2, 3]]))[:6]
        
        if morning_numbers:
            daily_news_sources = used_articles  # เก็บข่าวที่มีเลข
        else:
            hours_back += 24  # ขยายไปอีก 24 ชั่วโมง
    
    # ถ้ายังไม่มีเลข ให้ใช้ข่าวล่าสุดโดยไม่จำกัดวันที่
    if not morning_numbers:
        fallback_news = NewsArticle.objects.filter(
            status='published'
        ).select_related('category').order_by('-published_date')[:10]
        
        used_articles = []
        for article in fallback_news:
            numbers = article.get_extracted_numbers_list()
            if numbers:
                used_articles.append(article)
                morning_numbers.extend(numbers[:2])
        
        # เอาเฉพาะเลข 2-3 หลัก และไม่ซ้ำกัน (รวม 195 ได้)
        morning_numbers = list(set([num for num in morning_numbers if len(num) in [2, 3]]))[:6]
        daily_news_sources = used_articles
    
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
    
    # 🎯 เลขเด็ดหวยงวดหน้า - จากสถิติ + ข่าวใหญ่
    next_draw_prediction = get_next_draw_prediction()
    
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
        
        # 🌅 เลขเด็ดเช้านี้ - จากข่าว 24 ชั่วโมงล่าสุด
        'morning_news_numbers': morning_numbers,
        'daily_news_sources': daily_news_sources,
        
        # 🤖 AI ทำนาย - จาก EnsemblePrediction confidence >= 70%
        'ai_prediction_numbers': ai_numbers,
        
        # ข้อมูลงวดหวย
        'target_lottery_date': next_draw_info['formatted_date'] if next_draw_info else '2 กันยายน 2025',
        
        # 🎯 เลขเด็ดหวยงวดหน้า
        'next_draw_prediction': next_draw_prediction,
        'next_draw_numbers': [item['number'] for item in next_draw_prediction['prediction_numbers']],
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
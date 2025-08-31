
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Count, Q
from datetime import datetime, timedelta
import json

from .models import (
    AIModel, LuckyNumberPrediction, UserFeedback,
    PredictionFactor, EnsemblePrediction, PredictionSession, 
    ModelPrediction, DataSource, DataIngestionRecord
)
from .ml_engine import LotteryAIEngine

def ai_prediction_page(request):
    """หน้าแสดงการทำนายเลขด้วย AI"""
    # ดึงการทำนายล่าสุด
    today = timezone.now().date()
    
    # ตรวจสอบว่ามีการทำนายวันนี้แล้วหรือไม่
    today_prediction = LuckyNumberPrediction.objects.filter(
        prediction_date=today
    ).first()
    
    if not today_prediction:
        # สร้างการทำนายใหม่
        today_prediction = generate_new_prediction()
    
    # เพิ่มยอดวิว
    today_prediction.views += 1
    today_prediction.save(update_fields=['views'])
    
    # ดึงการทำนายย้อนหลัง
    past_predictions = LuckyNumberPrediction.objects.exclude(
        id=today_prediction.id
    ).order_by('-prediction_date')[:5]
    
    # ดึง feedback
    feedbacks = UserFeedback.objects.filter(
        old_prediction=today_prediction
    ).order_by('-created_at')[:10]
    
    # คำนวณ rating เฉลี่ย
    avg_rating = 0
    if feedbacks:
        total_rating = sum(f.rating for f in feedbacks)
        avg_rating = total_rating / len(feedbacks)
    
    # Get the factors used for the prediction
    factors_used_codes = today_prediction.factors_used.keys()
    factors = PredictionFactor.objects.filter(code__in=factors_used_codes, is_active=True)

    context = {
        'prediction': today_prediction,
        'past_predictions': past_predictions,
        'feedbacks': feedbacks,
        'avg_rating': avg_rating,
        'factors': factors,
    }
    
    return render(request, 'ai_engine/prediction.html', context)

def generate_new_prediction(target_date=None):
    """สร้างการทำนายใหม่"""
    if target_date is None:
        target_date = timezone.now().date()
    
    # เลือกโมเดลที่ active
    ai_model = AIModel.objects.filter(is_active=True).first()
    if not ai_model:
        # สร้างโมเดล default ถ้ายังไม่มี
        ai_model = AIModel.objects.create(
            name="Pattern Analyzer",
            version="1.0",
            algorithm="pattern_analysis",
            accuracy=75.5
        )
    
    # สร้าง engine และทำนาย
    engine = LotteryAIEngine(model_type=ai_model.algorithm)
    result = engine.predict(target_date)
    
    # บันทึกผลการทำนาย
    prediction = LuckyNumberPrediction.objects.create(
        prediction_date=target_date,
        for_draw_date=target_date + timedelta(days=1),
        ai_model=ai_model,
        two_digit_numbers=', '.join(result['two_digit']),
        three_digit_numbers=', '.join(result['three_digit']),
        overall_confidence=result['confidence'],
        prediction_details={
            'reasoning': result['reasoning'],
            'algorithm': ai_model.algorithm,
            'version': ai_model.version
        },
        factors_used=result['factors']
    )
    
    return prediction

def api_predict(request):
    """API สำหรับขอการทำนายใหม่"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            target_date = data.get('date')
            
            if target_date:
                target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
            else:
                target_date = timezone.now().date()
            
            # ตรวจสอบว่ามีการทำนายวันนี้แล้วหรือไม่
            existing = LuckyNumberPrediction.objects.filter(
                prediction_date=target_date
            ).first()
            
            if existing:
                prediction = existing
            else:
                prediction = generate_new_prediction(target_date)
            
            return JsonResponse({
                'success': True,
                'prediction': {
                    'date': prediction.prediction_date.strftime('%Y-%m-%d'),
                    'two_digit': prediction.get_two_digit_list(),
                    'three_digit': prediction.get_three_digit_list(),
                    'confidence': prediction.overall_confidence,
                    'details': prediction.prediction_details
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

def prediction_detail(request, prediction_id):
    """รายละเอียดการทำนาย"""
    prediction = get_object_or_404(LuckyNumberPrediction, id=prediction_id)
    
    # เพิ่มยอดวิว
    prediction.views += 1
    prediction.save(update_fields=['views'])
    
    # ดึง feedbacks
    feedbacks = prediction.feedbacks.all().order_by('-created_at')
    
    context = {
        'prediction': prediction,
        'feedbacks': feedbacks,
        'two_digits': prediction.get_two_digit_list(),
        'three_digits': prediction.get_three_digit_list(),
    }
    
    return render(request, 'ai_engine/prediction_detail.html', context)

@require_http_methods(["POST"])
def add_feedback(request, prediction_id):
    """เพิ่ม feedback"""
    prediction = get_object_or_404(LuckyNumberPrediction, id=prediction_id)
    
    try:
        data = json.loads(request.body)
        
        feedback = UserFeedback.objects.create(
            prediction=prediction,
            user=request.user if request.user.is_authenticated else None,
            rating=int(data.get('rating', 3)),
            comment=data.get('comment', ''),
            is_winner=data.get('is_winner', False)
        )
        
        return JsonResponse({
            'success': True,
            'feedback_id': feedback.id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

def ai_history(request):
    """ประวัติการทำนายทั้งหมด"""
    predictions = LuckyNumberPrediction.objects.all().order_by('-prediction_date')
    
    # Filter by date range
    date_from = request.GET.get('from')
    date_to = request.GET.get('to')
    
    if date_from:
        predictions = predictions.filter(prediction_date__gte=date_from)
    if date_to:
        predictions = predictions.filter(prediction_date__lte=date_to)
    
    # Pagination
    paginator = Paginator(predictions, 20)
    page = request.GET.get('page')
    predictions = paginator.get_page(page)
    
    context = {
        'predictions': predictions,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'ai_engine/history.html', context)

def ai_accuracy(request):
    """หน้าแสดงความแม่นยำของ AI"""
    # ดึงสถิติความแม่นยำ
    from .models import PredictionAccuracy
    
    accuracy_records = PredictionAccuracy.objects.all().order_by('-checked_date')[:30]
    
    # คำนวณสถิติ
    total_predictions = len(accuracy_records)
    correct_first = sum(1 for r in accuracy_records if r.is_correct_first)
    correct_two = sum(1 for r in accuracy_records if r.is_correct_two_digit)
    correct_three = sum(1 for r in accuracy_records if r.is_correct_three_digit)
    
    accuracy_stats = {
        'total': total_predictions,
        'first_prize': {
            'correct': correct_first,
            'percentage': (correct_first / total_predictions * 100) if total_predictions > 0 else 0
        },
        'two_digit': {
            'correct': correct_two,
            'percentage': (correct_two / total_predictions * 100) if total_predictions > 0 else 0
        },
        'three_digit': {
            'correct': correct_three,
            'percentage': (correct_three / total_predictions * 100) if total_predictions > 0 else 0
        }
    }
    
    # ดึงโมเดลทั้งหมด
    models = AIModel.objects.all().order_by('-accuracy')
    
    context = {
        'accuracy_stats': accuracy_stats,
        'accuracy_records': accuracy_records,
        'models': models,
    }
    
    return render(request, 'ai_engine/accuracy.html', context)

def system_dashboard(request):
    """แดชบอร์ดระบบ AI"""
    
    # ข้อมูลรวม
    dashboard_stats = {
        'predictions': {
            'total': EnsemblePrediction.objects.count(),
            'today': EnsemblePrediction.objects.filter(
                prediction_timestamp__date=timezone.now().date()
            ).count(),
            'this_month': EnsemblePrediction.objects.filter(
                prediction_timestamp__month=timezone.now().month
            ).count()
        },
        'sessions': {
            'completed': PredictionSession.objects.filter(status='completed').count(),
            'failed': PredictionSession.objects.filter(status='failed').count(),
            'locked': PredictionSession.objects.filter(status='locked').count(),
        },
        'data': {
            'total_records': DataIngestionRecord.objects.count(),
            'today_records': DataIngestionRecord.objects.filter(
                ingested_at__date=timezone.now().date()
            ).count(),
            'processing_pending': DataIngestionRecord.objects.filter(
                processing_status='pending'
            ).count()
        }
    }
    
    # การทำนายล่าสุด
    recent_predictions = EnsemblePrediction.objects.select_related(
        'session'
    ).order_by('-prediction_timestamp')[:5]
    
    # ข้อมูลที่เก็บล่าสุด
    recent_data = DataIngestionRecord.objects.select_related(
        'data_source'
    ).order_by('-ingested_at')[:10]
    
    context = {
        'dashboard_stats': dashboard_stats,
        'recent_predictions': recent_predictions,
        'recent_data': recent_data,
    }
    
    return render(request, 'ai_engine/dashboard.html', context)

# New AI Ensemble Views

def ensemble_prediction_detail(request, prediction_id):
    """รายละเอียดการทำนาย AI Ensemble"""
    prediction = get_object_or_404(EnsemblePrediction, id=prediction_id)
    
    # ดึงการทำนายของแต่ละโมเดล
    individual_predictions = ModelPrediction.objects.filter(
        session=prediction.session
    ).select_related('model_type').order_by('model_type__name')
    
    # ดึงแหล่งข้อมูลที่ใช้
    data_sources_used = DataIngestionRecord.objects.filter(
        ingested_at__range=[
            prediction.session.data_collection_period_start,
            prediction.session.data_collection_period_end
        ],
        processing_status='completed'
    ).select_related('data_source')[:20]
    
    context = {
        'prediction': prediction,
        'individual_predictions': individual_predictions,
        'data_sources_used': data_sources_used,
    }
    
    return render(request, 'ai_engine/ensemble_prediction_detail.html', context)

def ensemble_history(request):
    """ประวัติการทำนาย AI Ensemble"""
    predictions = EnsemblePrediction.objects.select_related(
        'session'
    ).order_by('-prediction_timestamp')
    
    # Filter by date range
    date_from = request.GET.get('from')
    date_to = request.GET.get('to')
    
    if date_from:
        predictions = predictions.filter(
            session__for_draw_date__gte=date_from
        )
    if date_to:
        predictions = predictions.filter(
            session__for_draw_date__lte=date_to
        )
    
    # Pagination
    paginator = Paginator(predictions, 20)
    page = request.GET.get('page')
    predictions = paginator.get_page(page)
    
    context = {
        'predictions': predictions,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'ai_engine/ensemble_history.html', context)

def data_sources(request):
    """หน้าแสดงแหล่งข้อมูลทั้งหมด"""
    sources = DataSource.objects.all().order_by('source_type', 'name')
    
    # Filter by source type
    source_type_filter = request.GET.get('source_type')
    if source_type_filter:
        sources = sources.filter(source_type=source_type_filter)
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter == 'active':
        sources = sources.filter(is_active=True)
    elif status_filter == 'inactive':
        sources = sources.filter(is_active=False)
    
    # Calculate statistics
    today = timezone.now().date()
    stats = {
        'total_sources': DataSource.objects.count(),
        'active_sources': DataSource.objects.filter(is_active=True).count(),
        'total_records_today': DataIngestionRecord.objects.filter(
            ingested_at__date=today
        ).count(),
        'processing_records': DataIngestionRecord.objects.filter(
            processing_status='pending'
        ).count(),
    }
    
    # Add methods to calculate recent data for each source
    for source in sources:
        source.get_total_records = lambda s=source: DataIngestionRecord.objects.filter(data_source=s).count()
        source.get_today_records = lambda s=source: DataIngestionRecord.objects.filter(
            data_source=s, ingested_at__date=today
        ).count()
        source.get_recent_data = lambda s=source: DataIngestionRecord.objects.filter(
            data_source=s
        ).order_by('-ingested_at')[:5]
    
    # Pagination
    paginator = Paginator(sources, 10)
    page = request.GET.get('page')
    sources = paginator.get_page(page)
    
    context = {
        'data_sources': sources,
        'stats': stats,
        'source_type_filter': source_type_filter,
        'status_filter': status_filter,
    }
    
    return render(request, 'ai_engine/data_sources.html', context)

def data_source_detail(request, source_id):
    """รายละเอียดแหล่งข้อมูล"""
    data_source = get_object_or_404(DataSource, id=source_id)
    
    # Time range filter
    time_range = request.GET.get('time_range', 'week')
    today = timezone.now().date()
    
    if time_range == 'today':
        start_date = today
    elif time_range == 'week':
        start_date = today - timedelta(days=7)
    elif time_range == 'month':
        start_date = today - timedelta(days=30)
    else:
        start_date = None
    
    # Get recent data
    recent_data = DataIngestionRecord.objects.filter(
        data_source=data_source
    )
    
    if start_date:
        recent_data = recent_data.filter(ingested_at__date__gte=start_date)
    
    recent_data = recent_data.order_by('-ingested_at')
    
    # Statistics
    today_records = DataIngestionRecord.objects.filter(
        data_source=data_source,
        ingested_at__date=today
    ).count()
    
    week_records = DataIngestionRecord.objects.filter(
        data_source=data_source,
        ingested_at__date__gte=today - timedelta(days=7)
    ).count()
    
    total_numbers = sum([
        len(r.extracted_numbers or []) for r in 
        DataIngestionRecord.objects.filter(data_source=data_source)
    ])
    
    stats = {
        'total_records': DataIngestionRecord.objects.filter(data_source=data_source).count(),
        'today_records': today_records,
        'this_week_records': week_records,
        'numbers_extracted': total_numbers,
    }
    
    # Predictions using this source
    predictions_using_source = EnsemblePrediction.objects.filter(
        session__data_collection_period_start__lte=timezone.now().date(),
        session__data_collection_period_end__gte=timezone.now().date() - timedelta(days=90)
    ).select_related('session')[:10]
    
    # Pagination for recent data
    paginator = Paginator(recent_data, 20)
    page = request.GET.get('page')
    recent_data = paginator.get_page(page)
    
    context = {
        'data_source': data_source,
        'recent_data': recent_data,
        'stats': stats,
        'time_range': time_range,
        'predictions_using_source': predictions_using_source,
    }
    
    return render(request, 'ai_engine/data_source_detail.html', context)

@require_http_methods(["POST"])
def api_refresh_data_sources(request):
    """API สำหรับรีเฟรชแหล่งข้อมูล"""
    try:
        # Trigger data collection for all active sources
        from .data_ingestion import DataIngestionManager
        manager = DataIngestionManager()
        
        results = []
        active_sources = DataSource.objects.filter(is_active=True)
        
        for source in active_sources:
            try:
                records = manager.collect_from_source(source)
                results.append({
                    'source': source.name,
                    'records_collected': len(records)
                })
            except Exception as e:
                results.append({
                    'source': source.name,
                    'error': str(e)
                })
        
        return JsonResponse({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@require_http_methods(["POST"])
def api_trigger_data_collection(request, source_id):
    """API สำหรับเก็บข้อมูลจากแหล่งเฉพาะ"""
    try:
        data_source = get_object_or_404(DataSource, id=source_id)
        
        if not data_source.is_active:
            return JsonResponse({
                'success': False,
                'error': 'แหล่งข้อมูลนี้ไม่ได้เปิดใช้งาน'
            }, status=400)
        
        from .data_ingestion import DataIngestionManager
        manager = DataIngestionManager()
        
        records = manager.collect_from_source(data_source)
        
        return JsonResponse({
            'success': True,
            'records_collected': len(records),
            'message': f'เก็บข้อมูลจาก {data_source.name} แล้ว {len(records)} รายการ'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

# Backward compatibility สำหรับ API เก่า
def api_generate_prediction(request):
    """API สำหรับสร้างการทำนายใหม่"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            target_date = data.get('date')
            
            if target_date:
                target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
            else:
                target_date = timezone.now().date()
            
            # ตรวจสอบว่ามีการทำนาย AI Ensemble แล้วหรือไม่
            from .prediction_engine import PredictionEngine
            engine = PredictionEngine()
            
            session = engine.create_prediction_session(target_date)
            prediction = engine.run_prediction(session)
            
            return JsonResponse({
                'success': True,
                'prediction': {
                    'session_id': session.session_id,
                    'date': target_date.strftime('%Y-%m-%d'),
                    'two_digit': [item['number'] for item in prediction.get_top_two_digit_numbers()[:5]],
                    'three_digit': [item['number'] for item in prediction.get_top_three_digit_numbers()[:5]],
                    'confidence': prediction.overall_confidence,
                    'summary': prediction.prediction_summary
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)
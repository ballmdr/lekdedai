
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import (
    AIModel, LuckyNumberPrediction, UserFeedback,
    PredictionFactor
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
        prediction=today_prediction
    ).order_by('-created_at')[:10]
    
    # คำนวณ rating เฉลี่ย
    avg_rating = 0
    if feedbacks:
        total_rating = sum(f.rating for f in feedbacks)
        avg_rating = total_rating / len(feedbacks)
    
    context = {
        'prediction': today_prediction,
        'past_predictions': past_predictions,
        'feedbacks': feedbacks,
        'avg_rating': avg_rating,
        'factors': PredictionFactor.objects.filter(is_active=True),
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
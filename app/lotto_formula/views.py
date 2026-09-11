import json
from datetime import datetime

from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, DetailView

from .models import LotteryFormula, LotteryResult, Prediction
from .verification import get_verified_stats
from utils.lottery_dates import LotteryDates
from utils.thai_date import format_thai_date

class HomeView(ListView):
    model = LotteryFormula
    template_name = 'lotto_formula/home.html'
    context_object_name = 'formulas'

    def get_queryset(self):
        return LotteryFormula.objects.filter(is_approved=True).order_by('code')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['latest_results'] = LotteryResult.objects.all()[:5]
        context['page_title'] = 'เว็บสูตรคำนวณหวย - ทำนายเลขเด็ดแม่นยำ'
        context['meta_description'] = 'เว็บสูตรคำนวณหวยไทย มีสูตรหลากหลาย ทำนายเลขเด็ดแม่นยำ ดูผลย้อนหลัง และสถิติความแม่นยำ'
        return context

class FormulaDetailView(DetailView):
    model = LotteryFormula
    template_name = 'lotto_formula/formula_detail.html'
    context_object_name = 'formula'

    def get_queryset(self):
        return LotteryFormula.objects.filter(is_approved=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        formula = self.get_object()
        context['predictions'] = Prediction.objects.filter(formula=formula).order_by('-draw_date')[:10]
        context['verified_stats'] = get_verified_stats(formula)
        context['page_title'] = f'{formula.name} - สูตรคำนวณหวย'
        context['meta_description'] = f'{formula.description[:150]}...'
        return context

def calculator_view(request):
    formulas = LotteryFormula.objects.filter(is_approved=True).order_by('code')
    upcoming_draws = [
        {"value": d, "label": format_thai_date(datetime.strptime(d, "%Y-%m-%d").date())}
        for d in LotteryDates.get_upcoming_draw_dates(4)
    ]
    return render(request, 'lotto_formula/calculator.html', {
        'formulas': formulas,
        'upcoming_draws': upcoming_draws,
        'page_title': 'เครื่องคำนวณหวย - คำนวณเลขเด็ด',
        'meta_description': 'เครื่องคำนวณหวยออนไลน์ เลือกสูตรและคำนวณเลขเด็ดได้ทันที'
    })

@require_http_methods(["POST"])
def calculate_numbers(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'ข้อมูลที่ส่งมาไม่ถูกต้อง'}, status=400)

    formula_id = data.get('formula_id')
    input_numbers = str(data.get('input_numbers') or '').strip()

    if not formula_id or not input_numbers:
        return JsonResponse({'success': False, 'error': 'กรุณาเลือกสูตรและกรอกเลขอ้างอิง'}, status=400)

    formula = LotteryFormula.objects.filter(id=formula_id, is_approved=True).first()
    if not formula:
        return JsonResponse({'success': False, 'error': 'ไม่พบสูตรที่เลือก'}, status=404)

    calculated_numbers = calculate_by_formula(formula, input_numbers)
    if not calculated_numbers:
        return JsonResponse({'success': False, 'error': 'เลขอ้างอิงต้องมีตัวเลขอย่างน้อย 2 ตัว'}, status=400)

    return JsonResponse({
        'success': True,
        'calculated_numbers': calculated_numbers,
        'formula_name': formula.name,
        'formula_version': formula.version
    })

@require_http_methods(["POST"])
def save_prediction(request):
    """บันทึกการทำนายสำหรับงวดที่ยังไม่ออก (Task 15).

    บังคับ: สูตรที่อนุมัติ + งวดหวยจริงในอนาคต + เลขตรงกับที่สูตรคำนวณได้
    (เซิร์ฟเวอร์คำนวณซ้ำ กันส่งเลขปลอม). สถานะเริ่มที่รอตรวจ (is_correct=None).
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'ข้อมูลที่ส่งมาไม่ถูกต้อง'}, status=400)

    formula_id = data.get('formula_id')
    input_numbers = str(data.get('input_numbers') or '').strip()
    draw_date_str = str(data.get('draw_date') or '').strip()

    formula = LotteryFormula.objects.filter(id=formula_id, is_approved=True).first()
    if not formula:
        return JsonResponse({'success': False, 'error': 'ไม่พบสูตรที่เลือก'}, status=404)

    try:
        draw_date = datetime.strptime(draw_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'รูปแบบงวดไม่ถูกต้อง'}, status=400)

    if not LotteryDates.is_draw_date(draw_date):
        return JsonResponse({'success': False, 'error': 'วันที่เลือกไม่ใช่วันหวยออก (1 หรือ 16)'}, status=400)

    if draw_date <= timezone.localdate():
        return JsonResponse({'success': False, 'error': 'งวดนี้ออกผลแล้ว — บันทึกได้เฉพาะงวดที่ยังไม่ออก'}, status=400)

    calculated_numbers = calculate_by_formula(formula, input_numbers)
    if not calculated_numbers:
        return JsonResponse({'success': False, 'error': 'เลขอ้างอิงต้องมีตัวเลขอย่างน้อย 2 ตัว'}, status=400)

    predicted = ','.join(calculated_numbers)
    prediction, created = Prediction.objects.get_or_create(
        formula=formula,
        draw_date=draw_date,
        input_numbers=input_numbers,
        predicted_numbers=predicted,
    )
    return JsonResponse({
        'success': True,
        'created': created,
        'prediction_id': prediction.id,
        'formula_name': formula.name,
        'draw_date': draw_date_str,
        'predicted_numbers': calculated_numbers,
        'status': 'pending',
        'message': 'บันทึกแล้ว — รอตรวจกับผลจริงหลังวันหวยออก',
    })

@require_http_methods(["GET"])
def api_stats(request):
    """API endpoint สำหรับสถิติการทำนาย — นับเฉพาะแถวที่ตรวจผลแล้ว (Task 15)."""
    verified = Prediction.objects.filter(is_correct__isnull=False)
    verified_count = verified.count()
    correct_predictions = verified.filter(is_correct=True).count()
    accuracy_rate = (correct_predictions / verified_count * 100) if verified_count > 0 else 0

    # สถิติแต่ละสูตร (เฉพาะที่อนุมัติ)
    formula_stats = []
    for formula in LotteryFormula.objects.filter(is_approved=True).order_by('code'):
        formula_verified = Prediction.objects.filter(formula=formula, is_correct__isnull=False)
        formula_correct = formula_verified.filter(is_correct=True).count()
        formula_total = formula_verified.count()
        formula_accuracy = (formula_correct / formula_total * 100) if formula_total > 0 else 0

        formula_stats.append({
            'name': formula.name,
            'total': formula_total,
            'verified': formula_total,
            'correct': formula_correct,
            'accuracy': round(formula_accuracy, 1)
        })

    return JsonResponse({
        'total_predictions': Prediction.objects.count(),
        'verified_predictions': verified_count,
        'correct_predictions': correct_predictions,
        'accuracy_rate': round(accuracy_rate, 1),
        'formula_stats': formula_stats
    })

@require_http_methods(["GET"])
def api_formula_detail(request, formula_id):
    """API endpoint สำหรับรายละเอียดสูตร"""
    try:
        formula = LotteryFormula.objects.get(id=formula_id)
        predictions = Prediction.objects.filter(formula=formula).order_by('-created_at')[:10]
        
        predictions_data = [{
            'predicted_numbers': p.predicted_numbers,
            'input_numbers': p.input_numbers,
            'draw_date': p.draw_date.strftime('%Y-%m-%d'),
            'is_correct': p.is_correct
        } for p in predictions]

        stats = get_verified_stats(formula)

        return JsonResponse({
            'formula': {
                'id': formula.id,
                'name': formula.name,
                'description': formula.description,
                'method': formula.method,
                'accuracy_rate': formula.accuracy_rate,
                'verified_predictions': stats['verified'],
                'verified_correct': stats['correct'],
                'verified_from': stats['date_from'].strftime('%Y-%m-%d') if stats['date_from'] else None,
                'verified_to': stats['date_to'].strftime('%Y-%m-%d') if stats['date_to'] else None,
                'verification_rule': stats['rule'],
                'total_predictions': formula.total_predictions,
                'correct_predictions': formula.correct_predictions
            },
            'predictions': predictions_data
        })
    except LotteryFormula.DoesNotExist:
        return JsonResponse({'error': 'Formula not found'}, status=404)

def _calc_sum_diff(numbers):
    """สูตรบวกลบ: เอาเลข 2 ตัวแรกมาบวกลบ"""
    result1 = str((numbers[0] + numbers[1]) % 10) + str((numbers[0] - numbers[1]) % 10) + str((numbers[0] * numbers[1]) % 10)
    result2 = str((numbers[1] + numbers[0]) % 10) + str((numbers[1] - numbers[0]) % 10) + str((numbers[1] * numbers[0]) % 10)
    result3 = str((sum(numbers[:3]) % 10)) + str((sum(numbers[:2]) % 10)) + str((numbers[0] % 10))
    return [result1, result2, result3]


def _calc_running(numbers):
    """สูตรเลขวิ่ง: เลขที่วิ่งตามลำดับ"""
    base = numbers[0] % 10
    result1 = str(base) + str((base + 1) % 10) + str((base + 2) % 10)
    result2 = str((base + 3) % 10) + str((base + 4) % 10) + str((base + 5) % 10)
    result3 = str((base + 6) % 10) + str((base + 7) % 10) + str((base + 8) % 10)
    return [result1, result2, result3]


def _calc_reverse(numbers):
    """สูตรเลขกลับ: กลับเลขและคำนวณ"""
    reversed_num = int(str(numbers[0])[::-1]) if len(str(numbers[0])) > 1 else numbers[0]
    result1 = str((numbers[0] + reversed_num) % 1000).zfill(3)
    result2 = str((numbers[0] - reversed_num) % 1000).zfill(3)
    result3 = str((numbers[0] * 2) % 1000).zfill(3)
    return [result1, result2, result3]


def _calc_even_odd(numbers):
    """สูตรเลขคู่คี่: แยกเลขคู่คี่"""
    even_nums = [n for n in numbers if n % 2 == 0]
    odd_nums = [n for n in numbers if n % 2 == 1]

    result1 = str(sum(even_nums) % 10) + str(sum(odd_nums) % 10) + str((sum(even_nums) + sum(odd_nums)) % 10)
    result2 = str(len(even_nums)) + str(len(odd_nums)) + str((len(even_nums) + len(odd_nums)) % 10)
    result3 = str(max(even_nums) if even_nums else 0) + str(max(odd_nums) if odd_nums else 0) + str(min(numbers))
    return [result1, result2, result3]


def _calc_default(numbers):
    """สูตรเริ่มต้น"""
    result1 = str(sum(numbers[:3]) % 1000).zfill(3)
    result2 = str((numbers[0] * numbers[1]) % 1000).zfill(3)
    result3 = str((sum(numbers) * 2) % 1000).zfill(3)
    return [result1, result2, result3]


# Task 14: dispatch ด้วย code (ไม่ผูกกับชื่อแสดงผลภาษาไทย)
FORMULA_CALCULATORS = {
    'sum_diff': _calc_sum_diff,
    'running': _calc_running,
    'reverse': _calc_reverse,
    'even_odd': _calc_even_odd,
}


def calculate_by_formula(formula, input_numbers):
    """คำนวณตามสูตรที่เลือก (คืน None ถ้าข้อมูลไม่พอ)"""
    if not input_numbers:
        return None

    try:
        numbers = [int(d) for d in str(input_numbers) if d.isdigit()]
    except (TypeError, ValueError):
        return None

    if len(numbers) < 2:
        return None

    calculator = FORMULA_CALCULATORS.get(getattr(formula, 'code', ''), _calc_default)
    return calculator(numbers)

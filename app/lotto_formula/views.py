from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView
import json
from .models import LotteryFormula, LotteryResult, Prediction

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from datetime import datetime, timedelta

class HomeView(ListView):
    model = LotteryFormula
    template_name = 'lotto_formula/home.html'
    context_object_name = 'formulas'
    
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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        formula = self.get_object()
        context['predictions'] = Prediction.objects.filter(formula=formula)[:10]
        context['page_title'] = f'{formula.name} - สูตรคำนวณหวย'
        context['meta_description'] = f'{formula.description[:150]}...'
        return context

def calculator_view(request):
    formulas = LotteryFormula.objects.all()
    return render(request, 'lotto_formula/calculator.html', {
        'formulas': formulas,
        'page_title': 'เครื่องคำนวณหวย - คำนวณเลขเด็ด',
        'meta_description': 'เครื่องคำนวณหวยออนไลน์ เลือกสูตรและคำนวณเลขเด็ดได้ทันที'
    })

@csrf_exempt
def calculate_numbers(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        formula_id = data.get('formula_id')
        input_numbers = data.get('input_numbers')
        
        # Logic การคำนวณตามสูตร
        formula = get_object_or_404(LotteryFormula, id=formula_id)
        
        # ตัวอย่างการคำนวณ (ต้องปรับตามสูตรจริง)
        calculated_numbers = calculate_by_formula(formula, input_numbers)
        
        return JsonResponse({
            'success': True,
            'calculated_numbers': calculated_numbers,
            'formula_name': formula.name
        })
    
    return JsonResponse({'success': False})

@require_http_methods(["GET"])
def api_stats(request):
    """API endpoint สำหรับสถิติการทำนาย"""
    total_predictions = Prediction.objects.count()
    correct_predictions = Prediction.objects.filter(is_correct=True).count()
    accuracy_rate = (correct_predictions / total_predictions * 100) if total_predictions > 0 else 0
    
    # สถิติแต่ละสูตร
    formula_stats = []
    for formula in LotteryFormula.objects.all():
        formula_predictions = Prediction.objects.filter(formula=formula)
        formula_correct = formula_predictions.filter(is_correct=True).count()
        formula_total = formula_predictions.count()
        formula_accuracy = (formula_correct / formula_total * 100) if formula_total > 0 else 0
        
        formula_stats.append({
            'name': formula.name,
            'total': formula_total,
            'correct': formula_correct,
            'accuracy': round(formula_accuracy, 1)
        })
    
    return JsonResponse({
        'total_predictions': total_predictions,
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
            'draw_date': p.draw_date.strftime('%Y-%m-%d'),
            'is_correct': p.is_correct
        } for p in predictions]
        
        return JsonResponse({
            'formula': {
                'id': formula.id,
                'name': formula.name,
                'description': formula.description,
                'method': formula.method,
                'accuracy_rate': formula.accuracy_rate,
                'total_predictions': formula.total_predictions,
                'correct_predictions': formula.correct_predictions
            },
            'predictions': predictions_data
        })
    except LotteryFormula.DoesNotExist:
        return JsonResponse({'error': 'Formula not found'}, status=404)

def calculate_by_formula(formula, input_numbers):
    """ปรับปรุงการคำนวณให้มีสูตรที่หลากหลายมากขึ้น"""
    if not input_numbers or len(input_numbers) < 2:
        return ["000", "111", "222"]
    
    # แปลงเลขอ้างอิงเป็นตัวเลข
    try:
        numbers = [int(d) for d in input_numbers if d.isdigit()]
        if len(numbers) < 2:
            return ["000", "111", "222"]
    except:
        return ["000", "111", "222"]
    
    if formula.name == "สูตรบวกลบ":
        # สูตรบวกลบ: เอาเลข 2 ตัวแรกมาบวกลบ
        result1 = str((numbers[0] + numbers[1]) % 10) + str((numbers[0] - numbers[1]) % 10) + str((numbers[0] * numbers[1]) % 10)
        result2 = str((numbers[1] + numbers[0]) % 10) + str((numbers[1] - numbers[0]) % 10) + str((numbers[1] * numbers[0]) % 10)
        result3 = str((sum(numbers[:3]) % 10)) + str((sum(numbers[:2]) % 10)) + str((numbers[0] % 10))
        return [result1, result2, result3]
        
    elif formula.name == "สูตรเลขวิ่ง":
        # สูตรเลขวิ่ง: เลขที่วิ่งตามลำดับ
        base = numbers[0] % 10
        result1 = str(base) + str((base + 1) % 10) + str((base + 2) % 10)
        result2 = str((base + 3) % 10) + str((base + 4) % 10) + str((base + 5) % 10)
        result3 = str((base + 6) % 10) + str((base + 7) % 10) + str((base + 8) % 10)
        return [result1, result2, result3]
        
    elif formula.name == "สูตรเลขกลับ":
        # สูตรเลขกลับ: กลับเลขและคำนวณ
        reversed_num = int(str(numbers[0])[::-1]) if len(str(numbers[0])) > 1 else numbers[0]
        result1 = str((numbers[0] + reversed_num) % 1000).zfill(3)
        result2 = str((numbers[0] - reversed_num) % 1000).zfill(3)
        result3 = str((numbers[0] * 2) % 1000).zfill(3)
        return [result1, result2, result3]
        
    elif formula.name == "สูตรเลขคู่คี่":
        # สูตรเลขคู่คี่: แยกเลขคู่คี่
        even_nums = [n for n in numbers if n % 2 == 0]
        odd_nums = [n for n in numbers if n % 2 == 1]
        
        result1 = str(sum(even_nums) % 10) + str(sum(odd_nums) % 10) + str((sum(even_nums) + sum(odd_nums)) % 10)
        result2 = str(len(even_nums)) + str(len(odd_nums)) + str((len(even_nums) + len(odd_nums)) % 10)
        result3 = str(max(even_nums) if even_nums else 0) + str(max(odd_nums) if odd_nums else 0) + str(min(numbers))
        return [result1, result2, result3]
        
    else:
        # สูตรเริ่มต้น
        result1 = str(sum(numbers[:3]) % 1000).zfill(3)
        result2 = str((numbers[0] * numbers[1]) % 1000).zfill(3)
        result3 = str((sum(numbers) * 2) % 1000).zfill(3)
        return [result1, result2, result3]

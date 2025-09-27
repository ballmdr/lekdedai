from django.contrib import admin
from .models import LotteryFormula, LotteryResult, Prediction

@admin.register(LotteryFormula)
class LotteryFormulaAdmin(admin.ModelAdmin):
    list_display = ['name', 'accuracy_rate', 'total_predictions', 'correct_predictions', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']

@admin.register(LotteryResult)
class LotteryResultAdmin(admin.ModelAdmin):
    list_display = ['draw_date', 'first_prize', 'created_at']
    list_filter = ['draw_date', 'created_at']
    search_fields = ['first_prize']
    ordering = ['-draw_date']

@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ['formula', 'predicted_numbers', 'draw_date', 'is_correct', 'created_at']
    list_filter = ['is_correct', 'draw_date', 'formula']
    search_fields = ['predicted_numbers']
    ordering = ['-created_at']

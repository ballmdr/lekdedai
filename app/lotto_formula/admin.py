from django.contrib import admin
from .models import LotteryFormula, LotteryResult, Prediction

@admin.register(LotteryFormula)
class LotteryFormulaAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'version', 'is_approved', 'accuracy_rate', 'verified_count', 'total_predictions', 'created_at']
    list_filter = ['is_approved', 'created_at']
    search_fields = ['code', 'name', 'description']
    readonly_fields = ['created_at']

@admin.register(LotteryResult)
class LotteryResultAdmin(admin.ModelAdmin):
    list_display = ['draw_date', 'first_prize', 'created_at']
    list_filter = ['draw_date', 'created_at']
    search_fields = ['first_prize']
    ordering = ['-draw_date']

@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ['formula', 'predicted_numbers', 'input_numbers', 'draw_date', 'is_correct', 'verified_at', 'created_at']
    list_filter = ['is_correct', 'draw_date', 'formula']
    search_fields = ['predicted_numbers', 'input_numbers']
    ordering = ['-created_at']

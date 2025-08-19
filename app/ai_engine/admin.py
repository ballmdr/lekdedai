from django.contrib import admin
from .models import (
    AIModel, PredictionFactor, LuckyNumberPrediction,
    PredictionAccuracy, UserFeedback
)

@admin.register(AIModel)
class AIModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'version', 'algorithm', 'accuracy', 'is_active', 'training_date']
    list_filter = ['algorithm', 'is_active']
    search_fields = ['name']
    actions = ['activate_models', 'deactivate_models']
    
    def activate_models(self, request, queryset):
        queryset.update(is_active=True)
    activate_models.short_description = "เปิดใช้งานโมเดลที่เลือก"
    
    def deactivate_models(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_models.short_description = "ปิดใช้งานโมเดลที่เลือก"

@admin.register(PredictionFactor)
class PredictionFactorAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'weight', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    ordering = ['-weight', 'name']

@admin.register(LuckyNumberPrediction)
class LuckyNumberPredictionAdmin(admin.ModelAdmin):
    list_display = ['prediction_date', 'for_draw_date', 'overall_confidence', 'views', 'created_at']
    list_filter = ['prediction_date', 'ai_model']
    search_fields = ['two_digit_numbers', 'three_digit_numbers']
    readonly_fields = ['views', 'created_at']
    date_hierarchy = 'prediction_date'
    
    fieldsets = (
        ('ข้อมูลการทำนาย', {
            'fields': ('prediction_date', 'for_draw_date', 'ai_model')
        }),
        ('เลขที่ทำนาย', {
            'fields': ('two_digit_numbers', 'three_digit_numbers', 'overall_confidence')
        }),
        ('รายละเอียด', {
            'fields': ('prediction_details', 'factors_used'),
            'classes': ('collapse',)
        }),
        ('ข้อมูลอื่นๆ', {
            'fields': ('requested_by', 'views', 'created_at'),
        }),
    )

@admin.register(PredictionAccuracy)
class PredictionAccuracyAdmin(admin.ModelAdmin):
    list_display = ['prediction', 'actual_result', 'is_correct_first', 'is_correct_two_digit', 'checked_date']
    list_filter = ['is_correct_first', 'is_correct_two_digit', 'checked_date']
    search_fields = ['actual_result']
    date_hierarchy = 'checked_date'

@admin.register(UserFeedback)
class UserFeedbackAdmin(admin.ModelAdmin):
    list_display = ['prediction', 'user', 'rating', 'is_winner', 'created_at']
    list_filter = ['rating', 'is_winner', 'created_at']
    search_fields = ['comment']
    readonly_fields = ['created_at']
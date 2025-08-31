from django.contrib import admin
from .models import DreamCategory, DreamKeyword, DreamInterpretation
import json

@admin.register(DreamCategory)
class DreamCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']

@admin.register(DreamKeyword)
class DreamKeywordAdmin(admin.ModelAdmin):
    list_display = ['keyword', 'category', 'main_number', 'secondary_number', 'common_numbers']
    list_filter = ['category']
    search_fields = ['keyword', 'numbers']
    ordering = ['keyword']

@admin.register(DreamInterpretation)
class DreamInterpretationAdmin(admin.ModelAdmin):
    list_display = ['interpreted_at', 'get_short_dream', 'sentiment', 'main_symbols', 'get_predicted_numbers_summary']
    list_filter = ['interpreted_at', 'sentiment']
    search_fields = ['dream_text', 'main_symbols', 'suggested_numbers']
    readonly_fields = [
        'interpreted_at', 'ip_address', 'user', 'dream_text',
        'interpretation', 'sentiment', 'main_symbols',
        'predicted_numbers_json', 'keywords_found', 'suggested_numbers'
    ]
    fieldsets = (
        ('ข้อมูลหลัก', {
            'fields': ('interpreted_at', 'user', 'dream_text', 'ip_address')
        }),
        ('ผลการทำนาย (Seer-AI)', {
            'fields': ('sentiment', 'main_symbols', 'interpretation', 'predicted_numbers_json')
        }),
        ('ข้อมูล Legacy (สำหรับ backward compatibility)', {
            'classes': ('collapse',),
            'fields': ('keywords_found', 'suggested_numbers'),
        }),
    )

    def get_short_dream(self, obj):
        return obj.dream_text[:50] + '...' if len(obj.dream_text) > 50 else obj.dream_text
    get_short_dream.short_description = 'ความฝัน'

    def get_predicted_numbers_summary(self, obj):
        if obj.predicted_numbers_json and 'predicted_numbers' in obj.predicted_numbers_json:
            numbers = [item['number'] for item in obj.predicted_numbers_json['predicted_numbers']]
            return ', '.join(numbers)
        return obj.suggested_numbers
    get_predicted_numbers_summary.short_description = 'เลขที่ทำนาย'

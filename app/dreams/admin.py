from django.contrib import admin
from .models import DreamCategory, DreamKeyword, DreamInterpretation

@admin.register(DreamCategory)
class DreamCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']

@admin.register(DreamKeyword)
class DreamKeywordAdmin(admin.ModelAdmin):
    list_display = ['keyword', 'category', 'numbers']
    list_filter = ['category']
    search_fields = ['keyword', 'numbers']
    ordering = ['keyword']

@admin.register(DreamInterpretation)
class DreamInterpretationAdmin(admin.ModelAdmin):
    list_display = ['interpreted_at', 'get_short_dream', 'suggested_numbers']
    list_filter = ['interpreted_at']
    search_fields = ['dream_text', 'suggested_numbers']
    readonly_fields = ['interpreted_at', 'ip_address']
    
    def get_short_dream(self, obj):
        return obj.dream_text[:50] + '...' if len(obj.dream_text) > 50 else obj.dream_text
    get_short_dream.short_description = 'ความฝัน'
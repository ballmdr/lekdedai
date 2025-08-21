from django.contrib import admin
from django.utils.html import format_html
from .models import LottoResult

@admin.register(LottoResult)
class LottoResultAdmin(admin.ModelAdmin):
    """การจัดการผลรางวัลหวยใน Django Admin"""
    
    list_display = [
        'draw_date', 
        'formatted_draw_date', 
        'is_today_display', 
        'is_recent_display',
        'source',
        'created_at', 
        'updated_at'
    ]
    
    list_filter = [
        'draw_date',
        'source',
        'created_at',
        'updated_at',
    ]
    
    search_fields = ['draw_date']
    
    readonly_fields = ['created_at', 'updated_at']
    
    date_hierarchy = 'draw_date'
    
    ordering = ['-draw_date']
    
    fieldsets = (
        ('ข้อมูลพื้นฐาน', {
            'fields': ('draw_date', 'result_data', 'source')
        }),
        ('ข้อมูลระบบ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def formatted_draw_date(self, obj):
        """แสดงวันที่ในรูปแบบไทย"""
        return obj.formatted_date
    formatted_draw_date.short_description = 'วันที่ (ไทย)'
    
    def is_today_display(self, obj):
        """แสดงสถานะวันนี้"""
        if obj.is_today:
            return format_html('<span style="color: green;">✓ วันนี้</span>')
        return format_html('<span style="color: gray;">-</span>')
    is_today_display.short_description = 'วันนี้'
    
    def is_recent_display(self, obj):
        """แสดงสถานะข้อมูลล่าสุด"""
        if obj.is_recent:
            return format_html('<span style="color: blue;">✓ ล่าสุด</span>')
        return format_html('<span style="color: gray;">-</span>')
    is_recent_display.short_description = 'ข้อมูลล่าสุด'
    
    def has_add_permission(self, request):
        """ไม่อนุญาตให้เพิ่มข้อมูลผ่าน admin"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """ไม่อนุญาตให้ลบข้อมูลผ่าน admin"""
        return False


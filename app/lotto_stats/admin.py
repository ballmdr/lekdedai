from django.contrib import admin
from .models import LotteryDraw, NumberStatistics, HotColdNumber

@admin.register(LotteryDraw)
class LotteryDrawAdmin(admin.ModelAdmin):
    list_display = ['draw_date', 'first_prize', 'two_digit', 'draw_round']
    list_filter = ['draw_date']
    search_fields = ['first_prize', 'two_digit']
    ordering = ['-draw_date']
    
    fieldsets = (
        ('ข้อมูลงวด', {
            'fields': ('draw_date', 'draw_round')
        }),
        ('รางวัล', {
            'fields': ('first_prize', 'two_digit', 'three_digit_front', 'three_digit_back')
        }),
    )

@admin.register(NumberStatistics)
class NumberStatisticsAdmin(admin.ModelAdmin):
    list_display = ['number', 'number_type', 'total_appearances', 'last_appeared', 'days_since_last']
    list_filter = ['number_type', 'last_appeared']
    search_fields = ['number']
    ordering = ['-total_appearances']
    readonly_fields = ['updated_at']

@admin.register(HotColdNumber)
class HotColdNumberAdmin(admin.ModelAdmin):
    list_display = ['date', 'calculation_days', 'get_hot_2d_preview', 'get_cold_2d_preview']
    list_filter = ['date', 'calculation_days']
    
    def get_hot_2d_preview(self, obj):
        return ', '.join(obj.hot_2d[:5]) if obj.hot_2d else '-'
    get_hot_2d_preview.short_description = 'เลขฮอต 2 ตัว (5 อันดับแรก)'
    
    def get_cold_2d_preview(self, obj):
        return ', '.join(obj.cold_2d[:5]) if obj.cold_2d else '-'
    get_cold_2d_preview.short_description = 'เลขเย็น 2 ตัว (5 อันดับแรก)'
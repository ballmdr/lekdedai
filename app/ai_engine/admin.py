from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    # เก่า
    AIModel, PredictionFactor, LuckyNumberPrediction,
    PredictionAccuracy, UserFeedback,
    # ใหม่
    DataSource, DataIngestionRecord, AIModelType, 
    PredictionSession, ModelPrediction, EnsemblePrediction,
    PredictionAccuracyTracking
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
    
    # เพิ่มแสดงข้อมูลพารามิเตอร์
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('training_date',)
        return self.readonly_fields

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
    list_display = ['get_prediction_display', 'user', 'rating', 'is_winner', 'created_at']
    list_filter = ['rating', 'is_winner', 'created_at']
    search_fields = ['comment']
    readonly_fields = ['created_at']
    
    def get_prediction_display(self, obj):
        if obj.ensemble_prediction:
            return f"AI งวด {obj.ensemble_prediction.session.for_draw_date}"
        elif obj.old_prediction:
            return f"เก่า {obj.old_prediction.prediction_date}"
        return "-"
    get_prediction_display.short_description = "การทำนาย"

# === โมเดลใหม่ ===

@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'source_type', 'is_active', 'scraping_interval', 'last_scraped_display']
    list_filter = ['source_type', 'is_active']
    search_fields = ['name']
    actions = ['activate_sources', 'deactivate_sources', 'run_ingestion']
    
    fieldsets = (
        ('ข้อมูลพื้นฐาน', {
            'fields': ('name', 'source_type', 'is_active')
        }),
        ('การตั้งค่า', {
            'fields': ('url', 'api_endpoint', 'api_key', 'scraping_interval')
        }),
        ('สถิติ', {
            'fields': ('last_scraped',),
            'classes': ('collapse',)
        })
    )
    
    def last_scraped_display(self, obj):
        if obj.last_scraped:
            return obj.last_scraped.strftime('%d/%m/%Y %H:%M')
        return 'ยังไม่เคย'
    last_scraped_display.short_description = 'เก็บข้อมูลล่าสุด'
    
    def activate_sources(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f'เปิดใช้งาน {queryset.count()} แหล่งข้อมูล')
    activate_sources.short_description = "เปิดใช้งานแหล่งข้อมูล"
    
    def deactivate_sources(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f'ปิดใช้งาน {queryset.count()} แหล่งข้อมูล')
    deactivate_sources.short_description = "ปิดใช้งานแหล่งข้อมูล"
    
    def run_ingestion(self, request, queryset):
        from .data_ingestion import DataIngestionManager
        manager = DataIngestionManager()
        
        total_records = 0
        for source in queryset:
            count = manager.run_ingestion_for_source(source.id)
            total_records += count
        
        self.message_user(request, f'เก็บข้อมูลได้ {total_records} รายการ')
    run_ingestion.short_description = "เก็บข้อมูลทันที"

@admin.register(DataIngestionRecord)
class DataIngestionRecordAdmin(admin.ModelAdmin):
    list_display = ['title_short', 'data_source', 'processing_status', 'relevance_score', 'numbers_count', 'ingested_at']
    list_filter = ['data_source__source_type', 'processing_status', 'ingested_at']
    search_fields = ['title', 'raw_content']
    readonly_fields = ['ingested_at', 'processed_at']
    date_hierarchy = 'ingested_at'
    
    fieldsets = (
        ('ข้อมูลต้นฉบับ', {
            'fields': ('data_source', 'title', 'author', 'publish_date')
        }),
        ('เนื้อหา', {
            'fields': ('raw_content', 'processed_content'),
            'classes': ('collapse',)
        }),
        ('ผลการวิเคราะห์', {
            'fields': ('extracted_numbers', 'keywords', 'sentiment_score', 'relevance_score')
        }),
        ('สถานะ', {
            'fields': ('processing_status', 'error_message', 'ingested_at', 'processed_at')
        })
    )
    
    def title_short(self, obj):
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_short.short_description = 'หัวข้อ'
    
    def numbers_count(self, obj):
        return len(obj.extracted_numbers) if obj.extracted_numbers else 0
    numbers_count.short_description = 'จำนวนเลข'

@admin.register(AIModelType)
class AIModelTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'role', 'weight_in_ensemble', 'is_active']
    list_filter = ['role', 'is_active']
    search_fields = ['name', 'description']
    
    fieldsets = (
        ('ข้อมูลโมเดล', {
            'fields': ('name', 'role', 'description', 'is_active')
        }),
        ('การตั้งค่า', {
            'fields': ('input_data_types', 'weight_in_ensemble')
        })
    )

@admin.register(PredictionSession)
class PredictionSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'for_draw_date', 'status', 'total_data_points', 'processing_time_display', 'start_time']
    list_filter = ['status', 'for_draw_date']
    search_fields = ['session_id']
    readonly_fields = ['session_id', 'start_time', 'end_time', 'processing_time_seconds']
    date_hierarchy = 'start_time'
    actions = ['rerun_sessions']
    
    fieldsets = (
        ('ข้อมูลเซสชัน', {
            'fields': ('session_id', 'for_draw_date', 'status')
        }),
        ('ช่วงเวลาเก็บข้อมูล', {
            'fields': ('data_collection_period_start', 'data_collection_period_end')
        }),
        ('สถิติ', {
            'fields': ('total_data_sources', 'total_data_points', 'processing_time_seconds')
        }),
        ('เวลา', {
            'fields': ('start_time', 'end_time'),
            'classes': ('collapse',)
        })
    )
    
    def processing_time_display(self, obj):
        if obj.processing_time_seconds:
            return f"{obj.processing_time_seconds:.1f} วิ"
        return "-"
    processing_time_display.short_description = 'เวลาประมวลผล'
    
    def rerun_sessions(self, request, queryset):
        from .prediction_engine import PredictionEngine
        engine = PredictionEngine()
        
        count = 0
        for session in queryset.filter(status__in=['failed', 'completed']):
            try:
                engine.run_prediction(session)
                count += 1
            except Exception as e:
                self.message_user(request, f'เซสชัน {session.session_id} ล้มเหลว: {str(e)}', level='ERROR')
        
        self.message_user(request, f'รันเซสชันใหม่สำเร็จ {count} เซสชัน')
    rerun_sessions.short_description = "รันการทำนายใหม่"

@admin.register(ModelPrediction)
class ModelPredictionAdmin(admin.ModelAdmin):
    list_display = ['session_display', 'model_type', 'numbers_preview', 'avg_confidence', 'processing_time', 'created_at']
    list_filter = ['model_type__role', 'created_at']
    search_fields = ['session__session_id']
    readonly_fields = ['created_at']
    
    def session_display(self, obj):
        return f"{obj.session.session_id} ({obj.session.for_draw_date})"
    session_display.short_description = 'เซสชัน'
    
    def numbers_preview(self, obj):
        numbers = obj.predicted_numbers
        preview = []
        if numbers.get('two_digit'):
            preview.append(f"2ตัว: {', '.join(numbers['two_digit'][:2])}")
        if numbers.get('three_digit'):
            preview.append(f"3ตัว: {', '.join(numbers['three_digit'][:1])}")
        return " | ".join(preview)
    numbers_preview.short_description = 'เลขที่ทำนาย'
    
    def avg_confidence(self, obj):
        confidence = obj.confidence_scores
        all_scores = []
        for scores in confidence.values():
            all_scores.extend(scores)
        if all_scores:
            return f"{sum(all_scores)/len(all_scores):.1%}"
        return "-"
    avg_confidence.short_description = 'ความมั่นใจเฉลี่ย'

@admin.register(EnsemblePrediction)
class EnsemblePredictionAdmin(admin.ModelAdmin):
    list_display = ['session_display', 'top_numbers_display', 'overall_confidence', 'view_count', 'is_featured', 'prediction_timestamp']
    list_filter = ['is_featured', 'prediction_timestamp', 'session__for_draw_date']
    search_fields = ['session__session_id', 'prediction_summary']
    readonly_fields = ['prediction_timestamp', 'view_count']
    actions = ['feature_predictions', 'unfeature_predictions', 'lock_sessions']
    
    fieldsets = (
        ('ข้อมูลการทำนาย', {
            'fields': ('session', 'overall_confidence', 'prediction_summary')
        }),
        ('ผลลัพธ์', {
            'fields': ('final_two_digit', 'final_three_digit')
        }),
        ('รายละเอียด', {
            'fields': ('model_contributions', 'total_data_points'),
            'classes': ('collapse',)
        }),
        ('การแสดงผล', {
            'fields': ('is_featured', 'view_count', 'prediction_timestamp')
        })
    )
    
    def session_display(self, obj):
        return f"งวด {obj.session.for_draw_date}"
    session_display.short_description = 'งวด'
    
    def top_numbers_display(self, obj):
        display_parts = []
        
        # เลข 2 ตัว
        if obj.final_two_digit:
            top_2 = [item['number'] for item in obj.get_top_two_digit_numbers(2)]
            display_parts.append(f"2ตัว: {', '.join(top_2)}")
        
        # เลข 3 ตัว
        if obj.final_three_digit:
            top_3 = [item['number'] for item in obj.get_top_three_digit_numbers(1)]
            display_parts.append(f"3ตัว: {', '.join(top_3)}")
        
        return " | ".join(display_parts)
    top_numbers_display.short_description = 'เลขเด็ด'
    
    def feature_predictions(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, f'ตั้งเป็นเด่น {queryset.count()} การทำนาย')
    feature_predictions.short_description = "ตั้งเป็นการทำนายเด่น"
    
    def unfeature_predictions(self, request, queryset):
        queryset.update(is_featured=False)
        self.message_user(request, f'ยกเลิกเด่น {queryset.count()} การทำนาย')
    unfeature_predictions.short_description = "ยกเลิกการทำนายเด่น"
    
    def lock_sessions(self, request, queryset):
        sessions = [pred.session for pred in queryset]
        for session in sessions:
            session.status = 'locked'
            session.save()
        self.message_user(request, f'ล็อกแล้ว {len(sessions)} เซสชัน')
    lock_sessions.short_description = "ล็อกเซสชัน (ป้องกันการเปลี่ยนแปลง)"

@admin.register(PredictionAccuracyTracking)
class PredictionAccuracyTrackingAdmin(admin.ModelAdmin):
    list_display = ['prediction_display', 'actual_results_display', 'accuracy_display', 'checked_at']
    list_filter = ['two_digit_accuracy', 'three_digit_accuracy', 'first_prize_accuracy', 'checked_at']
    readonly_fields = ['checked_at', 'updated_at']
    
    fieldsets = (
        ('การทำนาย', {
            'fields': ('ensemble_prediction',)
        }),
        ('ผลที่ออกจริง', {
            'fields': ('actual_first_prize', 'actual_last_two_digits', 'actual_last_three_digits')
        }),
        ('ความแม่นยำ', {
            'fields': ('two_digit_accuracy', 'three_digit_accuracy', 'first_prize_accuracy')
        }),
        ('รายละเอียด', {
            'fields': ('model_accuracies', 'checked_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def prediction_display(self, obj):
        return f"งวด {obj.ensemble_prediction.session.for_draw_date}"
    prediction_display.short_description = 'การทำนาย'
    
    def actual_results_display(self, obj):
        parts = []
        if obj.actual_first_prize:
            parts.append(f"รางวัลที่1: {obj.actual_first_prize}")
        if obj.actual_last_two_digits:
            parts.append(f"2ตัวท้าย: {obj.actual_last_two_digits}")
        return " | ".join(parts) if parts else "-"
    actual_results_display.short_description = 'ผลที่ออกจริง'
    
    def accuracy_display(self, obj):
        accuracies = []
        if obj.two_digit_accuracy:
            accuracies.append("2ตัว✓")
        if obj.three_digit_accuracy:
            accuracies.append("3ตัว✓")
        if obj.first_prize_accuracy:
            accuracies.append("รางวัลที่1✓")
        return " ".join(accuracies) if accuracies else "ไม่ถูก"
    accuracy_display.short_description = 'ความแม่นยำ'

# กำหนดหมวดหมู่ใน Admin Site
admin.site.site_header = 'LekDedAI - ระบบจัดการ AI'
admin.site.site_title = 'AI Management'
admin.site.index_title = 'ระบบทำนายเลขเด็ดด้วย AI'
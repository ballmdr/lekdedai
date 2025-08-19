from django.contrib import admin
from django.utils import timezone
from .models import NewsCategory, NewsArticle, LuckyNumberHint, NewsComment
from .forms import NewsCategoryForm, NewsArticleForm

@admin.register(NewsCategory)
class NewsCategoryAdmin(admin.ModelAdmin):
    form = NewsCategoryForm
    list_display = ['name', 'slug']
    
    def save_model(self, request, obj, form, change):
        # สร้าง slug อัตโนมัติถ้าไม่มี
        if not obj.slug:
            from lekdedai.utils import generate_unique_slug
            obj.slug = generate_unique_slug(NewsCategory, obj.name, obj.slug)
        super().save_model(request, obj, form, change)

@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    form = NewsArticleForm
    list_display = ['title', 'category', 'status', 'published_date', 'views', 'confidence_score']
    list_filter = ['status', 'category', 'published_date']
    search_fields = ['title', 'content', 'extracted_numbers']
    date_hierarchy = 'published_date'
    
    def save_model(self, request, obj, form, change):
        # สร้าง slug อัตโนมัติถ้าไม่มี
        if not obj.slug:
            from lekdedai.utils import generate_unique_slug
            obj.slug = generate_unique_slug(NewsArticle, obj.title, obj.slug)
        super().save_model(request, obj, form, change)
    
    fieldsets = (
        ('ข้อมูลพื้นฐาน', {
            'fields': ('title', 'slug', 'category', 'author')
        }),
        ('เนื้อหา', {
            'fields': ('intro', 'content', 'featured_image')
        }),
        ('เลขจากข่าว', {
            'fields': ('extracted_numbers', 'confidence_score'),
            'classes': ('collapse',)
        }),
        ('การเผยแพร่', {
            'fields': ('status', 'published_date')
        }),
        ('SEO', {
            'fields': ('meta_description',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['publish_articles', 'extract_numbers']
    
    def publish_articles(self, request, queryset):
        queryset.update(status='published', published_date=timezone.now())
        self.message_user(request, f"เผยแพร่ {queryset.count()} บทความแล้ว")
    publish_articles.short_description = "เผยแพร่บทความที่เลือก"
    
    def extract_numbers(self, request, queryset):
        for article in queryset:
            numbers = article.extract_numbers_from_content()
            article.extracted_numbers = ', '.join(numbers)
            article.save()
        self.message_user(request, f"วิเคราะห์เลขจาก {queryset.count()} บทความแล้ว")
    extract_numbers.short_description = "วิเคราะห์เลขจากเนื้อหา"

@admin.register(LuckyNumberHint)
class LuckyNumberHintAdmin(admin.ModelAdmin):
    list_display = ['source_name', 'source_type', 'lucky_numbers', 'hint_date', 'reliability_score']
    list_filter = ['source_type', 'hint_date', 'reliability_score']
    search_fields = ['source_name', 'lucky_numbers', 'location']
    date_hierarchy = 'hint_date'

@admin.register(NewsComment)
class NewsCommentAdmin(admin.ModelAdmin):
    list_display = ['article', 'name', 'created_at', 'is_approved']
    list_filter = ['is_approved', 'created_at']
    search_fields = ['content', 'name', 'suggested_numbers']
    actions = ['approve_comments']
    
    def approve_comments(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f"อนุมัติ {queryset.count()} ความคิดเห็นแล้ว")
    approve_comments.short_description = "อนุมัติความคิดเห็นที่เลือก"
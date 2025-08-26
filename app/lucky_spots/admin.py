from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Region, Province, LocationCategory, LuckyLocation, 
    LocationImage, LocationComment, LocationNewsTag
)


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_name_display']
    list_filter = ['name']


@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ['name', 'region']
    list_filter = ['region']
    search_fields = ['name']


@admin.register(LocationCategory)
class LocationCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_name_display', 'icon']
    list_filter = ['name']


class LocationImageInline(admin.TabularInline):
    model = LocationImage
    extra = 1
    fields = ['image', 'caption', 'order']


class LocationCommentInline(admin.TabularInline):
    model = LocationComment
    extra = 0
    readonly_fields = ['created_at', 'user']
    fields = ['name', 'email', 'comment', 'lucky_number_shared', 'is_approved', 'created_at']


class LocationNewsTagInline(admin.TabularInline):
    model = LocationNewsTag
    extra = 0
    raw_id_fields = ['news_article']


@admin.register(LuckyLocation)
class LuckyLocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'province', 'category', 'is_active', 'views_count', 'created_at']
    list_filter = ['is_active', 'category', 'province__region', 'province', 'created_at']
    search_fields = ['name', 'description', 'address']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['views_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('ข้อมูลพื้นฐาน', {
            'fields': ('name', 'slug', 'description', 'is_active')
        }),
        ('ตำแหน่งที่ตั้ง', {
            'fields': ('latitude', 'longitude', 'address', 'province', 'category')
        }),
        ('เลขเด็ดและไฮไลท์', {
            'fields': ('lucky_numbers', 'highlights')
        }),
        ('รูปภาพ', {
            'fields': ('main_image',)
        }),
        ('สถิติ', {
            'fields': ('views_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [LocationImageInline, LocationCommentInline, LocationNewsTagInline]
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)


@admin.register(LocationImage)
class LocationImageAdmin(admin.ModelAdmin):
    list_display = ['location', 'caption', 'order', 'image_thumbnail']
    list_filter = ['location__province', 'location__category']
    search_fields = ['location__name', 'caption']
    
    def image_thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;"/>', 
                             obj.image.url)
        return "ไม่มีรูป"
    image_thumbnail.short_description = "รูปภาพ"


@admin.register(LocationComment)
class LocationCommentAdmin(admin.ModelAdmin):
    list_display = ['location', 'get_author_name', 'lucky_number_shared', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'location__province', 'created_at']
    search_fields = ['location__name', 'name', 'comment']
    readonly_fields = ['created_at']
    
    def get_author_name(self, obj):
        return obj.get_author_name()
    get_author_name.short_description = "ผู้แสดงความคิดเห็น"


@admin.register(LocationNewsTag)
class LocationNewsTagAdmin(admin.ModelAdmin):
    list_display = ['location', 'news_article', 'created_at']
    list_filter = ['location__province', 'created_at']
    search_fields = ['location__name', 'news_article__title']
    raw_id_fields = ['location', 'news_article']

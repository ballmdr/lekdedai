from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Q
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from .models import LuckyLocation, Province, LocationCategory, LocationComment
from news.models import NewsArticle


def map_view(request):
    """Main map view showing all lucky locations"""
    provinces = Province.objects.select_related('region').all()
    categories = LocationCategory.objects.all()
    
    context = {
        'provinces': provinces,
        'categories': categories,
        'page_title': 'แผนที่พิกัดเลขเด็ด',
    }
    return render(request, 'lucky_spots/map.html', context)


def locations_api(request):
    """API endpoint to get all locations for the map"""
    locations = LuckyLocation.objects.filter(is_active=True).select_related('province', 'category')
    
    data = []
    for location in locations:
        data.append({
            'id': location.id,
            'name': location.name,
            'slug': location.slug,
            'latitude': float(location.latitude),
            'longitude': float(location.longitude),
            'province': location.province.name,
            'category': location.category.get_name_display(),
            'category_code': location.category.name,
            'main_image': location.main_image.url if location.main_image else '',
            'lucky_numbers': location.get_lucky_numbers_list()[:3],  # First 3 numbers
            'url': location.get_absolute_url(),
        })
    
    return JsonResponse({'locations': data})


def locations_search_api(request):
    """API endpoint for searching and filtering locations"""
    query = request.GET.get('q', '')
    province_id = request.GET.get('province', '')
    category_id = request.GET.get('category', '')
    region = request.GET.get('region', '')
    
    locations = LuckyLocation.objects.filter(is_active=True).select_related('province', 'category')
    
    # Search by name or description
    if query:
        locations = locations.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(address__icontains=query)
        )
    
    # Filter by province
    if province_id:
        locations = locations.filter(province_id=province_id)
    
    # Filter by category
    if category_id:
        locations = locations.filter(category_id=category_id)
    
    # Filter by region
    if region:
        locations = locations.filter(province__region__name=region)
    
    data = []
    for location in locations:
        data.append({
            'id': location.id,
            'name': location.name,
            'slug': location.slug,
            'latitude': float(location.latitude),
            'longitude': float(location.longitude),
            'province': location.province.name,
            'category': location.category.get_name_display(),
            'category_code': location.category.name,
            'main_image': location.main_image.url if location.main_image else '',
            'lucky_numbers': location.get_lucky_numbers_list()[:3],
            'url': location.get_absolute_url(),
        })
    
    return JsonResponse({'locations': data})


def location_detail(request, slug):
    """Detail view for a specific location"""
    location = get_object_or_404(LuckyLocation, slug=slug, is_active=True)
    
    # Increment views count
    location.views_count += 1
    location.save(update_fields=['views_count'])
    
    # Get approved comments
    comments = location.comments.filter(is_approved=True).select_related('user')
    
    # Get related news articles
    related_news = NewsArticle.objects.filter(
        locationnewstag__location=location
    ).distinct()[:5]
    
    # Get nearby locations (within ~50km)
    from decimal import Decimal
    range_offset = Decimal('0.45')
    nearby_locations = LuckyLocation.objects.filter(
        is_active=True,
        latitude__range=[location.latitude - range_offset, location.latitude + range_offset],
        longitude__range=[location.longitude - range_offset, location.longitude + range_offset]
    ).exclude(id=location.id)[:6]
    
    context = {
        'location': location,
        'comments': comments,
        'related_news': related_news,
        'nearby_locations': nearby_locations,
        'lucky_numbers_list': location.get_lucky_numbers_list(),
        'page_title': f'{location.name} - พิกัดเลขเด็ด',
        'meta_description': location.highlights or location.description[:200],
    }
    return render(request, 'lucky_spots/location_detail.html', context)


@require_http_methods(["POST"])
def add_comment(request, slug):
    """Add a comment to a location"""
    location = get_object_or_404(LuckyLocation, slug=slug, is_active=True)
    
    name = request.POST.get('name', '').strip()
    email = request.POST.get('email', '').strip()
    comment = request.POST.get('comment', '').strip()
    lucky_number = request.POST.get('lucky_number', '').strip()
    
    if not name or not comment:
        messages.error(request, 'กรุณากรอกชื่อและความคิดเห็น')
        return redirect('lucky_spots:location_detail', slug=slug)
    
    # Create comment
    LocationComment.objects.create(
        location=location,
        user=request.user if request.user.is_authenticated else None,
        name=name,
        email=email,
        comment=comment,
        lucky_number_shared=lucky_number,
        is_approved=False  # Requires admin approval
    )
    
    messages.success(request, 'ความคิดเห็นของคุณถูกส่งแล้ว รอการอนุมัติจากผู้ดูแลระบบ')
    return redirect('lucky_spots:location_detail', slug=slug)

from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta

from .models import NewsArticle, NewsCategory, LuckyNumberHint, NewsComment
from .news_analyzer import NewsAnalyzer

def news_list(request):
    """หน้ารวมข่าวทั้งหมด"""
    # ดึงเฉพาะข่าวที่เผยแพร่แล้ว
    articles = NewsArticle.objects.filter(status='published').select_related('category', 'author')
    
    # Filter by category
    category_slug = request.GET.get('category')
    if category_slug:
        category = get_object_or_404(NewsCategory, slug=category_slug)
        articles = articles.filter(category=category)
    else:
        category = None
    
    # Search
    query = request.GET.get('q')
    if query:
        articles = articles.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(extracted_numbers__icontains=query)
        )
    
    # Pagination
    paginator = Paginator(articles, 12)
    page = request.GET.get('page')
    articles = paginator.get_page(page)
    
    # ดึงเลขเด็ดล่าสุด
    latest_hints = LuckyNumberHint.objects.all()[:5]
    
    # หมวดหมู่ทั้งหมด
    categories = NewsCategory.objects.annotate(
        article_count=Count('articles')
    )
    
    context = {
        'articles': articles,
        'category': category,
        'categories': categories,
        'latest_hints': latest_hints,
        'query': query,
    }
    
    return render(request, 'news/news_list.html', context)

def article_detail(request, slug):
    """หน้ารายละเอียดข่าว"""
    article = get_object_or_404(
        NewsArticle.objects.select_related('category', 'author'),
        slug=slug,
        status='published'
    )
    
    # เพิ่มยอดวิว
    article.views += 1
    article.save(update_fields=['views'])
    
    # ดึงข่าวที่เกี่ยวข้อง
    related_articles = NewsArticle.objects.filter(
        category=article.category,
        status='published'
    ).exclude(id=article.id)[:4]
    
    # ดึงเลขเด็ดที่เกี่ยวข้อง
    lucky_hints = article.lucky_hints.all()
    
    # ดึงความคิดเห็นที่อนุมัติแล้ว
    comments = article.comments.filter(is_approved=True)
    
    context = {
        'article': article,
        'related_articles': related_articles,
        'lucky_hints': lucky_hints,
        'comments': comments,
        'extracted_numbers': article.get_extracted_numbers_list(),
    }
    
    return render(request, 'news/article_detail.html', context)

def lucky_hints(request):
    """หน้าแสดงเลขเด็ดทั้งหมด"""
    hints = LuckyNumberHint.objects.all()
    
    # Filter by source type
    source_type = request.GET.get('source')
    if source_type:
        hints = hints.filter(source_type=source_type)
    
    # Filter by date range
    days = request.GET.get('days', '7')
    try:
        days = int(days)
        date_from = timezone.now().date() - timedelta(days=days)
        hints = hints.filter(hint_date__gte=date_from)
    except:
        pass
    
    # Group by date
    hints_by_date = {}
    for hint in hints:
        date_key = hint.hint_date
        if date_key not in hints_by_date:
            hints_by_date[date_key] = []
        hints_by_date[date_key].append(hint)
    
    context = {
        'hints_by_date': hints_by_date,
        'source_type': source_type,
        'days': days,
    }
    
    return render(request, 'news/lucky_hints.html', context)

@require_POST
def add_comment(request, slug):
    """เพิ่มความคิดเห็น"""
    article = get_object_or_404(NewsArticle, slug=slug)
    
    content = request.POST.get('content', '').strip()
    suggested_numbers = request.POST.get('suggested_numbers', '').strip()
    
    if not content:
        messages.error(request, 'กรุณากรอกความคิดเห็น')
        return redirect('news:article_detail', slug=slug)
    
    comment = NewsComment.objects.create(
        article=article,
        user=request.user if request.user.is_authenticated else None,
        name=request.POST.get('name', 'ผู้ไม่ประสงค์ออกนาม'),
        email=request.POST.get('email', ''),
        content=content,
        suggested_numbers=suggested_numbers,
        is_approved=False  # ต้องรออนุมัติ
    )
    
    messages.success(request, 'ส่งความคิดเห็นแล้ว รอการอนุมัติ')
    return redirect('news:article_detail', slug=slug)

def analyze_news(request, article_id):
    """API วิเคราะห์เลขจากข่าว"""
    # ตรวจสอบสิทธิ์แอดมิน
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'error': 'ไม่มีสิทธิ์ในการวิเคราะห์'
        }, status=403)
    
    article = get_object_or_404(NewsArticle, id=article_id)
    
    try:
        # วิเคราะห์เลข
        analyzer = NewsAnalyzer()
        result = analyzer.analyze_article(article)
        
        # อัพเดตเลขในบทความ
        article.extracted_numbers = ', '.join(result['numbers'])
        article.confidence_score = result['confidence']
        article.save()
        
        return JsonResponse({
            'success': True,
            'numbers': result['numbers'],
            'confidence': result['confidence'],
            'keywords': result['keywords'],
            'message': 'วิเคราะห์เสร็จแล้ว'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'เกิดข้อผิดพลาดในการวิเคราะห์: {str(e)}'
        }, status=500)
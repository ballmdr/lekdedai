from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from .models import NewsArticle, NewsCategory, LuckyNumberHint, NewsComment
from .ingestion import extract_numbers, get_news_freshness
from utils.api import api_server_error, audit
from utils.rate_limit import ratelimit
# from .news_analyzer import NewsAnalyzer  # ใช้ analyzer_switcher แทน

logger = logging.getLogger(__name__)

def news_list(request):
    """หน้ารวมข่าวทั้งหมด"""
    # ดึงเฉพาะข่าวที่เผยแพร่แล้ว
    articles = NewsArticle.objects.filter(status='published').select_related('category', 'author')
    
    # Filter by category (slug ที่ไม่มีอยู่จริงให้แสดงว่างแทน 404)
    category_slug = request.GET.get('category')
    category = None
    if category_slug:
        category = NewsCategory.objects.filter(slug=category_slug).first()
        if category:
            articles = articles.filter(category=category)
        else:
            articles = articles.none()
    
    # Search
    query = request.GET.get('q')
    if query:
        articles = articles.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query)
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
        'category_slug': category_slug,
        'categories': categories,
        'latest_hints': latest_hints,
        'query': query,
        'freshness': get_news_freshness(),
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
    
    # การวิเคราะห์ข่าวถูกลบออกเพื่อความเรียบง่าย
    insight_analysis = None
    
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
        'insight_analysis': insight_analysis,
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

@ratelimit("30/m", redirect_back=True)
@require_POST
def add_comment(request, slug):
    """เพิ่มความคิดเห็น (จำกัดความยาว + ต้องรออนุมัติก่อนแสดง)"""
    article = get_object_or_404(NewsArticle, slug=slug)

    content = request.POST.get('content', '').strip()[:1000]
    suggested_numbers = request.POST.get('suggested_numbers', '').strip()[:100]

    if not content:
        messages.error(request, 'กรุณากรอกความคิดเห็น')
        return redirect('news:article_detail', slug=slug)
    
    comment = NewsComment.objects.create(
        article=article,
        user=request.user if request.user.is_authenticated else None,
        name=request.POST.get('name', 'ผู้ไม่ประสงค์ออกนาม')[:100],
        email=request.POST.get('email', '')[:254],
        content=content,
        suggested_numbers=suggested_numbers,
        is_approved=False  # ต้องรออนุมัติ
    )
    
    messages.success(request, 'ส่งความคิดเห็นแล้ว รอการอนุมัติ')
    return redirect('news:article_detail', slug=slug)

@ratelimit("20/m")
@require_POST
def analyze_news(request, article_id):
    """API วิเคราะห์เลขจากข่าว (Task 23: ต้องมี CSRF + rate limit; เขียนเฉพาะฟิลด์ปัจจุบัน)."""
    article = get_object_or_404(NewsArticle, id=article_id)

    try:
        from .analyzer_switcher import AnalyzerSwitcher

        switcher = AnalyzerSwitcher(preferred_analyzer="groq")
        analysis_result = switcher.analyze_news_for_lottery(article.title, article.content)
    except Exception as exc:
        logger.warning("analyze_news AI failed for article %s: %r", article_id, exc)
        analysis_result = {"success": False}

    if (analysis_result or {}).get("success"):
        numbers = [
            str(n) for n in (analysis_result.get("numbers") or [])
            if str(n).isdigit() and len(str(n)) in (2, 3)
        ][:15]
        _merge_article_numbers(article, numbers, "วิเคราะห์ด้วย AI")
        article.analysis_status = "analyzed"
        article.save(update_fields=["numbers_with_reasons", "analysis_status"])
        audit(request, "news_analyze", f"article={article_id} engine=ai")
        return JsonResponse({
            "success": True,
            "numbers": numbers,
            "confidence": analysis_result.get("relevance_score"),
            "category": analysis_result.get("category", "other"),
            "reasoning": analysis_result.get("reasoning", ""),
            "analyzer_type": analysis_result.get("analyzer_type", "unknown"),
            "is_insight_ai": True,
            "message": f"วิเคราะห์ด้วย {(analysis_result.get('analyzer_type') or 'AI').upper()} สำเร็จ - พบ {len(numbers)} เลข",
        })

    # AI ล้มเหลว — ใช้ regex ภายใน ไม่ทิ้งข้อมูล
    try:
        numbers = extract_numbers(article.content or "", article.title or "")[:10]
    except Exception as exc:
        return api_server_error(request, exc)
    _merge_article_numbers(article, numbers, "วิเคราะห์พื้นฐาน")
    article.analysis_status = "analyzed" if numbers else "failed"
    article.save(update_fields=["numbers_with_reasons", "analysis_status"])
    audit(request, "news_analyze", f"article={article_id} engine=basic")
    return JsonResponse({
        "success": True,
        "numbers": numbers,
        "confidence": None,
        "category": "other",
        "reasoning": "ใช้การวิเคราะห์พื้นฐาน (AI ไม่สามารถใช้งานได้)",
        "analyzer_type": "basic",
        "is_insight_ai": False,
        "message": f"วิเคราะห์ด้วยระบบพื้นฐาน - พบ {len(numbers)} เลข",
    })


def _merge_article_numbers(article, numbers, reason):
    """รวมเลขใหม่เข้า numbers_with_reasons (กันซ้ำ เก็บสูงสุด 15 เลข)."""
    existing = {item.get("number") for item in article.get_numbers_with_reasons()}
    merged = list(article.get_numbers_with_reasons())
    for num in numbers:
        if num not in existing:
            merged.append({"number": num, "reason": reason})
            existing.add(num)
    article.numbers_with_reasons = merged[:15]


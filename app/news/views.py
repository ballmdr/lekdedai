from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
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
    
    # เตรียมข้อมูลการวิเคราะห์ (ใช้ Gemini AI ก่อน ถ้าไม่มีค่อยใช้ News Analyzer)
    insight_analysis = None
    
    if article.insight_entities:
        # ใช้ข้อมูลจาก Gemini AI
        numbers = [entity['value'] for entity in article.insight_entities]
        avg_score = sum(entity['significance_score'] for entity in article.insight_entities) / len(article.insight_entities) if article.insight_entities else 0
        
        insight_analysis = {
            'numbers': numbers,
            'confidence': round(avg_score * 100, 1),
            'story_summary': article.insight_summary or f'วิเคราะห์ด้วย Gemini AI พบ {len(numbers)} เลข',
            'story_impact_score': round(avg_score * 100, 1),
            'category': 'Gemini AI',
            'is_insight_ai': True,  # แสดงว่าเป็น Gemini AI
            'extracted_entities': article.insight_entities  # ส่งข้อมูลรายละเอียดไป JavaScript
        }
        
    elif article.extracted_numbers:
        # ใช้ข้อมูลจาก News Analyzer (fallback)
        numbers = [num.strip() for num in article.extracted_numbers.split(',') if num.strip()]
        
        insight_analysis = {
            'numbers': numbers,
            'confidence': article.confidence_score or 0,
            'story_summary': f'วิเคราะห์ด้วย News Analyzer Enhanced พบ {len(numbers)} เลข',
            'story_impact_score': article.confidence_score or 0,
            'category': 'News Analyzer Enhanced',
            'is_insight_ai': False  # แสดงว่าเป็น News Analyzer
        }
        
        # อัพเดตเลขหลักถ้ายังไม่มี
        if not article.extracted_numbers and article.insight_entities:
            numbers = [entity['number'] for entity in article.insight_entities]
            avg_score = sum(entity['significance_score'] for entity in article.insight_entities) / len(article.insight_entities) if article.insight_entities else 0
            article.extracted_numbers = ', '.join(numbers[:10])
            article.confidence_score = avg_score * 100
            article.save(update_fields=['extracted_numbers', 'confidence_score'])
    
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

@csrf_exempt
@require_POST
def analyze_news(request, article_id):
    """API วิเคราะห์เลขจากข่าว"""
    
    # Debug info (remove in production)
    # print(f"DEBUG: analyze_news called for article_id: {article_id}")
    # print(f"DEBUG: user authenticated: {request.user.is_authenticated}")
    # print(f"DEBUG: user is staff: {request.user.is_staff}")
    
    # เอาการตรวจสอบสิทธิ์ออก - ให้ทุกคนใช้ได้
    # if not request.user.is_staff:
    #     return JsonResponse({
    #         'success': False,
    #         'error': 'ไม่มีสิทธิ์ในการวิเคราะห์'
    #     }, status=403)
    
    article = get_object_or_404(NewsArticle, id=article_id)
    
    try:
        # ใช้ News Analyzer ปรับปรุงใหม่แทน Insight-AI
        from .news_analyzer import NewsAnalyzer
        from types import SimpleNamespace
        
        # สร้าง mock article object สำหรับ analyzer
        mock_article = SimpleNamespace()
        mock_article.title = article.title
        mock_article.content = article.content
        
        # วิเคราะห์ด้วย News Analyzer ใหม่
        analyzer = NewsAnalyzer()
        analysis_result = analyzer.analyze_article(mock_article)
        
        # อัพเดตข้อมูลในบทความ
        article.extracted_numbers = ','.join(analysis_result['numbers'][:15])
        article.confidence_score = analysis_result['confidence']
        article.save()
        
        return JsonResponse({
            'success': True,
            'numbers': analysis_result['numbers'][:15],
            'confidence': analysis_result['confidence'],
            'category': analysis_result['category'],
            'basic_numbers': analysis_result.get('basic_numbers', []),
            'advanced_numbers': analysis_result.get('advanced_numbers', []),
            'advanced_analysis': analysis_result.get('advanced_analysis', {}),
            'is_insight_ai': False,  # แสดงว่าเป็น News Analyzer
            'message': f'วิเคราะห์ด้วย News Analyzer ใหม่สำเร็จ - พบ {len(analysis_result["numbers"])} เลข'
        })
        
        # Fallback: ใช้ NewsAnalyzer เดิม
        # print(f"DEBUG: Using fallback NewsAnalyzer for article {article_id}")
        analyzer = NewsAnalyzer()
        result = analyzer.analyze_article(article)
        # print(f"DEBUG: NewsAnalyzer result: {result}")
        
        # อัพเดตเลขในบทความ
        article.extracted_numbers = ', '.join(result['numbers'])
        article.confidence_score = result['confidence']
        article.save()
        
        return JsonResponse({
            'success': True,
            'numbers': result['numbers'],
            'confidence': result['confidence'],
            'keywords': result['keywords'],
            'is_insight_ai': False,
            'message': 'วิเคราะห์เสร็จแล้ว (Traditional method)'
        })
        
    except Exception as e:
        # print(f"DEBUG: Exception in analyze_news: {str(e)}")
        # import traceback
        # traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'เกิดข้อผิดพลาดในการวิเคราะห์: {str(e)}'
        }, status=500)

def insight_ai_analysis(request, article_id):
    """API วิเคราะห์ข่าวด้วย Insight-AI และเก็บผลลัพธ์"""
    article = get_object_or_404(NewsArticle, id=article_id)
    
    try:
        # Import Insight-AI using absolute path
        import sys
        from django.utils import timezone
        sys.path.insert(0, '/app/mcp_dream_analysis')
        from specialized_django_integration import extract_news_numbers_for_django
        
        # วิเคราะห์ข่าว
        result = extract_news_numbers_for_django(article.content)
        
        if result and 'extracted_entities' in result:
            # เก็บผลลัพธ์ลงฐานข้อมูล
            article.insight_summary = result.get('story_summary', '')
            article.insight_impact_score = result.get('story_impact_score', 0)
            article.insight_entities = result.get('extracted_entities', [])
            article.insight_analyzed_at = timezone.now()
            
            # อัพเดตเลขในบทความด้วยถ้ายังไม่มี
            if not article.extracted_numbers or article.extracted_numbers.strip() == "":
                numbers = [entity['value'] for entity in result['extracted_entities']]
                avg_score = sum(entity['significance_score'] for entity in result['extracted_entities']) / len(result['extracted_entities']) if result['extracted_entities'] else 0
                article.extracted_numbers = ', '.join(numbers[:10])
                article.confidence_score = avg_score * 100
            
            article.save()
            
            # ส่งกลับผลลัพธ์เป็น JSON
            return JsonResponse({
                'success': True,
                'story_summary': result.get('story_summary', 'ไม่สามารถสรุปได้'),
                'story_impact_score': round(result.get('story_impact_score', 0) * 100, 1),
                'extracted_entities': result.get('extracted_entities', []),
                'numbers': [entity['value'] for entity in result.get('extracted_entities', [])],
                'confidence': round(sum(entity['significance_score'] for entity in result['extracted_entities']) / len(result['extracted_entities']) * 100, 1) if result.get('extracted_entities') else 0,
                'is_insight_ai': True,
                'saved': True
            })
        else:
            raise Exception("No valid result from Insight-AI analysis")
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'เกิดข้อผิดพลาด: {str(e)}',
            'story_summary': 'ไม่สามารถวิเคราะห์ได้',
            'story_impact_score': 0,
            'extracted_entities': [],
            'saved': False
        })
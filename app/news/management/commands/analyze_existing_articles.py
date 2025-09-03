import os
import sys
from django.core.management.base import BaseCommand
from django.utils import timezone
from news.models import NewsArticle

class Command(BaseCommand):
    help = 'Run Insight-AI analysis on existing articles that don\'t have analysis data'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, help='Limit number of articles to analyze', default=None)
        parser.add_argument('--force', action='store_true', help='Re-analyze articles that already have analysis')

    def analyze_with_insight_ai(self, article_content):
        """วิเคราะห์ข่าวด้วย Insight-AI"""
        try:
            # Import Insight-AI using absolute path
            sys.path.insert(0, '/app/mcp_dream_analysis')
            from specialized_django_integration import extract_news_numbers_for_django
            
            # ใช้ Insight-AI วิเคราะห์
            result = extract_news_numbers_for_django(article_content)
            
            if result and 'extracted_entities' in result:
                return {
                    'summary': result.get('story_summary', ''),
                    'impact_score': result.get('story_impact_score', 0),
                    'entities': result.get('extracted_entities', [])
                }
            return None
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Insight-AI analysis failed: {str(e)}'))
            return None

    def handle(self, *args, **options):
        # หาบทความที่ยังไม่มีข้อมูล Insight-AI
        if options.get('force'):
            articles = NewsArticle.objects.filter(status='published')
            self.stdout.write(f'Found {articles.count()} published articles (force mode)')
        else:
            articles = NewsArticle.objects.filter(
                status='published',
                insight_analyzed_at__isnull=True
            )
            self.stdout.write(f'Found {articles.count()} articles without Insight-AI analysis')

        if options.get('limit'):
            articles = articles[:options['limit']]
            self.stdout.write(f'Limited to {options["limit"]} articles')

        analyzed_count = 0
        failed_count = 0

        for article in articles:
            try:
                self.stdout.write(f'Analyzing: {article.title[:50]}...')
                
                # วิเคราะห์ด้วย Insight-AI
                insight_result = self.analyze_with_insight_ai(article.content)
                
                if insight_result:
                    # บันทึกผลลัพธ์
                    article.insight_summary = insight_result['summary']
                    article.insight_impact_score = insight_result['impact_score']
                    article.insight_entities = insight_result['entities']
                    article.insight_analyzed_at = timezone.now()
                    
                    # อัพเดตเลขในบทความด้วยถ้ายังไม่มี
                    if not article.extracted_numbers or article.extracted_numbers.strip() == "":
                        numbers = [entity['value'] for entity in insight_result['entities']]
                        avg_score = sum(entity['significance_score'] for entity in insight_result['entities']) / len(insight_result['entities']) if insight_result['entities'] else 0
                        article.extracted_numbers = ', '.join(numbers[:10])
                        article.confidence_score = avg_score * 100
                    
                    article.save()
                    analyzed_count += 1
                    
                    self.stdout.write(self.style.SUCCESS(f'✅ Success: Found {len(insight_result["entities"])} entities'))
                else:
                    failed_count += 1
                    self.stdout.write(self.style.ERROR('❌ Failed: No analysis result'))
                    
            except Exception as e:
                failed_count += 1
                self.stdout.write(self.style.ERROR(f'❌ Error analyzing article {article.id}: {str(e)}'))

        self.stdout.write(self.style.SUCCESS(f'\n🎯 Analysis complete!'))
        self.stdout.write(self.style.SUCCESS(f'✅ Successfully analyzed: {analyzed_count}'))
        self.stdout.write(self.style.WARNING(f'❌ Failed: {failed_count}'))
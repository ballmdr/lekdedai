import json
import os
import sys
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from news.models import NewsArticle, NewsCategory

class Command(BaseCommand):
    help = 'Imports news articles from a JSON file scraped from news sites.'

    def add_arguments(self, parser):
        parser.add_argument('json_file_path', type=str, help='The path to the JSON file to import.')
        parser.add_argument('--no-insight', action='store_true', help='Skip Insight-AI analysis')

    def analyze_with_insight_ai(self, article_title, article_content):
        """วิเคราะห์ข่าวด้วย Insight-AI"""
        try:
            # Import Insight-AI
            sys.path.append('/app/mcp_dream_analysis/models')
            from insight_ai_news_analyzer import analyze_news_for_django
            
            # วิเคราะห์ข่าว
            full_text = f"{article_title} {article_content}"
            result = analyze_news_for_django(full_text)
            
            return {
                'summary': result.get('story_summary', ''),
                'impact_score': result.get('story_impact_score', 0),
                'entities': result.get('extracted_entities', [])
            }
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Insight-AI analysis failed: {str(e)}'))
            return None

    def handle(self, *args, **options):
        json_file_path = options['json_file_path']

        if not os.path.exists(json_file_path):
            raise CommandError(f"File not found at: {json_file_path}")

        with open(json_file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                raise CommandError("Invalid JSON format.")

        if not isinstance(data, list):
            raise CommandError("JSON file should contain a list of articles.")

        # Get or create a default category for scraped news
        category, created = NewsCategory.objects.get_or_create(
            name='ข่าวจากเว็บ',
            defaults={'slug': 'scraped-news'}
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created default category "ข่าวจากเว็บ"'))

        imported_count = 0
        skipped_count = 0
        skip_insight = options.get('no_insight', False)

        for article_data in data:
            url = article_data.get('url')
            if not url:
                self.stdout.write(self.style.WARNING(f"Skipping article with no URL: {article_data.get('title', 'N/A')[:30]}..."))
                skipped_count += 1
                continue

            # Avoid duplicates by checking the source URL
            if NewsArticle.objects.filter(source_url=url).exists():
                self.stdout.write(self.style.NOTICE(f"Skipping existing article: {url}"))
                skipped_count += 1
                continue

            try:
                # ใช้เนื้อหาจาก JSON หรือ placeholder หากไม่มี
                content = article_data.get('content', f"เนื้อหาข่าวจาก {url}")
                if not content or content.strip() == "":
                    content = f"เนื้อหาข่าวจาก {url}"
                
                article = NewsArticle(
                    title=article_data['title'],
                    source_url=url,
                    category=category,
                    status='draft',  # Import as draft to be reviewed later
                    intro=article_data.get('title'),
                    content=content,
                    extracted_numbers=','.join(article_data.get('extracted_numbers', [])),
                )
                
                # วิเคราะห์ด้วย Insight-AI (ถ้าไม่ skip)
                if not skip_insight:
                    insight_result = self.analyze_with_insight_ai(article.title, article.content)
                    if insight_result:
                        article.insight_summary = insight_result['summary']
                        article.insight_impact_score = insight_result['impact_score']
                        article.insight_entities = insight_result['entities']
                        article.insight_analyzed_at = timezone.now()
                        self.stdout.write(self.style.SUCCESS(f"🧠 Insight-AI analyzed: {len(insight_result['entities'])} entities found"))
                
                article.save()  # Slug will be generated automatically
                imported_count += 1
                self.stdout.write(self.style.SUCCESS(f"Successfully imported: {article.title}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error importing article {url}: {e}"))
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(f"\nImport complete. Imported: {imported_count}, Skipped: {skipped_count}"))
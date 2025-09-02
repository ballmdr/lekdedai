import json
import os
from django.core.management.base import BaseCommand, CommandError
from news.models import NewsArticle, NewsCategory

class Command(BaseCommand):
    help = 'Imports news articles from a JSON file scraped from news sites.'

    def add_arguments(self, parser):
        parser.add_argument('json_file_path', type=str, help='The path to the JSON file to import.')

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
                article.save()  # Slug will be generated automatically
                imported_count += 1
                self.stdout.write(self.style.SUCCESS(f"Successfully imported: {article.title}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error importing article {url}: {e}"))
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(f"\nImport complete. Imported: {imported_count}, Skipped: {skipped_count}"))
#!/usr/bin/env python
import os
import sys
import django
import json
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lekdedai.settings')
django.setup()

from news.models import NewsArticle, NewsCategory
from django.utils.text import slugify

def import_news_from_json():
    """Import news data from JSON files"""
    json_files = [
        'thairath_news_20250829_082004.json',
        'thairath_news_20250829_082158.json',
        'thairath_news_20250829_082310.json',
        'thairath_news_20250829_082716.json',
        'thairath_news_20250829_082746.json',
        'thairath_news_20250829_092125.json',
        'thairath_news_20250829_092406.json',
        'thairath_news_20250829_092501.json',
    ]
    
    # Get or create default category
    category, created = NewsCategory.objects.get_or_create(
        name='ข่าวทั่วไป',
        defaults={'slug': 'general-news'}
    )
    
    total_imported = 0
    
    for json_file in json_files:
        if not os.path.exists(json_file):
            print(f"File not found: {json_file}")
            continue
            
        print(f"Importing from {json_file}...")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            news_data = json.load(f)
        
        for item in news_data:
            try:
                # Create slug from title
                slug = slugify(item['title'][:50])  # Limit to 50 chars
                
                # Check if article already exists
                if NewsArticle.objects.filter(title=item['title']).exists():
                    print(f"Article already exists: {item['title'][:50]}...")
                    continue
                
                # Extract numbers from the item
                numbers = item.get('numbers', [])
                extracted_numbers = ','.join(numbers) if numbers else ''
                
                # Create news article
                article = NewsArticle.objects.create(
                    title=item['title'],
                    slug=slug,
                    intro=f"ข่าวจาก {item.get('source', 'thairath')}",
                    content=f"ข่าวจาก {item.get('source', 'thairath')}: {item['title']}",
                    category=category,
                    source_url=item.get('url', ''),
                    extracted_numbers=extracted_numbers,
                    status='published',
                    published_date=datetime.fromisoformat(item['scraped_at'].replace('Z', '+00:00')),
                )
                
                total_imported += 1
                print(f"Imported: {item['title'][:50]}...")
                
            except Exception as e:
                print(f"Error importing article: {e}")
                continue
    
    print(f"\nTotal imported: {total_imported} articles")

if __name__ == '__main__':
    import_news_from_json()

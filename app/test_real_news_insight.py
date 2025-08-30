#!/usr/bin/env python3
"""
Test Insight-AI with Real News Article
"""
import sys
import os
import django

# Add MCP path
sys.path.insert(0, "/app/mcp_dream_analysis")

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lekdedai.settings')
django.setup()

from specialized_django_integration import extract_news_numbers_for_django
from news.models import NewsArticle

def test_real_news():
    """Test Insight-AI with real news articles"""
    
    print("🔍 Testing Insight-AI with Real News Articles...")
    print("=" * 60)
    
    # Get first few articles
    articles = NewsArticle.objects.all()[:3]
    
    for i, article in enumerate(articles, 1):
        print(f"\n📰 Article {i}: {article.title}")
        print("-" * 50)
        print(f"Content preview: {article.content[:150]}...")
        
        try:
            # Test Insight-AI
            result = extract_news_numbers_for_django(article.content)
            
            if result:
                print("\n✅ Insight-AI Results:")
                
                # Story impact score
                story_impact = result.get('story_impact_score', 0)
                print(f"📊 Story Impact: {story_impact:.2f} ({story_impact*100:.1f}%)")
                
                # Extracted entities
                entities = result.get('extracted_entities', [])
                print(f"🔢 Numbers Found: {len(entities)}")
                
                if entities:
                    print("Top 5 Numbers:")
                    for j, entity in enumerate(entities[:5], 1):
                        print(f"  {j}. {entity['value']:>8s} ({entity['entity_type']}) - {entity['significance_score']*100:.1f}%")
                        print(f"     {entity['reasoning']}")
                else:
                    print("  No significant numbers found")
                    
            else:
                print("❌ No results")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    test_real_news()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
สคริปต์ทดลองดึงข่าวจากไทยรัฐ
"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import json

class ThairathScraper:
    """คลาสสำหรับดึงข่าวจากไทยรัฐ"""
    
    def __init__(self):
        self.base_url = "https://www.thairath.co.th"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def get_latest_news(self, url):
        """ดึงข่าวล่าสุดจาก URL ที่กำหนด"""
        try:
            print(f"กำลังดึงข้อมูลจาก: {url}")
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # หาข้อมูลข่าว
            news_items = []
            
            # หา headline ข่าวหลัก
            headlines = soup.find_all('h3', class_='css-1xyd7f1')
            for headline in headlines[:10]:  # เอาแค่ 10 ข่าวแรก
                news_item = self.extract_news_item(headline)
                if news_item:
                    news_items.append(news_item)
            
            # หาข่าวทั่วไป
            news_links = soup.find_all('a', href=re.compile(r'/news/'))
            for link in news_links[:20]:  # เอาแค่ 20 ลิงก์แรก
                if len(news_items) >= 15:  # จำกัดจำนวนข่าว
                    break
                    
                news_item = self.extract_news_from_link(link)
                if news_item and news_item not in news_items:
                    news_items.append(news_item)
            
            return news_items
            
        except requests.RequestException as e:
            print(f"เกิดข้อผิดพลาดในการดึงข้อมูล: {e}")
            return []
        except Exception as e:
            print(f"เกิดข้อผิดพลาดที่ไม่คาดคิด: {e}")
            return []
    
    def extract_news_item(self, element):
        """แยกข้อมูลข่าวจาก element"""
        try:
            # หา link
            link_elem = element.find('a')
            if not link_elem:
                return None
                
            title = link_elem.get_text(strip=True)
            if not title:
                return None
                
            href = link_elem.get('href')
            if href and not href.startswith('http'):
                href = self.base_url + href
            
            # หาเลขจากหัวข้อข่าว
            numbers = self.extract_numbers_from_text(title)
            
            return {
                'title': title,
                'url': href,
                'extracted_numbers': numbers,
                'source': 'thairath',
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการแยกข้อมูล: {e}")
            return None
    
    def extract_news_from_link(self, link_elem):
        """แยกข้อมูลข่าวจากลิงก์"""
        try:
            title = link_elem.get_text(strip=True)
            if not title or len(title) < 10:  # กรองหัวข้อที่สั้นเกินไป
                return None
                
            href = link_elem.get('href')
            if href and not href.startswith('http'):
                href = self.base_url + href
            
            # หาเลขจากหัวข้อข่าว
            numbers = self.extract_numbers_from_text(title)
            
            return {
                'title': title,
                'url': href,
                'extracted_numbers': numbers,
                'source': 'thairath',
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            return None
    
    def extract_numbers_from_text(self, text):
        """หาเลขจากข้อความ"""
        numbers = []
        
        # หาเลข 2-3 หลัก
        number_patterns = re.findall(r'\b\d{2,3}\b', text)
        
        # กรองเลขที่น่าสนใจ
        for num in number_patterns:
            if len(num) == 2:
                numbers.append(num)
            elif len(num) == 3:
                # แยกเลข 3 หลักเป็นเลข 2 หลัก
                numbers.append(num[:2])
                numbers.append(num[1:])
                numbers.append(num)
        
        # ลบเลขซ้ำและจำกัดจำนวน
        unique_numbers = list(dict.fromkeys(numbers))[:10]
        return unique_numbers
    
    def get_news_detail(self, url):
        """ดึงรายละเอียดข่าวจาก URL"""
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # หาเนื้อหาข่าว
            content_elem = soup.find('div', class_='css-1shj5k7')
            if content_elem:
                content = content_elem.get_text(strip=True)
            else:
                content = ""
            
            # หาเลขจากเนื้อหา
            numbers = self.extract_numbers_from_text(content)
            
            return {
                'content': content[:500] + "..." if len(content) > 500 else content,
                'extracted_numbers': numbers,
                'full_url': url
            }
            
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการดึงรายละเอียด: {e}")
            return None

def main():
    """ฟังก์ชันหลัก"""
    print("=" * 60)
    print("ทดลองดึงข่าวจากไทยรัฐ")
    print("=" * 60)
    
    scraper = ThairathScraper()
    
    # ดึงข่าวล่าสุด
    url = "https://www.thairath.co.th/news/local/all-latest"
    news_items = scraper.get_latest_news(url)
    
    if not news_items:
        print("ไม่สามารถดึงข่าวได้")
        return
    
    print(f"\nพบข่าวทั้งหมด: {len(news_items)} ข่าว")
    print("-" * 60)
    
    # แสดงผลข่าว
    for i, news in enumerate(news_items, 1):
        print(f"{i:2d}. {news['title']}")
        if news['extracted_numbers']:
            print(f"    เลขที่ได้: {', '.join(news['extracted_numbers'])}")
        print(f"    URL: {news['url']}")
        print()
    
    # ทดลองดึงรายละเอียดข่าวแรก
    if news_items:
        print("=" * 60)
        print("ทดลองดึงรายละเอียดข่าวแรก:")
        print("=" * 60)
        
        first_news = news_items[0]
        detail = scraper.get_news_detail(first_news['url'])
        
        if detail:
            print(f"หัวข้อ: {first_news['title']}")
            print(f"เนื้อหา: {detail['content']}")
            print(f"เลขที่ได้จากเนื้อหา: {', '.join(detail['extracted_numbers'])}")
        else:
            print("ไม่สามารถดึงรายละเอียดได้")
    
    # บันทึกผลลัพธ์เป็น JSON
    output_file = "thairath_news.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(news_items, f, ensure_ascii=False, indent=2)
    
    print(f"\nบันทึกผลลัพธ์ลงไฟล์: {output_file}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
สคริปต์สำหรับดึงข่าวจากหลายแหล่ง (Thairath, Daily News, Khao Sod)
"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import json
import sys
import feedparser
from abc import ABC, abstractmethod

class BaseScraper(ABC):
    """
    คลาสแม่สำหรับ Scraper แต่ละเว็บ
    """
    def __init__(self, source_name, base_url):
        self.source_name = source_name
        self.base_url = base_url
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'en-US,en;q=0.9,th;q=0.8',
            'Referer': 'https://www.google.com/'
        }
        self.news_items = []

    def get_page(self, url):
        """ดึงข้อมูลหน้าเว็บ"""
        try:
            print(f"[{self.source_name}] กำลังดึงข้อมูลจาก: {url}")
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return BeautifulSoup(response.text, 'html.parser')
        except requests.RequestException as e:
            print(f"[{self.source_name}] เกิดข้อผิดพลาดในการดึงข้อมูล: {e}")
            return None

    def extract_numbers_from_text(self, text):
        """หาเลข 2-3 หลักจากข้อความ"""
        numbers = []
        # ใช้ \b เพื่อให้มั่นใจว่าเป็นคำที่แยกออกมา (whole word)
        number_patterns = re.findall(r'\b\d{2,3}\b', text)
        for num in number_patterns:
            numbers.append(num)
        return list(dict.fromkeys(numbers))[:10]

    def save_to_json(self):
        """บันทึกข้อมูลเป็น JSON"""
        output_file = f"{self.source_name.lower()}_news.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.news_items, f, ensure_ascii=False, indent=2)
        print(f"\n[{self.source_name}] บันทึกผลลัพธ์ลงไฟล์: {output_file}")

    def get_article_content(self, article_url):
        """ดึงเนื้อหาข่าวจาก URL"""
        try:
            print(f"  -> กำลังดึงเนื้อหาจาก: {article_url[:80]}...")
            soup = self.get_page(article_url)
            if not soup:
                return "ไม่สามารถดึงเนื้อหาได้"
            
            # ลองหา content จาก selector ทั่วไป
            content_selectors = [
                'div.content', 'div.article-content', 'div.news-content',
                'div[class*="content"]', 'div[class*="article"]', 
                'div[class*="story"]', 'div[class*="body"]',
                'article', '.entry-content', '.post-content'
            ]
            
            content = ""
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    # เอาข้อความจากทุก paragraph
                    paragraphs = elements[0].find_all(['p', 'div'])
                    if paragraphs:
                        content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                        break
            
            # ถ้าไม่เจอ ใช้วิธีสำรอง
            if not content:
                # หาจาก p tags ทั่วไป
                paragraphs = soup.find_all('p')
                if paragraphs:
                    content = ' '.join([p.get_text(strip=True) for p in paragraphs[:10] if p.get_text(strip=True)])
            
            # ทำความสะอาด
            content = re.sub(r'\s+', ' ', content)
            content = content.strip()
            
            return content[:2000] if content else "ไม่สามารถดึงเนื้อหาได้"
            
        except Exception as e:
            print(f"    ข้อผิดพลาดในการดึงเนื้อหา: {e}")
            return "เกิดข้อผิดพลาดในการดึงเนื้อหา"

    @abstractmethod
    def scrape(self):
        """เมธอดหลักในการดึงข้อมูล (ต้อง implement ในคลาสลูก)"""
        pass

class ThairathScraper(BaseScraper):
    """คลาสสำหรับดึงข่าวจากไทยรัฐ"""
    def __init__(self):
        super().__init__("Thairath", "https://www.thairath.co.th")

    def scrape(self):
        url = "https://www.thairath.co.th/news/local/all-latest"
        soup = self.get_page(url)
        if not soup:
            return

        processed_urls = set()
        headline_selectors = [
            'h3.css-1xyd7f1',
            'h3',
            '.css-1xyd7f1',
            'a[href*="/news/"]'
        ]

        for selector in headline_selectors:
            elements = soup.select(selector)
            for elem in elements:
                link_elem = None
                if elem.name == 'a':
                    link_elem = elem
                else:
                    link_elem = elem.find('a')

                if link_elem:
                    href = link_elem.get('href')
                    title = link_elem.get_text(strip=True)

                    if title and href and len(title) > 10 and href not in processed_urls:
                        # แก้ไข URL ให้ถูกต้อง
                        if href.startswith('/'):
                            full_url = self.base_url + href
                        elif href.startswith('//'):
                            full_url = 'https:' + href
                        elif not href.startswith('http'):
                            full_url = self.base_url + '/' + href
                        else:
                            full_url = href
                        
                        # แก้ไข bug URL ที่เสีย
                        full_url = full_url.replace('co.thnews', 'co.th/news')
                        
                        processed_urls.add(href)
                        
                        # ดึงเนื้อหาข่าว
                        content = self.get_article_content(full_url)
                        full_text = f"{title} {content}"
                        
                        self.news_items.append({
                            'title': title,
                            'content': content,
                            'url': full_url,
                            'extracted_numbers': self.extract_numbers_from_text(full_text),
                            'source': self.source_name,
                            'scraped_at': datetime.now().isoformat()
                        })
            if self.news_items: # If news items are found with a selector, break
                break

        print(f"[{self.source_name}] พบข่าวทั้งหมด: {len(self.news_items)} ข่าว")

class DailyNewsScraper(BaseScraper):
    """คลาสสำหรับดึงข่าวจากเดลินิวส์"""
    def __init__(self):
        super().__init__("DailyNews", "https://www.dailynews.co.th")

    def scrape(self):
        # NOTE: URL และ selector อาจจะต้องมีการปรับเปลี่ยนตามโครงสร้างเว็บจริง
        url = "https://www.dailynews.co.th/news/"
        soup = self.get_page(url)
        if not soup:
            return

        processed_urls = set()
        # NOTE: 'article' และ 'h3' เป็นการคาดเดา selector ที่พบบ่อย
        articles = soup.find_all('article', limit=20)
        for article in articles:
            link_elem = article.find('h3')
            if link_elem and link_elem.find('a'):
                link_elem = link_elem.find('a')
                href = link_elem.get('href')
                if href and href not in processed_urls:
                    title = link_elem.get_text(strip=True)
                    if title:
                        processed_urls.add(href)
                        
                        # ดึงเนื้อหาข่าว
                        content = self.get_article_content(href)
                        full_text = f"{title} {content}"
                        
                        self.news_items.append({
                            'title': title,
                            'content': content,
                            'url': href, # DailyNews มักใช้ full URL
                            'extracted_numbers': self.extract_numbers_from_text(full_text),
                            'source': self.source_name,
                            'scraped_at': datetime.now().isoformat()
                        })
        
        print(f"[{self.source_name}] พบข่าวทั้งหมด: {len(self.news_items)} ข่าว")

class KhaosodScraper(BaseScraper):
    """คลาสสำหรับดึงข่าวจากข่าวสดผ่าน RSS Feed"""
    def __init__(self):
        super().__init__("Khaosod", "https://www.khaosod.co.th")

    def scrape(self):
        # ใช้ RSS Feed ของหมวดการเมือง เนื่องจากหน้าเว็บหลักมีระบบป้องกัน
        url = "https://www.khaosod.co.th/politics/feed"
        print(f"[{self.source_name}] กำลังดึงข้อมูลจาก RSS Feed: {url}")
        
        feed = feedparser.parse(url)
        
        if feed.bozo:
            print(f"[{self.source_name}] เกิดข้อผิดพลาดในการอ่าน Feed: {feed.bozo_exception}")
            return

        for entry in feed.entries[:20]: # เอาแค่ 20 ข่าวล่าสุด
            title = entry.title
            link = entry.link
            
            # ดึงเนื้อหาข่าว
            content = self.get_article_content(link)
            full_text = f"{title} {content}"
            
            self.news_items.append({
                'title': title,
                'content': content,
                'url': link,
                'extracted_numbers': self.extract_numbers_from_text(full_text),
                'source': self.source_name,
                'scraped_at': datetime.now().isoformat()
            })

        print(f"[{self.source_name}] พบข่าวทั้งหมด: {len(self.news_items)} ข่าว")


def main():
    """ฟังก์ชันหลักในการเลือกและรัน Scraper"""
    scrapers = {
        "thairath": ThairathScraper,
        "dailynews": DailyNewsScraper,
        "khaosod": KhaosodScraper,
    }

    if len(sys.argv) < 2 or sys.argv[1] not in scrapers:
        print("กรุณาระบุแหล่งข่าวที่ต้องการดึงข้อมูล:")
        print(f"Usage: python {sys.argv[0]} [{'|'.join(scrapers.keys())}]")
        sys.exit(1)

    source_to_scrape = sys.argv[1]
    print("=" * 60)
    print(f"เริ่มต้นดึงข่าวจาก: {source_to_scrape.capitalize()}")
    print("=" * 60)

    scraper_class = scrapers[source_to_scrape]
    scraper_instance = scraper_class()
    scraper_instance.scrape()
    scraper_instance.save_to_json()

if __name__ == "__main__":
    main()
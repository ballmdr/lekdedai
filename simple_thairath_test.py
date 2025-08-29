#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
สคริปต์ทดลองง่ายๆ สำหรับดึงข่าวจากไทยรัฐ
"""

import requests
from bs4 import BeautifulSoup
import re
import json

def test_thairath_scraping():
    """ทดลองดึงข่าวจากไทยรัฐ"""
    
    print("=" * 60)
    print("ทดลองดึงข่าวจากไทยรัฐ")
    print("=" * 60)
    
    url = "https://www.thairath.co.th/news/local/all-latest"
    
    # Headers เพื่อจำลอง browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        print(f"กำลังดึงข้อมูลจาก: {url}")
        
        # ดึงข้อมูลจากเว็บ
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        print(f"สถานะการตอบสนอง: {response.status_code}")
        print(f"ขนาดข้อมูล: {len(response.text)} ตัวอักษร")
        
        # แยกข้อมูลด้วย BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # หาข้อมูลข่าว
        news_items = []
        
        # หา headline ข่าวหลัก (ลองหลาย class)
        headline_selectors = [
            'h3.css-1xyd7f1',
            'h3',
            '.css-1xyd7f1',
            'a[href*="/news/"]'
        ]
        
        for selector in headline_selectors:
            elements = soup.select(selector)
            print(f"พบ elements ด้วย selector '{selector}': {len(elements)} รายการ")
            
            if elements:
                for i, elem in enumerate(elements[:5]):  # เอาแค่ 5 รายการแรก
                    try:
                        # หา link และ title
                        if elem.name == 'a':
                            link_elem = elem
                        else:
                            link_elem = elem.find('a')
                        
                        if link_elem:
                            title = link_elem.get_text(strip=True)
                            href = link_elem.get('href')
                            
                            if title and href and len(title) > 10:
                                # สร้าง URL เต็ม
                                if href.startswith('/'):
                                    full_url = f"https://www.thairath.co.th{href}"
                                elif href.startswith('http'):
                                    full_url = href
                                else:
                                    full_url = f"https://www.thairath.co.th/{href}"
                                
                                # หาเลขจากหัวข้อ
                                numbers = re.findall(r'\b\d{2,3}\b', title)
                                
                                news_item = {
                                    'title': title,
                                    'url': full_url,
                                    'numbers': numbers,
                                    'selector_used': selector
                                }
                                
                                if news_item not in news_items:
                                    news_items.append(news_item)
                                    print(f"  {i+1}. {title[:50]}...")
                                    if numbers:
                                        print(f"     เลขที่ได้: {', '.join(numbers)}")
                    except Exception as e:
                        continue
                
                if news_items:
                    break  # ถ้าได้ข้อมูลแล้วให้หยุด
        
        # แสดงผลลัพธ์
        print(f"\nพบข่าวทั้งหมด: {len(news_items)} ข่าว")
        print("-" * 60)
        
        for i, news in enumerate(news_items, 1):
            print(f"{i:2d}. {news['title']}")
            print(f"    URL: {news['url']}")
            if news['numbers']:
                print(f"    เลขที่ได้: {', '.join(news['numbers'])}")
            print(f"    ใช้ selector: {news['selector_used']}")
            print()
        
        # บันทึกผลลัพธ์
        if news_items:
            output_file = "thairath_test_results.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(news_items, f, ensure_ascii=False, indent=2)
            print(f"บันทึกผลลัพธ์ลงไฟล์: {output_file}")
        
        # ทดลองดึงรายละเอียดข่าวแรก
        if news_items:
            print("=" * 60)
            print("ทดลองดึงรายละเอียดข่าวแรก:")
            print("=" * 60)
            
            first_news = news_items[0]
            print(f"หัวข้อ: {first_news['title']}")
            print(f"URL: {first_news['url']}")
            
            try:
                detail_response = requests.get(first_news['url'], headers=headers, timeout=30)
                if detail_response.status_code == 200:
                    detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
                    
                    # หาเนื้อหาข่าว
                    content_selectors = [
                        '.css-1shj5k7',
                        '.article-content',
                        '.content',
                        'p'
                    ]
                    
                    content = ""
                    for selector in content_selectors:
                        content_elem = detail_soup.select_one(selector)
                        if content_elem:
                            content = content_elem.get_text(strip=True)
                            print(f"ใช้ selector: {selector}")
                            break
                    
                    if content:
                        print(f"เนื้อหา (500 ตัวอักษรแรก): {content[:500]}...")
                        
                        # หาเลขจากเนื้อหา
                        content_numbers = re.findall(r'\b\d{2,3}\b', content)
                        if content_numbers:
                            print(f"เลขที่ได้จากเนื้อหา: {', '.join(content_numbers[:10])}")
                    else:
                        print("ไม่พบเนื้อหาข่าว")
                        
                else:
                    print(f"ไม่สามารถดึงรายละเอียดได้: {detail_response.status_code}")
                    
            except Exception as e:
                print(f"เกิดข้อผิดพลาดในการดึงรายละเอียด: {e}")
        
    except requests.RequestException as e:
        print(f"เกิดข้อผิดพลาดในการดึงข้อมูล: {e}")
    except Exception as e:
        print(f"เกิดข้อผิดพลาดที่ไม่คาดคิด: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_thairath_scraping()

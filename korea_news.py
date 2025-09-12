# korean_news_to_drupal.py
import os
import time
import sqlite3
import logging
import base64
import requests
import feedparser
from dotenv import load_dotenv

# Gemini SDK (google-genai)
from google import genai

# ----------------
# Config
# ----------------
FEEDS = [
    "https://www.yna.co.kr/rss/entertainment.xml",              # Yonhap Entertainment
    "https://www.hankyung.com/feed/entertainment",              # Hankyung Entertainment
    "https://www.mk.co.kr/rss/30000023/",                       # MK 문화·연예
    "http://www.yonhapnewstv.co.kr/category/news/culture/feed/" # Yonhap News TV 문화·연예
]

DB_PATH = "seen_articles.db"
SLEEP_SECONDS_BETWEEN_POSTS = 2

# ----------------
# Setup
# ----------------
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
#DRUPAL_BASE_URL = os.getenv("DRUPAL_BASE_URL", "").rstrip("/")
#DRUPAL_USER = os.getenv("DRUPAL_USER")
#DRUPAL_PASS = os.getenv("DRUPAL_PASS")
#DRUPAL_CONTENT_TYPE = os.getenv("DRUPAL_CONTENT_TYPE", "article")  # e.g. 'article'

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

if not GEMINI_API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY in environment variables (.env)")
#if not (DRUPAL_BASE_URL and DRUPAL_USER and DRUPAL_PASS):
#    raise RuntimeError("Missing DRUPAL_* env vars (.env): DRUPAL_BASE_URL, DRUPAL_USER, DRUPAL_PASS")

client = genai.Client()  # ใช้ GEMINI_API_KEY จาก env

# ----------------
# Persistence (SQLite)
# ----------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS seen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            link TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def is_seen(link: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM seen WHERE link = ?", (link,))
    row = cur.fetchone()
    conn.close()
    return row is not None

def mark_seen(link: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute("INSERT OR IGNORE INTO seen (link) VALUES (?)", (link,))
        conn.commit()
    finally:
        conn.close()

# ----------------
# RSS Fetch
# ----------------
def fetch_feed_entries(feed_url: str):
    d = feedparser.parse(feed_url)
    if d.bozo:
        logging.warning(f"Feed parse warning for {feed_url}: {d.bozo_exception}")
    return d.entries or []

# ----------------
# Gemini Summarize & Translate (to Thai)
# ----------------
def summarize_to_thai(title: str, summary: str, content: str, link: str) -> str:
    user_prompt = f"""
คุณคือผู้ช่วยสรุปข่าวบันเทิงเกาหลี ให้สรุปเป็นภาษาไทย กระชับ เข้าใจง่าย:
- ทำ bullet 3-5 จุด (ภาษากระชับ)
- เพิ่ม hashtag 2-3 คำ (#ภาษาอังกฤษหรือเกาหลีได้)
- ปิดท้ายด้วยลิงก์ต้นฉบับ
- จำกัดความยาวรวมประมาณ 300-400 ตัวอักษร

หัวข้อ: {title.strip() if title else ""}
สรุป/คำอธิบาย (ถ้ามี): {summary.strip() if summary else ""}
เนื้อหา (ถ้ามี): {content.strip() if content else ""}
ลิงก์: {link.strip() if link else ""}
"""
    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=user_prompt,
    )
    return (resp.text or "").strip()

# ----------------
# Drupal JSON:API Posting
# ----------------
def _basic_auth_header(user: str, pwd: str) -> str:
    token = base64.b64encode(f"{user}:{pwd}".encode()).decode()
    return f"Basic {token}"

def post_to_drupal_jsonapi(title: str, body_text: str):
    """
    ส่ง POST ไปยัง /jsonapi/node/{bundle} โดยใช้ JSON:API document:
    {
      "data": {
        "type": "node--{bundle}",
        "attributes": {
          "title": "...",
          "body": { "value": "...", "format": "plain_text" }
        }
      }
    }
    """
    url = f"{DRUPAL_BASE_URL}/jsonapi/node/{DRUPAL_CONTENT_TYPE}"
    headers = {
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json",
        "Authorization": _basic_auth_header(DRUPAL_USER, DRUPAL_PASS),
    }
    payload = {
        "data": {
            "type": f"node--{DRUPAL_CONTENT_TYPE}",
            "attributes": {
                "title": title[:255] if title else "Untitled",
                "body": {
                    "value": body_text,
                    "format": "plain_text"
                }
            }
        }
    }
    r = requests.post(url, json=payload, headers=headers, timeout=30)
    if r.status_code not in (200, 201):
        logging.error(f"Drupal post failed: {r.status_code} {r.text}")
    else:
        logging.info("Posted to Drupal JSON:API.")

# ----------------
# Main Workflow
# ----------------
def main():
    init_db()
    for feed in FEEDS:
        logging.info(f"Fetching: {feed}")
        entries = fetch_feed_entries(feed)
        for e in entries:
            link = getattr(e, "link", None) or getattr(e, "id", None)
            if not link:
                continue
            if is_seen(link):
                continue

            title = getattr(e, "title", "")
            summary = getattr(e, "summary", "") or getattr(e, "description", "")
            content = ""
            if hasattr(e, "content") and isinstance(e.content, list) and e.content:
                content = e.content.get("value", "") or ""

            try:
                thai_post = summarize_to_thai(title, summary, content, link)
                if thai_post:
                    # รวมหัวข้อ + สรุปไทย + ลิงก์ (ตัวสรุปมีใส่ลิงก์ไว้แล้ว แต่กันพลาด)
                    body_text = f"{thai_post}\n\nที่มา: {link}"
                    print(title, body_text)
                    #post_to_drupal_jsonapi(title, body_text)
                    mark_seen(link)
                    time.sleep(SLEEP_SECONDS_BETWEEN_POSTS)
            except Exception as ex:
                logging.exception(f"Failed processing entry: {link} - {ex}")

if __name__ == "__main__":
    main()

"""Task 18: category-page scraper (fallback เมื่อ RSS ไม่มีข้อมูล) — owner ตัวเดียว.

กลยุทธ์ selector (ยืนยันกับ HTML จริงของไทยรัฐ 2026-09-11):
- หน้ารวมข่าว: ดึง URL บทความจาก pattern `/news/<section>/<id>` ใน HTML ดิบ
  (เว็บเป็น Next.js ไม่มีลิงก์ server-render ให้จับ) ถ้าไม่เจอเลย = โครงสร้างเปลี่ยน
  -> หยุดอย่างปลอดภัยพร้อมแจ้งเตือน ไม่เดา selector ใหม่เอง
- หน้าบทความ: อ่าน `__NEXT_DATA__` -> items (title/content/summary/publishTime)
  ถ้าโครงสร้างเปลี่ยน ใช้ fallback h1 + <main> ถ้ายังไม่ได้ ข้ามข่าวนั้น
- ทุกข่าวจาก fallback เข้า review queue (status=draft เสมอ) ไม่มี auto-publish
"""
import json
import logging
import re
from datetime import timedelta
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from news.ingestion import (
    NUMBER_REASON,
    clean_html_text,
    content_hash,
    extract_numbers,
    find_duplicate,
    get_or_create_rss_category,
    normalize_url,
)

logger = logging.getLogger(__name__)

FETCH_TIMEOUT_SECONDS = 20
MIN_CONTENT_LENGTH = 50
SCRAPER_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LekdeDaiBot/1.0"

# pattern URL บทความไทยรัฐ (ยืนยันจาก HTML จริง)
THAIRATH_ARTICLE_URL_RE = re.compile(r"/news/[a-z0-9\-]+/\d+")
THAIRATH_NEXT_DATA_RE = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', re.S
)


def fetch_html(url, timeout=FETCH_TIMEOUT_SECONDS):
    """ดึง HTML (มี timeout + UA) — จุดเดียวที่แตะ network (mock ง่าย)."""
    response = requests.get(
        url, timeout=timeout, headers={"User-Agent": SCRAPER_USER_AGENT}
    )
    response.raise_for_status()
    return response.text


def extract_list_urls(html, base_url, limit=10):
    """ดึง URL บทความจากหน้ารวม (คืน [] ถ้าโครงสร้างเปลี่ยน — ผู้เรียกต้องหยุด)."""
    found = []
    seen = set()
    for match in THAIRATH_ARTICLE_URL_RE.finditer(html or ""):
        path = match.group(0)
        if path.startswith("http"):
            full = path
        else:
            full = urljoin(base_url.rstrip("/") + "/", path)
        normalized = normalize_url(full)
        if normalized not in seen:
            seen.add(normalized)
            found.append(normalized)
        if len(found) >= limit:
            break
    return found


def _next_data_items(html):
    """แกะ items จาก __NEXT_DATA__ (คืน None ถ้าโครงสร้างเปลี่ยน)."""
    try:
        match = THAIRATH_NEXT_DATA_RE.search(html or "")
        if not match:
            return None
        data = json.loads(match.group(1))
        items = (
            data.get("props", {})
            .get("initialProps", {})
            .get("pageProps", {})
            .get("items")
        )
        return items if isinstance(items, dict) else None
    except (ValueError, AttributeError):
        return None


def _parse_publish_time(value):
    if not value:
        return None
    try:
        parsed = parse_datetime(str(value))
    except (ValueError, TypeError):
        return None
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=dt_timezone.utc)
    return parsed


def extract_article_data(html, url):
    """สกัด title/text/summary/published จากหน้าบทความ.

    คืน dict หรือ None ถ้าอ่านไม่ได้ (ผู้เรียกข้ามข่าวนั้น ไม่ล้มทั้งรอบ).
    """
    items = _next_data_items(html)
    if items and (items.get("title") or items.get("content")):
        return {
            "title": (items.get("title") or "").strip(),
            "text": clean_html_text(items.get("content") or ""),
            "summary": clean_html_text(items.get("summary") or items.get("abstract") or ""),
            "published": _parse_publish_time(items.get("publishTime")),
            "url": url,
        }

    # fallback: h1 + <main> (เว็บเปลี่ยนโครงสร้างบางส่วน)
    try:
        soup = BeautifulSoup(html or "", "html.parser")
        h1 = soup.find("h1")
        title = h1.get_text(strip=True) if h1 else ""
        mains = soup.select("main")
        text = ""
        if mains:
            paras = [
                p.get_text(separator=" ", strip=True)
                for p in mains[0].find_all("p")
                if len(p.get_text(strip=True)) > 40
            ]
            text = " ".join(paras)
        if not title or not text:
            return None
        return {
            "title": title,
            "text": " ".join(text.split()),
            "summary": "",
            "published": None,
            "url": url,
        }
    except Exception:  # HTML พัง — ข้ามข่าวนั้น
        return None


def scrape_category_source(source, limit=5, dry_run=False):
    """ขูด 1 แหล่ง category-page -> สรุป dict (ไม่ throw ออกนอก ยกเว้น DB ล่ม).

    นโยบาย: fallback เข้า review queue (draft) เสมอ ไม่มี auto-publish.
    """
    from ai_engine.models import DataIngestionRecord
    from news.models import NewsArticle

    summary = {
        "ok": False,
        "error": "",
        "examined": 0,
        "created": 0,
        "would_create": 0,
        "duplicates": 0,
        "skipped": 0,
    }

    try:
        list_html = fetch_html(source.url)
    except Exception as exc:
        logger.warning("Category list fetch failed for %s: %r", source.url, exc)
        _mark_failure(source, "ดึงหน้ารวมข่าวไม่สำเร็จ (เครือข่ายหรือเซิร์ฟเวอร์ต้นทาง)")
        summary["error"] = "ดึงหน้ารวมข่าวไม่สำเร็จ"
        return summary

    urls = extract_list_urls(list_html, source.url, limit=limit)
    if not urls:
        logger.warning("No article links found (structure changed?): %s", source.url)
        _mark_failure(source, "โครงสร้างหน้าเว็บเปลี่ยนหรือไม่พบลิงก์ข่าว — หยุดเพื่อรอตรวจสอบ")
        summary["error"] = "โครงสร้างหน้าเว็บเปลี่ยนหรือไม่พบลิงก์ข่าว"
        return summary

    now = timezone.now()
    source.last_scraped = now
    source.last_success_at = now
    source.last_error = ""
    if not dry_run:
        source.save(update_fields=["last_scraped", "last_success_at", "last_error"])
    summary["ok"] = True

    category = None if dry_run else get_or_create_rss_category()
    seen_hashes = set()

    for article_url in urls:
        summary["examined"] += 1
        try:
            article_html = fetch_html(article_url)
        except Exception as exc:
            logger.warning("Article fetch failed %s: %r", article_url, exc)
            summary["skipped"] += 1
            continue

        data = extract_article_data(article_html, article_url)
        if not data or len(data["text"]) < MIN_CONTENT_LENGTH:
            summary["skipped"] += 1
            continue

        digest = content_hash(data["title"], article_url)
        if digest in seen_hashes or (
            not dry_run and find_duplicate(source, article_url, data["title"])
        ):
            summary["duplicates"] += 1
            continue
        seen_hashes.add(digest)

        numbers = extract_numbers(data["text"], data["title"])
        numbered = [{"number": n, "reason": NUMBER_REASON} for n in numbers]
        if dry_run:
            summary["would_create"] += 1
            continue

        article = NewsArticle.objects.create(
            title=data["title"][:200],
            intro=(data["summary"] or data["text"])[:500],
            content=data["text"],
            category=category,
            data_source=source,
            source_url=normalize_url(article_url)[:500],
            content_hash=digest,
            published_date=data["published"],
            numbers_with_reasons=numbered,
            status="draft",  # fallback ต้องผ่าน review ก่อนเผยแพร่เสมอ
            analysis_status="pending",
        )
        DataIngestionRecord.objects.create(
            data_source=source,
            raw_content=f"{data['title']}\n{data['text']}",
            processed_content=data["text"],
            title=data["title"][:500],
            publish_date=data["published"],
            extracted_numbers=numbers,
            processing_status="completed",
        )
        summary["created"] += 1

    return summary


def _mark_failure(source, message):
    source.last_scraped = timezone.now()
    source.last_failure_at = source.last_scraped
    source.last_error = message
    source.save(update_fields=["last_scraped", "last_failure_at", "last_error"])


def rss_has_fresh_data(hours=24):
    """RSS มีข้อมูลล่าสุดหรือไม่ (fallback ใช้เฉพาะเมื่อไม่มี)."""
    from news.models import NewsArticle

    cutoff = timezone.now() - timedelta(hours=hours)
    return NewsArticle.objects.filter(
        data_source__category="rss", fetched_at__gte=cutoff
    ).exists()

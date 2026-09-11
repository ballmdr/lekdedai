"""Task 17: RSS ingestion เป็นเส้นทางหลัก — pure/testable functions + สรุปผลคาดเดาได้.

นโยบาย (policy):
- เก็บทุกข่าวที่ดึงได้ (draft) ไม่ทิ้งข้อมูลต้นฉบับ แม้ AI วิเคราะห์ล้มเหลว
- เลขจาก regex ภายใน (deterministic) ถ้าพบเลข -> สถานะ published พร้อมเลข+เหตุผล
- ไม่พบเลข -> สถานะ draft (เก็บไว้ ไม่โชว์สาธารณะ)
- AI ภายนอกเป็น best-effort เท่านั้น: ล้มเหลวได้ แต่ข้อมูลต้นฉบับต้องอยู่
- dedupe ด้วย content_hash (link+title) กันข่าวซ้ำข้ามรอบ
"""
import calendar
import hashlib
import logging
from datetime import datetime, timezone as dt_timezone
from urllib.parse import urlparse, urlunparse

import feedparser
import requests
from bs4 import BeautifulSoup
from django.utils import timezone

from qa import metrics as qa_metrics

from news.models import NewsArticle, NewsCategory

logger = logging.getLogger(__name__)

FETCH_TIMEOUT_SECONDS = 15
MIN_CONTENT_LENGTH = 50
NUMBER_REASON = "สกัดจากเนื้อหาข่าวอัตโนมัติ"
FETCH_USER_AGENT = "LekdeDaiBot/1.0 (RSS ingestion; +/news/)"
# ข่าวที่ดึงมานานเกินนี้ถือว่าเก่า (stale) — ไม่นำเสนอเป็น "ข่าวล่าสุด"
STALE_AFTER_HOURS = 48


def get_news_freshness(hours=STALE_AFTER_HOURS):
    """สถานะความสดของข่าวสำหรับ UI (Task 19).

    คืน {latest_fetched, is_stale, last_success, last_failure, failure_newer}:
    - is_stale = ไม่มีข่าว published เลย หรือข่าวใหม่สุดถูกดึงมานานเกิน hours
    - failure_newer = ความล้มเหลวล่าสุดใหม่กว่าความสำเร็จล่าสุด (ingestion ขัดข้อง)
    """
    from ai_engine.models import DataSource

    now = timezone.now()
    latest = (
        NewsArticle.objects.filter(status="published")
        .order_by("-fetched_at")
        .first()
    )
    latest_fetched = latest.fetched_at if latest else None

    rss_sources = DataSource.objects.filter(
        source_type="news", category="rss", is_active=True
    )
    successes = [s.last_success_at for s in rss_sources if s.last_success_at]
    failures = [s.last_failure_at for s in rss_sources if s.last_failure_at]
    last_success = max(successes) if successes else None
    last_failure = max(failures) if failures else None

    return {
        "latest_fetched": latest_fetched,
        "is_stale": latest_fetched is None
        or (now - latest_fetched).total_seconds() > hours * 3600,
        "last_success": last_success,
        "last_failure": last_failure,
        "failure_newer": bool(last_failure)
        and (not last_success or last_failure > last_success),
    }


def fetch_feed_content(url, timeout=FETCH_TIMEOUT_SECONDS):
    """ดึง bytes ของ feed (มี timeout) — จุดเดียวที่แตะ network (mock ง่าย)."""
    response = requests.get(
        url, timeout=timeout, headers={"User-Agent": FETCH_USER_AGENT}
    )
    response.raise_for_status()
    return response.content


def clean_html_text(html):
    """ล้าง HTML เหลือข้อความล้วน (เว้นวรรค normalize)."""
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator=" ").strip()
    return " ".join(text.split())


def entry_published_at(entry):
    """เวลาที่ข่าวเผยแพร่จาก feed (aware UTC) หรือ None ถ้าไม่มี."""
    parsed = getattr(entry, "published_parsed", None) or getattr(
        entry, "updated_parsed", None
    )
    if not parsed:
        return None
    try:
        return datetime.fromtimestamp(
            calendar.timegm(parsed), tz=dt_timezone.utc
        )
    except (ValueError, OverflowError, OSError):
        return None


def normalize_entry(entry):
    """normalize RSS entry -> dict (ทนฟิลด์หาย ไม่ throw กับ entry ปกติ)."""
    title = (getattr(entry, "title", "") or "").strip()
    link = (getattr(entry, "link", "") or "").strip()
    summary_html = ""
    if getattr(entry, "content", None):
        try:
            summary_html = entry.content[0].get("value", "")
        except (IndexError, AttributeError):
            summary_html = ""
    if not summary_html:
        summary_html = getattr(entry, "summary", "") or getattr(entry, "description", "") or ""
    return {
        "title": title,
        "link": link,
        "text": clean_html_text(summary_html),
        "published": entry_published_at(entry),
    }


def content_hash(title, link):
    """แฮชกันซ้ำจาก link (normalize แล้ว) + title."""
    normalized = f"{normalize_url(link)}\n{(title or '').strip()}"
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def normalize_url(url):
    """normalize URL กันซ้ำแม้เปลี่ยนเล็กน้อย (query/fragment/case/trailing slash)."""
    url = (url or "").strip()
    if not url:
        return ""
    try:
        parts = urlparse(url)
    except ValueError:
        return url.lower()
    scheme = (parts.scheme or "https").lower()
    netloc = parts.netloc.lower()
    path = parts.path.rstrip("/") or "/"
    return urlunparse((scheme, netloc, path, "", "", ""))


def find_duplicate(source, link, title):
    """หาข่าวซ้ำ: link ตรงกัน (หลัง normalize) หรือชื่อเดียวกันจากแหล่งเดียวกัน."""
    normalized = normalize_url(link)
    title = (title or "").strip()
    if normalized:
        hit = NewsArticle.objects.filter(source_url=normalized).first()
        if hit:
            return hit
    if source is not None and title:
        return NewsArticle.objects.filter(data_source=source, title=title).first()
    return None


def extract_numbers(text, title=""):
    """สกัดเลข 2-3 หลักแบบ deterministic (ไม่พึ่ง AI/เครือข่าย)."""
    probe = NewsArticle(title=title or "", content=text or "")
    return probe.extract_numbers_from_content()


def get_or_create_rss_category():
    category, _ = NewsCategory.objects.get_or_create(
        name="ข่าวทั่วไป",
        defaults={"slug": "general", "description": "ข่าวทั่วไปจาก RSS feeds"},
    )
    return category


def build_article_kwargs(normalized, numbers, source, category, analysis_status="pending"):
    """kwargs สร้าง NewsArticle ตาม policy (ยังไม่ save)."""
    text = normalized["text"]
    numbered = [
        {"number": num, "reason": NUMBER_REASON} for num in numbers
    ]
    return {
        "title": normalized["title"][:200],
        "intro": text[:500],
        "content": text,
        "category": category,
        "data_source": source,
        "source_url": normalize_url(normalized["link"])[:500],
        "content_hash": content_hash(normalized["title"], normalized["link"]),
        "published_date": normalized["published"],
        "numbers_with_reasons": numbered,
        "status": "published" if numbered else "draft",
        "analysis_status": analysis_status,
    }


def ingest_source(source, limit=20, analyzer=None, dry_run=False):
    """ดึง 1 แหล่ง RSS -> สรุปผล dict (ไม่ throw ออกนอก ยกเว้น DB ล่ม).

    คืน: {ok, error, examined, created, published, drafts, duplicates,
           skipped_short, analysis_failed}
    dry_run=True: ไม่เขียน DB (นับ would_create แทน created).
    analyzer=None: ข้าม AI (analysis_status ค้าง pending); ถ้าส่ง analyzer มา
    ล้มเหลวได้ แต่บทความต้องถูกบันทึกอยู่ดี (analysis_status=failed).
    """
    from ai_engine.models import DataIngestionRecord

    summary = {
        "ok": False,
        "error": "",
        "examined": 0,
        "created": 0,
        "would_create": 0,
        "published": 0,
        "drafts": 0,
        "duplicates": 0,
        "skipped_short": 0,
        "analysis_failed": 0,
    }

    try:
        raw = fetch_feed_content(source.url)
    except Exception as exc:  # network/timeout/HTTP — predictible failure
        logger.warning("RSS fetch failed for %s: %r", source.url, exc)
        _mark_source_failure(source, "ดึง feed ไม่สำเร็จ (เครือข่ายหรือเซิร์ฟเวอร์ต้นทาง)")
        summary["error"] = "ดึง feed ไม่สำเร็จ"
        return summary

    feed = feedparser.parse(raw)
    entries = list(getattr(feed, "entries", []) or [])
    if getattr(feed, "bozo", False) and not entries:
        logger.warning("Malformed RSS feed for %s", source.url)
        _mark_source_failure(source, "รูปแบบ feed ไม่ถูกต้อง")
        summary["error"] = "รูปแบบ feed ไม่ถูกต้อง"
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
    for entry in entries[:limit]:
        summary["examined"] += 1
        try:
            normalized = normalize_entry(entry)
        except Exception as exc:  # entry ประหลาด — ข้าม ไม่ล้มทั้ง feed
            logger.warning("Skipping bad RSS entry: %r", exc)
            continue
        if not normalized["title"] or len(normalized["text"]) < MIN_CONTENT_LENGTH:
            summary["skipped_short"] += 1
            continue

        digest = content_hash(normalized["title"], normalized["link"])
        if digest in seen_hashes or (
            not dry_run
            and find_duplicate(source, normalized["link"], normalized["title"])
        ):
            summary["duplicates"] += 1
            continue
        seen_hashes.add(digest)

        numbers = extract_numbers(normalized["text"], normalized["title"])
        analysis_status = "pending"
        if analyzer is not None:
            try:
                extra = _analyze_with_ai(analyzer, normalized)
                seen = set(numbers)
                for num in extra:
                    if num not in seen:
                        numbers.append(num)
                        seen.add(num)
                analysis_status = "analyzed"
                qa_metrics.incr("external_ai_calls", "ingestion|ok")
            except Exception as exc:
                logger.warning("AI analysis failed, keeping raw article: %r", exc)
                analysis_status = "failed"
                summary["analysis_failed"] += 1
                qa_metrics.incr("external_ai_calls", "ingestion|error")

        kwargs = build_article_kwargs(normalized, numbers, source, category, analysis_status)
        if dry_run:
            summary["would_create"] += 1
            if kwargs["status"] == "published":
                summary["published"] += 1
            else:
                summary["drafts"] += 1
            continue

        article = NewsArticle.objects.create(**kwargs)
        DataIngestionRecord.objects.create(
            data_source=source,
            raw_content=f"{normalized['title']}\n{normalized['text']}",
            processed_content=normalized["text"],
            title=normalized["title"][:500],
            publish_date=normalized["published"],
            extracted_numbers=numbers,
            processing_status="completed",
        )
        summary["created"] += 1
        if article.status == "published":
            summary["published"] += 1
        else:
            summary["drafts"] += 1

    return summary


def _analyze_with_ai(analyzer, normalized):
    """เรียก analyzer ภายนอก คืน list เลข (throw ให้ผู้เรียกจัดการ)."""
    temp_article = type(
        "TempArticle", (), {"title": normalized["title"], "content": normalized["text"]}
    )()
    analysis = analyzer.analyze_article(temp_article)
    numbers = (analysis or {}).get("numbers") or []
    return [str(n) for n in numbers if str(n).isdigit() and len(str(n)) in (2, 3)][:10]


def _mark_source_failure(source, message):
    source.last_scraped = timezone.now()
    source.last_failure_at = source.last_scraped
    source.last_error = message
    source.save(update_fields=["last_scraped", "last_failure_at", "last_error"])

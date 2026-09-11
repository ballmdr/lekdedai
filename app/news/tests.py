from django.test import TestCase

# Create your tests here.


class NewsRouteTests(TestCase):
    """Regression: หมวดที่ไม่มีอยู่ต้องไม่ 404 และค้นหาไม่ crash."""

    def test_unknown_category_shows_empty_state_not_404(self):
        res = self.client.get("/news/?category=major")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "ไม่พบหมวดข่าว")

    def test_search_does_not_crash(self):
        res = self.client.get("/news/?q=ทดสอบ")
        self.assertEqual(res.status_code, 200)

    def test_empty_list_no_none_text(self):
        res = self.client.get("/news/")
        self.assertEqual(res.status_code, 200)
        self.assertNotContains(res, 'value="None"')


FEED_FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>Test Feed</title>
<link>https://example.com</link>
<item>
<title>อุบัติเหตุรถชน ทะเบียน กข 1234 บ้านเลขที่ 45</title>
<link>https://example.com/news/1</link>
<description><![CDATA[<p>เกิดอุบัติเหตุรถชนที่บ้านเลขที่ 45 รถทะเบียน กข 1234 มีผู้ได้รับบาดเจ็บหลายราย ต้องนำตัวส่งโรงพยาบาลใกล้เคียงโดยด่วนที่สุด</p>]]></description>
<pubDate>Mon, 01 Sep 2026 08:00:00 +0700</pubDate>
</item>
<item>
<title>พยากรณ์อากาศประจำวันทั่วประเทศ</title>
<link>https://example.com/news/2</link>
<description><![CDATA[<p>กรมอุตุนิยมวิทยาพยากรณ์อากาศวันนี้ ทั่วทุกภาคของประเทศจะมีฝนตกกระจายตัวและมีลมกระโชกแรงในบางพื้นที่ของภาคเหนือและภาคตะวันออกเฉียงเหนือ</p>]]></description>
<pubDate>Tue, 02 Sep 2026 09:00:00 +0700</pubDate>
</item>
<item>
<title>อุบัติเหตุรถชน ทะเบียน กข 1234 บ้านเลขที่ 45</title>
<link>https://example.com/news/1</link>
<description><![CDATA[<p>เกิดอุบัติเหตุรถชนที่บ้านเลขที่ 45 รถทะเบียน กข 1234 มีผู้ได้รับบาดเจ็บหลายราย ต้องนำตัวส่งโรงพยาบาลใกล้เคียงโดยด่วนที่สุด</p>]]></description>
<pubDate>Mon, 01 Sep 2026 08:00:00 +0700</pubDate>
</item>
</channel>
</rss>
""".encode("utf-8")


def _make_source(**kwargs):
    from ai_engine.models import DataSource

    defaults = {
        "key": "test-rss",
        "name": "Test RSS",
        "source_type": "news",
        "category": "rss",
        "url": "https://example.com/feed",
        "attribution": "Test",
        "is_active": True,
        "scraping_interval": 6,
    }
    defaults.update(kwargs)
    return DataSource.objects.create(**defaults)


class RssIngestionTests(TestCase):
    """Task 17: feed ปกติ/ผิดรูป/timeout/ซ้ำ/AI ล้มเหลว ต้องคาดเดาได้."""

    def test_normal_ingest_publishes_numbered_and_drafts_rest(self):
        from unittest.mock import patch

        from news.ingestion import ingest_source
        from news.models import NewsArticle

        source = _make_source()
        with patch("news.ingestion.fetch_feed_content", return_value=FEED_FIXTURE):
            summary = ingest_source(source, limit=10)

        self.assertTrue(summary["ok"])
        self.assertEqual(summary["examined"], 3)
        self.assertEqual(summary["created"], 2)
        self.assertEqual(summary["published"], 1)
        self.assertEqual(summary["drafts"], 1)
        self.assertEqual(summary["duplicates"], 1)

        article = NewsArticle.objects.get(source_url="https://example.com/news/1")
        self.assertEqual(article.status, "published")
        self.assertTrue(article.get_numbers_only())
        self.assertTrue(article.content_hash)
        self.assertIsNotNone(article.fetched_at)
        self.assertEqual(article.data_source, source)
        self.assertIsNotNone(article.published_date)
        self.assertEqual(article.analysis_status, "pending")

        draft = NewsArticle.objects.get(source_url="https://example.com/news/2")
        self.assertEqual(draft.status, "draft")

        source.refresh_from_db()
        self.assertIsNotNone(source.last_success_at)
        self.assertEqual(source.last_error, "")

    def test_rerun_dedupes_everything(self):
        from unittest.mock import patch

        from news.ingestion import ingest_source

        source = _make_source()
        with patch("news.ingestion.fetch_feed_content", return_value=FEED_FIXTURE):
            ingest_source(source, limit=10)
            summary = ingest_source(source, limit=10)
        self.assertEqual(summary["created"], 0)
        # ทั้ง 3 entry ซ้ำ (2 แถวมีใน DB แล้ว + 1 ซ้ำในรอบ)
        self.assertEqual(summary["duplicates"], 3)

    def test_malformed_feed_predictable_failure(self):
        from unittest.mock import patch

        from ai_engine.models import DataIngestionRecord
        from news.ingestion import ingest_source
        from news.models import NewsArticle

        source = _make_source()
        with patch("news.ingestion.fetch_feed_content", return_value=b"<html>not rss"):
            summary = ingest_source(source, limit=10)
        self.assertFalse(summary["ok"])
        self.assertEqual(summary["error"], "รูปแบบ feed ไม่ถูกต้อง")
        self.assertEqual(NewsArticle.objects.count(), 0)
        self.assertEqual(DataIngestionRecord.objects.count(), 0)
        source.refresh_from_db()
        self.assertIsNotNone(source.last_failure_at)
        self.assertNotIn("Traceback", source.last_error)

    def test_timeout_predictable_failure(self):
        from unittest.mock import patch

        import requests

        from news.ingestion import ingest_source
        from news.models import NewsArticle

        source = _make_source()
        with patch(
            "news.ingestion.fetch_feed_content", side_effect=requests.Timeout("slow")
        ):
            summary = ingest_source(source, limit=10)
        self.assertFalse(summary["ok"])
        self.assertEqual(summary["error"], "ดึง feed ไม่สำเร็จ")
        self.assertEqual(NewsArticle.objects.count(), 0)
        source.refresh_from_db()
        self.assertIsNotNone(source.last_failure_at)

    def test_ai_failure_keeps_raw_article(self):
        from unittest.mock import patch

        from news.ingestion import ingest_source
        from news.models import NewsArticle

        class Boom:
            def analyze_article(self, article):
                raise RuntimeError("groq down")

        source = _make_source()
        with patch("news.ingestion.fetch_feed_content", return_value=FEED_FIXTURE):
            summary = ingest_source(source, limit=10, analyzer=Boom())
        # analyzer ถูกเรียกทั้งข่าวมีเลขและข่าวร่าง (2 รายการไม่ซ้ำ) ล้มทั้งคู่ แต่ข้อมูลอยู่ครบ
        self.assertEqual(summary["analysis_failed"], 2)
        article = NewsArticle.objects.get(source_url="https://example.com/news/1")
        self.assertEqual(article.analysis_status, "failed")
        self.assertTrue(article.get_numbers_only())

    def test_dry_run_writes_nothing(self):
        from unittest.mock import patch

        from ai_engine.models import DataIngestionRecord
        from news.ingestion import ingest_source
        from news.models import NewsArticle

        source = _make_source()
        with patch("news.ingestion.fetch_feed_content", return_value=FEED_FIXTURE):
            summary = ingest_source(source, limit=10, dry_run=True)
        self.assertTrue(summary["ok"])
        self.assertEqual(summary["would_create"], 2)
        self.assertEqual(NewsArticle.objects.count(), 0)
        self.assertEqual(DataIngestionRecord.objects.count(), 0)

    def test_normalize_tolerates_missing_fields(self):
        import feedparser

        from news.ingestion import normalize_entry

        feed = feedparser.parse("""<?xml version="1.0"?>
        <rss version="2.0"><channel><title>t</title>
        <item><title>แค่หัวข้อ</title></item>
        </channel></rss>""")
        norm = normalize_entry(feed.entries[0])
        self.assertEqual(norm["title"], "แค่หัวข้อ")
        self.assertEqual(norm["link"], "")
        self.assertEqual(norm["text"], "")
        self.assertIsNone(norm["published"])

    def test_content_hash_stable(self):
        from news.ingestion import content_hash

        self.assertEqual(
            content_hash("ข่าว", "https://example.com/1"),
            content_hash("ข่าว", "https://example.com/1"),
        )
        self.assertNotEqual(
            content_hash("ข่าว", "https://example.com/1"),
            content_hash("ข่าว", "https://example.com/2"),
        )


class ScrapeRssCommandTests(TestCase):
    def test_dry_run_command(self):
        from unittest.mock import patch

        from django.core.management import call_command

        from news.models import NewsArticle

        _make_source(key="cmd-rss", name="Cmd RSS")
        with patch("news.ingestion.fetch_feed_content", return_value=FEED_FIXTURE):
            call_command("scrape_rss_feeds", source="cmd-rss", dry_run=True)
        self.assertEqual(NewsArticle.objects.count(), 0)

    def test_unknown_source_warns_without_crash(self):
        from django.core.management import call_command

        call_command("scrape_rss_feeds", source="no-such-source")  # ต้องไม่ throw


LIST_HTML = """
<html><body>
<nav><a href="/news/local">ท้องถิ่น</a><a href="/horoscope">ดวง</a></nav>
<div><a href="/news/local/2958991">พาดหัวข่าวหนึ่งที่ยาวพอให้ทดสอบระบบ</a></div>
<div><a href="https://www.thairath.co.th/news/politic/2958990">อีกพาดหัวหนึ่งสำหรับทดสอบเช่นกัน</a></div>
<div><a href="/news/local/2958991?utm_source=test">ลิงก์ซ้ำแบบมี query</a></div>
</body></html>
"""

ARTICLE_HTML = """
<html><head><title>t</title></head><body>
<h1>พาดหัวข่าวทดสอบที่มีบ้านเลขที่ 45</h1>
<script id="__NEXT_DATA__" type="application/json">{"props": {"initialProps": {"pageProps": {"items": {"title": "พาดหัวข่าวทดสอบที่มีบ้านเลขที่ 45", "content": "<p>เกิดเหตุเมื่อวานนี้ที่บ้านเลขที่ 45 รถทะเบียน กข 1234 มีผู้เห็นเหตุการณ์หลายคนเล่าให้ผู้สื่อข่าวฟังอย่างละเอียดครบถ้วนทุกประเด็น</p>", "summary": "<p>สรุปสั้นของข่าวทดสอบนี้</p>", "publishTime": "2026-09-10T08:00:00+07:00"}}}}}</script>
</body></html>
"""

NO_LINK_HTML = "<html><body><p>หน้านี้ไม่มีลิงก์ข่าวเลย</p></body></html>"

ARTICLE_HTML_2 = """
<html><head><title>t</title></head><body>
<h1>ไฟไหม้บ้านเลขที่ 99 เสียหายหลายแสน</h1>
<script id="__NEXT_DATA__" type="application/json">{"props": {"initialProps": {"pageProps": {"items": {"title": "ไฟไหม้บ้านเลขที่ 99 เสียหายหลายแสน", "content": "<p>เกิดเหตุเพลิงไหม้บ้านเลขที่ 99 เมื่อช่วงเช้าที่ผ่านมา เจ้าหน้าที่ดับเพลิงใช้เวลาควบคุมเพลิงกว่าหนึ่งชั่วโมง ค่าเสียหายเบื้องต้นหลายแสนบาท</p>", "summary": "<p>สรุปไฟไหม้</p>", "publishTime": "2026-09-09T10:00:00+07:00"}}}}}</script>
</body></html>
"""


def _make_category_source(**kwargs):
    from ai_engine.models import DataSource

    defaults = {
        "key": "test-cat",
        "name": "Test Category",
        "source_type": "news",
        "category": "category_page",
        "url": "https://example.com/cat",
        "attribution": "Test",
        "is_active": True,
        "scraping_interval": 12,
    }
    defaults.update(kwargs)
    return DataSource.objects.create(**defaults)


class CategoryScraperTests(TestCase):
    """Task 18: selector เปลี่ยนหยุดปลอดภัย, ซ้ำไม่สร้าง, draft เสมอ."""

    def test_extract_list_urls_dedupes_and_resolves(self):
        from news.category_scraper import extract_list_urls

        urls = extract_list_urls(LIST_HTML, "https://www.thairath.co.th", limit=10)
        self.assertEqual(len(urls), 2)
        self.assertIn("https://www.thairath.co.th/news/local/2958991", urls)
        self.assertIn("https://www.thairath.co.th/news/politic/2958990", urls)

    def test_extract_list_urls_empty_on_structure_change(self):
        from news.category_scraper import extract_list_urls

        self.assertEqual(extract_list_urls(NO_LINK_HTML, "https://x.co", limit=10), [])

    def test_extract_article_data_from_next_data(self):
        from news.category_scraper import extract_article_data

        data = extract_article_data(ARTICLE_HTML, "https://example.com/a/1")
        self.assertEqual(data["title"], "พาดหัวข่าวทดสอบที่มีบ้านเลขที่ 45")
        self.assertIn("บ้านเลขที่ 45", data["text"])
        self.assertIsNotNone(data["published"])
        self.assertTrue(data["published"].tzinfo is not None)

    def test_extract_article_data_fallback_and_garbage(self):
        from news.category_scraper import extract_article_data

        fallback = (
            "<html><body><h1>พาดหัว fallback</h1><main>"
            "<p>ย่อหน้าเนื้อหายาวพอสำหรับทดสอบ fallback ของ scraper  category นี้อย่างน้อยสี่สิบตัวอักษรขึ้นไป</p>"
            "</main></body></html>"
        )
        data = extract_article_data(fallback, "https://example.com/a/2")
        self.assertEqual(data["title"], "พาดหัว fallback")
        self.assertIsNone(extract_article_data("<html></html>", "https://example.com/a/3"))

    def _fetch(self, url):
        if url == "https://example.com/cat":
            return LIST_HTML
        if "2958990" in url:
            return ARTICLE_HTML_2
        return ARTICLE_HTML

    def test_scrape_creates_drafts_only(self):
        from unittest.mock import patch

        from news.category_scraper import scrape_category_source
        from news.models import NewsArticle

        source = _make_category_source()
        with patch("news.category_scraper.fetch_html", side_effect=self._fetch):
            summary = scrape_category_source(source, limit=5)
        self.assertTrue(summary["ok"])
        self.assertEqual(summary["created"], 2)
        articles = NewsArticle.objects.all()
        self.assertTrue(all(a.status == "draft" for a in articles))
        article = NewsArticle.objects.get(source_url__contains="2958991")
        self.assertTrue(article.get_numbers_only())
        self.assertEqual(article.data_source, source)
        source.refresh_from_db()
        self.assertIsNotNone(source.last_success_at)

    def test_duplicate_url_variant_not_created(self):
        from unittest.mock import patch

        from news.category_scraper import scrape_category_source
        from news.ingestion import normalize_url
        from news.models import NewsArticle

        source = _make_category_source()
        NewsArticle.objects.create(
            title="ข่าวเดิม",
            intro="x",
            content="เนื้อหาเดิมยาวพอสำหรับทดสอบการกันข่าวซ้ำในระบบนี้อย่างแน่นอน",
            source_url=normalize_url("https://example.com/news/local/2958991"),
            content_hash="preexisting",
            data_source=source,
        )
        with patch("news.category_scraper.fetch_html", side_effect=self._fetch):
            summary = scrape_category_source(source, limit=5)
        self.assertEqual(summary["created"], 1)
        self.assertEqual(summary["duplicates"], 1)

    def test_structure_change_fails_safely(self):
        from unittest.mock import patch

        from news.category_scraper import scrape_category_source
        from news.models import NewsArticle

        source = _make_category_source()
        with patch("news.category_scraper.fetch_html", return_value=NO_LINK_HTML):
            summary = scrape_category_source(source, limit=5)
        self.assertFalse(summary["ok"])
        self.assertIn("โครงสร้าง", summary["error"])
        self.assertEqual(NewsArticle.objects.count(), 0)
        source.refresh_from_db()
        self.assertIsNotNone(source.last_failure_at)

    def test_fetch_failure_fails_safely(self):
        from unittest.mock import patch

        import requests

        from news.category_scraper import scrape_category_source
        from news.models import NewsArticle

        source = _make_category_source()
        with patch(
            "news.category_scraper.fetch_html",
            side_effect=requests.ConnectionError("down"),
        ):
            summary = scrape_category_source(source, limit=5)
        self.assertFalse(summary["ok"])
        self.assertEqual(NewsArticle.objects.count(), 0)


class ScrapeCategoryCommandTests(TestCase):
    def _fetch(self, url):
        if url == "https://example.com/cat":
            return LIST_HTML
        if "2958990" in url:
            return ARTICLE_HTML_2
        return ARTICLE_HTML

    def test_skips_when_rss_fresh_without_force(self):
        from unittest.mock import patch

        from django.utils import timezone

        from ai_engine.models import DataSource
        from news.models import NewsArticle

        rss = DataSource.objects.create(
            key="rss-1", name="RSS", source_type="news", category="rss",
            url="https://example.com/feed", is_active=True,
        )
        NewsArticle.objects.create(
            title="ข่าว RSS ล่าสุด", intro="x",
            content="เนื้อหาข่าว RSS ล่าสุดที่ยาวพอสำหรับทดสอบอย่างแน่นอน",
            data_source=rss,
        )
        _make_category_source()
        with patch(
            "news.category_scraper.fetch_html", side_effect=self._fetch
        ) as mocked:
            from django.core.management import call_command

            call_command("scrape_category", limit=2)
            mocked.assert_not_called()
        self.assertEqual(
            NewsArticle.objects.filter(data_source__category="category_page").count(), 0
        )

    def test_force_runs_despite_fresh_rss(self):
        from unittest.mock import patch

        from django.core.management import call_command

        from ai_engine.models import DataSource
        from news.models import NewsArticle

        rss = DataSource.objects.create(
            key="rss-1", name="RSS", source_type="news", category="rss",
            url="https://example.com/feed", is_active=True,
        )
        NewsArticle.objects.create(
            title="ข่าว RSS ล่าสุด", intro="x",
            content="เนื้อหาข่าว RSS ล่าสุดที่ยาวพอสำหรับทดสอบอย่างแน่นอน",
            data_source=rss,
        )
        _make_category_source()
        with patch("news.category_scraper.fetch_html", side_effect=self._fetch):
            call_command("scrape_category", limit=2, force=True)
        self.assertEqual(
            NewsArticle.objects.filter(data_source__category="category_page").count(), 2
        )


class NewsAdminReviewTests(TestCase):
    """Task 18: admin เห็นที่มา/เลข/เหตุผล อนุมัติ/ปฏิเสธได้."""

    def setUp(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        self.staff = User.objects.create_user("editor", password="pw", is_staff=True)
        self.staff.is_superuser = True
        self.staff.save()

    def _article(self, **kwargs):
        from news.models import NewsArticle

        defaults = {
            "title": "ข่าวรอตรวจ",
            "intro": "x",
            "content": "อุบัติเหตุที่บ้านเลขที่ 45 รถทะเบียน กข 1234 มีผู้เห็นเหตุการณ์หลายคนเล่าให้ฟังอย่างละเอียด",
            "status": "draft",
        }
        defaults.update(kwargs)
        return NewsArticle.objects.create(**defaults)

    def _post_action(self, action, article):
        return self.client.post(
            "/admin/news/newsarticle/",
            {"action": action, "_selected_action": [article.id]},
            follow=True,
        )

    def test_publish_action(self):
        self.client.force_login(self.staff)
        res = self._post_action("publish_articles", self._article())
        self.assertEqual(res.status_code, 200)
        from news.models import NewsArticle

        self.assertEqual(NewsArticle.objects.get().status, "published")

    def test_archive_action_rejects(self):
        self.client.force_login(self.staff)
        res = self._post_action("archive_articles", self._article())
        self.assertEqual(res.status_code, 200)
        from news.models import NewsArticle

        self.assertEqual(NewsArticle.objects.get().status, "archived")

    def test_extract_numbers_writes_reasons(self):
        self.client.force_login(self.staff)
        article = self._article()
        res = self._post_action("extract_numbers", article)
        self.assertEqual(res.status_code, 200)
        article.refresh_from_db()
        self.assertTrue(article.get_numbers_only())
        self.assertEqual(article.analysis_status, "analyzed")


def _make_curated_article(**kwargs):
    from datetime import timedelta

    from django.utils import timezone

    from ai_engine.models import DataSource
    from news.models import NewsArticle

    source, _ = DataSource.objects.get_or_create(
        key="test-provenance",
        defaults={
            "name": "Test Source", "source_type": "news", "category": "rss",
            "url": "https://example.com/feed", "attribution": "Test Press",
            "is_active": True,
        },
    )
    now = timezone.now()
    defaults = {
        "title": "ข่าวผ่านการคัดที่ตรวจย้อนกลับได้",
        "intro": "สรุป",
        "content": "เนื้อหาข่าวผ่านการคัดที่ยาวพอสำหรับทดสอบการแสดงผลอย่างแน่นอน",
        "status": "published",
        "published_date": now - timedelta(hours=2),
        "data_source": source,
        "source_url": "https://example.com/original/1",
        "content_hash": "curated-1",
        "analysis_status": "analyzed",
        "numbers_with_reasons": [{"number": "45", "reason": "บ้านเลขที่"}],
    }
    defaults.update(kwargs)
    return NewsArticle.objects.create(**defaults)


class CuratedNewsDisplayTests(TestCase):
    """Task 19: published มี provenance ครบ โผล่ครั้งเดียว; draft ไม่โผล่; stale ตรง ingestion."""

    def test_published_appears_once_with_provenance(self):
        article = _make_curated_article()
        html = self.client.get("/news/").content.decode()
        self.assertEqual(html.count(article.get_absolute_url()), 1)
        self.assertContains(self.client.get("/news/"), "อ่านต้นฉบับ")
        self.assertContains(self.client.get("/news/"), "Test Press")
        self.assertContains(self.client.get("/news/"), "วิเคราะห์แล้ว")

    def test_detail_shows_provenance(self):
        article = _make_curated_article()
        res = self.client.get(article.get_absolute_url())
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "อ่านต้นฉบับ")
        self.assertContains(res, "ดึงข้อมูล")

    def test_home_shows_article_once(self):
        article = _make_curated_article()
        html = self.client.get("/").content.decode()
        self.assertEqual(html.count(article.get_absolute_url()), 1)

    def test_draft_hidden_everywhere(self):
        article = _make_curated_article(status="draft")
        self.assertNotContains(self.client.get("/news/"), article.title)
        self.assertNotContains(self.client.get("/"), article.title)
        self.assertNotContains(
            self.client.get("/"), article.get_absolute_url()
        )

    def test_stale_note_when_news_old(self):
        from datetime import timedelta

        from django.utils import timezone

        from news.models import NewsArticle

        article = _make_curated_article()
        old = timezone.now() - timedelta(days=3)
        NewsArticle.objects.filter(pk=article.pk).update(fetched_at=old)
        self.assertContains(self.client.get("/"), "อาจไม่อัปเดต")
        self.assertContains(self.client.get("/news/"), "อาจไม่อัปเดต")

    def test_failure_banner_when_ingestion_failing(self):
        from django.utils import timezone

        from ai_engine.models import DataSource

        _make_curated_article()
        DataSource.objects.filter(key="test-provenance").update(
            last_failure_at=timezone.now(), last_success_at=None
        )
        res = self.client.get("/news/")
        self.assertContains(res, "ดึงข่าวล่าสุดล้มเหลว")

    def test_e2e_fixture_to_homepage(self):
        from unittest.mock import patch

        from news.ingestion import ingest_source
        from news.models import NewsArticle

        source = _make_source(key="e2e-rss", name="E2E RSS")
        with patch("news.ingestion.fetch_feed_content", return_value=FEED_FIXTURE):
            ingest_source(source, limit=10)
        article = NewsArticle.objects.get(status="published")
        for url in ("/news/", "/"):
            html = self.client.get(url).content.decode()
            self.assertEqual(html.count(article.get_absolute_url()), 1, url)
        self.assertContains(self.client.get(article.get_absolute_url()), "อ่านต้นฉบับ")

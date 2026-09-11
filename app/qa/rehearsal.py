"""Task 29: staging dress rehearsal — จำลองหนึ่งรอบงวด + ทดสอบเหตุขัดข้อง.

รันจริงบน DB ปัจจุบัน (staging) โดยติดป้ายข้อมูลที่สร้างเองว่า "rehearsal-"
และลบทิ้งเมื่อจบ (ยกเว้น --keep) ไม่แตะข้อมูลจริงที่มีอยู่.

คืนผลเป็น list ของ step: {name, status (pass/degraded/fail), seconds, detail}
ให้ command ประกอบเป็นรายงานที่เซ็นด้วย sha256 + git rev.
"""
import hashlib
import json
import logging
import subprocess
import time
from contextlib import contextmanager
from datetime import date, timedelta
from unittest.mock import patch

from django.test import Client
from django.utils import timezone

from utils.lottery_dates import LotteryDates

logger = logging.getLogger(__name__)

REHEARSAL_SOURCE_KEY = "rehearsal-source"
REHEARSAL_SESSION_PREFIX = "rehearsal-"

FIXTURE_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Rehearsal</title>
<item><title>ทดสอบระบบ บ้านเลขที่ 45 ทะเบียน กข 1234</title>
<link>https://example.com/rehearsal/1</link>
<description><![CDATA[<p>เหตุการณ์ทดสอบที่บ้านเลขที่ 45 รถทะเบียน กข 1234
มีผู้เห็นเหตุการณ์หลายคนเล่าให้ผู้สื่อข่าวฟังอย่างละเอียดครบถ้วน</p>]]></description>
<pubDate>Mon, 01 Sep 2026 08:00:00 +0700</pubDate></item>
</channel></rss>
""".encode("utf-8")

EMPTY_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Empty</title></channel></rss>
""".encode("utf-8")

REHEARSAL_LEADING_ZERO_PAYLOAD = {
    "response": {
        "result": {
            "data": {
                "first": {"number": [{"value": "012345"}]},
                "second": {"number": [{"value": "111111"}]},
                "third": {"number": [{"value": "222222"}]},
                "fourth": {"number": [{"value": "333333"}]},
                "fifth": {"number": [{"value": "444444"}]},
                "last3f": {"number": [{"value": "012"}]},
                "last3b": {"number": [{"value": "345"}]},
                "last2": {"number": [{"value": "45"}]},
                "near1": {"number": [{"value": "012344"}]},
            }
        }
    }
}


class _Step:
    def __init__(self, name):
        self.name = name
        self.status = "pass"
        self.detail = ""
        self.seconds = 0.0
        self.started = time.monotonic()

    def finish(self, status="pass", detail=""):
        self.status = status
        self.detail = detail
        self.seconds = round(time.monotonic() - self.started, 2)
        return self

    def to_dict(self):
        return {
            "name": self.name,
            "status": self.status,
            "seconds": self.seconds,
            "detail": self.detail,
        }


@contextmanager
def _step(results, name):
    step = _Step(name)
    try:
        yield step
    except Exception as exc:  # noqa: BLE001
        step.finish("fail", f"{type(exc).__name__}: {exc}"[:200])
    finally:
        if step.status == "pass" and not step.detail:
            step.detail = "ok"
        results.append(step.to_dict())


def _git_rev():
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=10,
        ).stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def _pick_rehearsal_draw():
    """งวดในอดีตที่ยังไม่มีข้อมูล ใช้จำลอง 'ผลหวยมาแล้ว'."""
    from lottery_checker.models import LottoResult

    for iso in LotteryDates.get_recent_draw_dates(400):
        d = date.fromisoformat(iso)
        if d < timezone.localdate() and not LottoResult.objects.filter(draw_date=d).exists():
            return d
    return None


def _health(client):
    res = client.get("/health/", HTTP_HOST="localhost")
    return res.status_code, res.json()


def _make_rehearsal_source():
    from ai_engine.models import DataSource

    source, _ = DataSource.objects.update_or_create(
        key=REHEARSAL_SOURCE_KEY,
        defaults={
            "name": "Rehearsal Source",
            "source_type": "news",
            "category": "rss",
            "url": "https://example.com/rehearsal-feed",
            "attribution": "Rehearsal",
            "license_status": "approved",
            "is_active": True,
            "scraping_interval": 6,
        },
    )
    return source


def cleanup_rehearsal(draw_date=None):
    """ลบข้อมูลที่ rehearsal สร้าง (เรียกท้ายสุด/เมื่อ fail)."""
    from ai_engine.models import DataSource, DataIngestionRecord
    from analytics.models import AnalyticsEvent
    from lottery_checker.models import LottoResult
    from lotto_formula.models import Prediction
    from lotto_stats.models import LotteryDraw
    from news.models import NewsArticle
    from qa.models import JobRun

    NewsArticle.objects.filter(data_source__key=REHEARSAL_SOURCE_KEY).delete()
    DataIngestionRecord.objects.filter(
        data_source__key=REHEARSAL_SOURCE_KEY
    ).delete()
    DataSource.objects.filter(key=REHEARSAL_SOURCE_KEY).delete()
    AnalyticsEvent.objects.filter(
        session_id__startswith=REHEARSAL_SESSION_PREFIX
    ).delete()
    JobRun.objects.filter(key__startswith="rehearsal-").delete()
    if draw_date:
        Prediction.objects.filter(draw_date=draw_date).delete()
        LottoResult.objects.filter(draw_date=draw_date).delete()
        LotteryDraw.objects.filter(draw_date=draw_date).delete()


def run_rehearsal(cleanup=True, include_backup=True):
    """รัน rehearsal ทั้งหมด คืน dict พร้อม steps/overall/report_sha256.

    include_backup=False ใช้ในเทสต์ (SQLite in-memory backup ชน lock ของ transaction).
    """
    from news.ingestion import ingest_source
    from qa.management.commands.check_alerts import collect_alerts

    started_at = timezone.now().isoformat()
    results = []
    client = Client()
    draw_date = _pick_rehearsal_draw()

    # 1) baseline health
    with _step(results, "health_baseline") as s:
        code, body = _health(client)
        s.finish("pass" if code in (200, 503) else "fail",
                 f"status={body.get('status')} problems={body.get('problems')}")

    # 2) รอบปกติ: ดึงข่าวสำเร็จ
    source = _make_rehearsal_source()
    with _step(results, "news_happy_path") as s:
        with patch("news.ingestion.fetch_feed_content", return_value=FIXTURE_FEED):
            summary = ingest_source(source, limit=5)
        from news.models import NewsArticle
        created = NewsArticle.objects.filter(data_source=source).count()
        if summary["ok"] and created >= 1:
            s.detail = f"created={created} published={summary['published']}"
        else:
            s.finish("fail", f"summary={summary}")

    # 3) ข่าวว่าง ต้องไม่ crash
    with _step(results, "empty_news_no_crash") as s:
        with patch("news.ingestion.fetch_feed_content", return_value=EMPTY_FEED):
            summary = ingest_source(source, limit=5)
        s.finish("pass" if summary["ok"] else "fail", f"examined={summary['examined']}")

    # 4) AI ล้ม — ข้อมูลต้นฉบับต้องอยู่ (ลบข่าว rehearsal ก่อนให้ ingest สด)
    with _step(results, "ai_failure_keeps_data") as s:
        from news.models import NewsArticle

        NewsArticle.objects.filter(data_source=source).delete()

        class Boom:
            def analyze_article(self, article):
                raise RuntimeError("provider down")

        with patch("news.ingestion.fetch_feed_content", return_value=FIXTURE_FEED):
            summary = ingest_source(source, limit=5, analyzer=Boom())
        kept = NewsArticle.objects.filter(data_source=source).count()
        ok = summary["analysis_failed"] >= 1 and kept >= 1
        s.finish("pass" if ok else "fail",
                 f"analysis_failed={summary['analysis_failed']} kept={kept}")

    # 5) upstream ล่ม — ปิดแหล่ง + บันทึก failure
    with _step(results, "upstream_down_safe") as s:
        import requests

        with patch(
            "news.ingestion.fetch_feed_content",
            side_effect=requests.Timeout("down"),
        ):
            summary = ingest_source(source, limit=5)
        source.refresh_from_db()
        ok = (not summary["ok"]) and source.last_failure_at is not None
        s.finish("pass" if ok else "fail", f"error={summary['error']}")

    # 6) สร้าง/บันทึก prediction + ผลจริง + ตรวจประวัติ
    if draw_date is None:
        with _step(results, "draw_cycle") as s:
            s.finish("degraded", "ไม่มีงวดว่างให้จำลอง (ข้าม draw cycle)")
    else:
        with _step(results, "prediction_and_result_cycle") as s:
            from lotto_formula.models import LotteryFormula, Prediction
            from lotto_formula.verification import verify_pending_predictions
            from lottery_checker.lotto_service import LottoService
            from lotto_stats.lotto_sync_service import LottoSyncService

            formula = LotteryFormula.objects.filter(is_approved=True).first()
            if formula is None:
                s.finish("degraded", "ไม่มีสูตรที่อนุมัติ (ข้าม)")
            else:
                Prediction.objects.create(
                    formula=formula,
                    predicted_numbers="012,345",
                    input_numbers="12",
                    draw_date=draw_date,
                )
                LottoService().save_to_database(REHEARSAL_LEADING_ZERO_PAYLOAD, draw_date)
                LottoSyncService().sync_specific_date(draw_date)
                verify_pending_predictions()
                row = Prediction.objects.get(draw_date=draw_date)
                s.finish(
                    "pass" if row.is_correct is not None else "fail",
                    f"prediction verified is_correct={row.is_correct}",
                )

        # 7) ผู้ใช้ตรวจผลผ่าน API (read-only) เห็นรางวัลที่ 1
        with _step(results, "user_result_check") as s:
            res = client.post(
                "/lottery_checker/api/check-draw/",
                data=json.dumps({"draw_date": draw_date.isoformat(), "number": "012345"}),
                content_type="application/json",
                HTTP_HOST="localhost",
            )
            body = res.json()
            ok = res.status_code == 200 and body.get("status") == "won"
            s.finish("pass" if ok else "fail", f"status={body.get('status')}")

    # 8) analytics รับ event
    with _step(results, "analytics_event") as s:
        res = client.post(
            "/analytics/event/",
            data=json.dumps({
                "name": "landing_view",
                "session_id": f"{REHEARSAL_SESSION_PREFIX}abc",
            }),
            content_type="application/json",
            HTTP_HOST="localhost",
        )
        s.finish("pass" if res.json().get("stored") else "fail", f"code={res.status_code}")

    # 9) backup + restore drill (ข้ามอัตโนมัติบน DB in-memory/เทสต์ กัน lock)
    from django.db import connection

    db_name = str(connection.settings_dict.get("NAME", ""))
    if ":memory:" in db_name or "file:memory" in db_name:
        include_backup = False
    if include_backup:
        with _step(results, "backup_restore_drill") as s:
            import tempfile

            from qa.backup import backup_sqlite, restore_sqlite

            with tempfile.TemporaryDirectory() as tmp:
                dest = backup_sqlite(dest_dir=tmp, keep=2)
                tables = restore_sqlite(dest, target=str(__import__("pathlib").Path(tmp) / "r.sqlite3"))
                s.finish("pass" if tables > 0 else "fail", f"tables_restored={tables}")
    else:
        results.append(_Step("backup_restore_drill").finish("skipped", "ปิดในเทสต์").to_dict())

    # 10) ผลหวยช้า (stale job ในทะเบียนจริง) → degraded + alert
    with _step(results, "stale_data_degraded") as s:
        from qa.models import JobRun

        row, created = JobRun.objects.get_or_create(key="lotto_sync")
        prev = None
        if not created:
            prev = {"status": row.status, "last_success_at": row.last_success_at}
        row.status = "success"
        row.last_success_at = timezone.now() - timedelta(hours=100)
        row.save()
        try:
            code, body = _health(client)
            alerts = collect_alerts()
            ok = any("stale" in a for a in alerts)
        finally:
            if created:
                row.delete()
            else:
                row.status = prev["status"]
                row.last_success_at = prev["last_success_at"]
                row.save()
        s.finish("pass" if ok else "fail", f"alerts={len(alerts)}")

    # 11) upstream/AI ล้ม → alert จับได้
    with _step(results, "failure_alerts") as s:
        alerts = collect_alerts()
        ok = any("RSS" in a or "job" in a for a in alerts)
        s.finish("pass" if ok else "fail", f"alerts={len(alerts)}")

    # cleanup
    if cleanup:
        with _step(results, "cleanup") as s:
            cleanup_rehearsal(draw_date)
            s.finish("pass", "ลบข้อมูล rehearsal แล้ว")

    # 12) health หลัง cleanup
    with _step(results, "health_after") as s:
        code, body = _health(client)
        s.finish("pass" if code == 200 else "degraded",
                 f"status={body.get('status')} problems={body.get('problems')}")

    overall = "pass"
    if any(r["status"] == "fail" for r in results):
        overall = "fail"
    elif any(r["status"] == "degraded" for r in results):
        overall = "degraded"

    report = {
        "started_at": started_at,
        "finished_at": timezone.now().isoformat(),
        "git_rev": _git_rev(),
        "draw_date": draw_date.isoformat() if draw_date else None,
        "overall": overall,
        "steps": results,
    }
    report["report_sha256"] = hashlib.sha256(
        json.dumps(report, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    return report

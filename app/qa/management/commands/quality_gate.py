"""Task 21: quality gate คำสั่งเดียว — check, migrations, tests, static, smoke.

ล้มทันที (exit != 0) เมื่อขั้นตอนใดผิด ใช้ได้ทั้ง local และ CI.
"""
import json

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.test import Client

from utils.lottery_dates import LotteryDates

TEST_APPS = [
    "lottery_checker",
    "ai_engine",
    "news",
    "lotto_formula",
    "dreams",
    "notebook",
    "lotto_stats",
    "home",
    "qa",
]

SMOKE_GET_ROUTES = [
    "/",
    "/health/",
    "/dreams/",
    "/lottery_checker/",
    "/notebook/",
    "/lotto_stats/",
    "/news/",
    "/ai/",
    "/ai/history/",
    "/ai/accuracy/",
    "/ai/ensemble/history/",
    "/ai/data-sources/",
    "/lotto_formula/",
    "/lotto_formula/calculator/",
    "/static/css/tailwind.css",
    "/static/css/theme.css",
    "/static/js/format.js",
]


class Command(BaseCommand):
    help = "Quality gate: checks + migrations + tests + static + smoke (fail fast)"

    def handle(self, *args, **options):
        self._step("Django checks", self._run_checks)
        self._step("Migrations check", self._run_migrations_check)
        self._step("Migrate", self._run_migrate)
        self._step("Unit/integration tests", self._run_tests)
        self._step("Collect static", self._run_collectstatic)
        self._step("Smoke tests", self._run_smoke)
        self.stdout.write(self.style.SUCCESS("QUALITY GATE PASSED"))

    def _step(self, name, func):
        self.stdout.write(f"--- {name} ---")
        try:
            func()
        except CommandError:
            raise
        except SystemExit as exc:
            raise CommandError(f"{name} failed (exit {exc.code})")
        except Exception as exc:  # noqa: BLE001
            raise CommandError(f"{name} failed: {exc}")
        self.stdout.write(self.style.SUCCESS(f"OK {name}"))

    def _run_checks(self):
        call_command("check")
        call_command("check", "--deploy")

    def _run_migrations_check(self):
        call_command("makemigrations", "--check", "--dry-run", verbosity=0)

    def _run_migrate(self):
        call_command("migrate", "--noinput", verbosity=1)

    def _run_tests(self):
        call_command("test", *TEST_APPS, verbosity=1)

    def _run_collectstatic(self):
        call_command("collectstatic", "--noinput", verbosity=1)

    def _run_smoke(self):
        # ใช้ Host จริง (localhost) เพื่อตรวจ ALLOWED_HOSTS ไปด้วย — ห้ามพึ่ง testserver
        client = Client()
        failures = []
        for route in SMOKE_GET_ROUTES:
            response = client.get(route, HTTP_HOST="localhost")
            if response.status_code != 200:
                failures.append(f"GET {route} -> {response.status_code}")
        upcoming = LotteryDates.get_upcoming_draw_dates(1)
        if upcoming:
            response = client.post(
                "/lottery_checker/api/check-draw/",
                data=json.dumps(
                    {"draw_date": upcoming[0], "number": "123456"}
                ),
                content_type="application/json",
                HTTP_HOST="localhost",
            )
            body = response.json()
            if not (response.status_code == 200 and body.get("success")):
                failures.append(f"POST check-draw -> {response.status_code}")
        if failures:
            raise CommandError("smoke failures:\n" + "\n".join(failures))
        self.stdout.write(f"smoked {len(SMOKE_GET_ROUTES)} routes + check-draw API")

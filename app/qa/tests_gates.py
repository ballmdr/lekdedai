"""Task 27: performance, accessibility และ compatibility gate.

Static analysis จาก HTML ที่เรนเดอร์จริง + query budget ต่อ route
(ไม่ต้องพึ่ง browser/Lighthouse — ตรวจสิ่งที่ตรวจได้ในเครื่อง และกัน regression).
"""
import re

from bs4 import BeautifulSoup
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

# route -> จำนวน query สูงสุดที่ยอมรับได้ (กัน N+1 หลุดเข้ามาใหม่)
QUERY_BUDGET = {
    "/": 25,
    "/dreams/": 15,
    "/lottery_checker/": 15,
    "/notebook/": 15,
    "/lotto_stats/": 20,
    "/news/": 15,
    "/ai/": 15,
    "/ai/history/": 15,
    "/ai/accuracy/": 10,
    "/ai/ensemble/history/": 10,
    "/ai/data-sources/": 20,
    "/lotto_formula/": 15,
    "/lotto_formula/calculator/": 10,
    "/privacy/": 5,
    "/terms/": 5,
    "/contact/": 10,
}

A11Y_PAGES = [
    "/", "/dreams/", "/lottery_checker/", "/notebook/", "/lotto_stats/",
    "/news/", "/ai/", "/ai/history/", "/ai/accuracy/",
    "/ai/ensemble/history/", "/ai/data-sources/", "/lotto_formula/",
    "/lotto_formula/calculator/", "/privacy/", "/terms/", "/contact/",
]


class QueryBudgetTests(TestCase):
    """Task 27: performance budget ต่อ route (นับ query จริง)."""

    def test_routes_within_query_budget(self):
        failures = []
        for route, budget in QUERY_BUDGET.items():
            with CaptureQueriesContext(connection) as ctx:
                response = self.client.get(route, HTTP_HOST="localhost")
            if response.status_code != 200:
                failures.append(f"{route}: status {response.status_code}")
                continue
            if len(ctx) > budget:
                failures.append(f"{route}: {len(ctx)} queries > budget {budget}")
        self.assertEqual(failures, [], "เกิน query budget: " + "; ".join(failures))


class AccessibilityGateTests(TestCase):
    """Task 27: accessibility gate จาก HTML จริง (critical violations)."""

    def _soup(self, route):
        html = self.client.get(route, HTTP_HOST="localhost").content.decode()
        return BeautifulSoup(html, "html.parser")

    def test_every_page_has_single_h1(self):
        failures = []
        for route in A11Y_PAGES:
            soup = self._soup(route)
            h1s = soup.find_all("h1")
            if len(h1s) != 1:
                failures.append(f"{route}: {len(h1s)} h1")
        self.assertEqual(failures, [], "; ".join(failures))

    def test_inputs_have_accessible_name(self):
        failures = []
        for route in A11Y_PAGES:
            soup = self._soup(route)
            for inp in soup.find_all("input"):
                if inp.get("type") == "hidden":
                    continue
                if inp.get("aria-label") or inp.get("aria-labelledby"):
                    continue
                input_id = inp.get("id")
                if input_id and soup.find("label", attrs={"for": input_id}):
                    continue
                if inp.find_parent("label"):
                    continue
                failures.append(f"{route}: input#{input_id or '?'}")
            for select in soup.find_all("select"):
                if select.get("aria-label"):
                    continue
                select_id = select.get("id")
                if select_id and soup.find("label", attrs={"for": select_id}):
                    continue
                if select.find_parent("label"):
                    continue
                failures.append(f"{route}: select#{select_id or '?'}")
        self.assertEqual(failures, [], "input/select ไม่มี label: " + "; ".join(failures))

    def test_images_have_alt(self):
        failures = []
        for route in A11Y_PAGES:
            soup = self._soup(route)
            for img in soup.find_all("img"):
                if not img.has_attr("alt"):
                    failures.append(f"{route}: img {img.get('src', '?')[:40]}")
        self.assertEqual(failures, [], "; ".join(failures))

    def test_no_dead_hash_links(self):
        failures = []
        for route in A11Y_PAGES:
            soup = self._soup(route)
            for a in soup.find_all("a", href="#"):
                failures.append(f"{route}: {a.get_text(strip=True)[:30]}")
        self.assertEqual(failures, [], "; ".join(failures))

    def test_buttons_have_accessible_name(self):
        failures = []
        for route in A11Y_PAGES:
            soup = self._soup(route)
            for btn in soup.find_all("button"):
                if btn.get("aria-label") or btn.get_text(strip=True):
                    continue
                failures.append(f"{route}: button {btn.get('id', '?')}")
        self.assertEqual(failures, [], "ปุ่มไม่มีชื่อ: " + "; ".join(failures))

    def test_form_controls_have_id_for_js(self):
        """input/select ที่มี label for= ต้องมี id ตรงกันจริง."""
        for route in A11Y_PAGES:
            soup = self._soup(route)
            ids = {tag.get("id") for tag in soup.find_all(["input", "select", "textarea"])}
            for label in soup.find_all("label", attrs={"for": True}):
                self.assertIn(
                    label["for"], ids,
                    f"{route}: label for={label['for']} ไม่มี control รองรับ",
                )


class CompatibilityGateTests(TestCase):
    """Task 27: charset/viewport/lang + static served ถูกต้อง."""

    def test_html_metadata_present(self):
        for route in A11Y_PAGES:
            html = self.client.get(route, HTTP_HOST="localhost").content.decode()
            self.assertIn('<html lang="th"', html, route)
            self.assertIn('charset="UTF-8"', html, route)
            self.assertIn('name="viewport"', html, route)
            self.assertIn("width=device-width", html, route)

    def test_static_assets_served(self):
        for path in (
            "/static/css/tailwind.css",
            "/static/css/theme.css",
            "/static/js/format.js",
        ):
            res = self.client.get(path, HTTP_HOST="localhost")
            self.assertEqual(res.status_code, 200, path)

    def test_no_inline_handler_with_missing_function(self):
        """onclick/onsubmit ที่เรียกฟังก์ชัน ต้องมีนิยามในหน้าเดียวกัน (กันล้มเงียบ)."""
        call_re = re.compile(r'on(?:click|submit)="([A-Za-z_][A-Za-z0-9_]*)\s*\(', re.I)
        failures = []
        for route in A11Y_PAGES:
            html = self.client.get(route, HTTP_HOST="localhost").content.decode()
            for name in set(call_re.findall(html)):
                defined = re.search(
                    rf"(function\s+{name}\b|\b{name}\s*=\s*(function|async|\(|class))",
                    html,
                )
                if not defined:
                    failures.append(f"{route}: {name}()")
        self.assertEqual(failures, [], "onclick ไม่มี function: " + "; ".join(failures))

    def test_security_headers_in_production(self):
        from django.test import override_settings

        with override_settings(DEBUG=False):
            res = self.client.get("/", HTTP_HOST="localhost")
        self.assertEqual(res.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(res.headers.get("X-Frame-Options"), "DENY")
        self.assertEqual(res.headers.get("Referrer-Policy"), "same-origin")

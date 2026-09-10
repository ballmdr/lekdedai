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

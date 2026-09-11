# Testing & Quality Gate (Task 21)

คำสั่งมาตรฐานคำสั่งเดียว (ล้มทันทีเมื่อผิด):

```bash
# local (venv + env)
$env:SECRET_KEY="local-dev-only"; $env:DEBUG="True"
.\.venv\Scripts\python app/manage.py quality_gate

# CI (ดู .github/workflows/ci.yml, DEBUG=False + SQLite)
python app/manage.py quality_gate
```

ขั้นตอนใน gate ตามลำดับ:

1. `manage.py check` และ `check --deploy`
2. `makemigrations --check` (ห้ามมี migration ค้าง)
3. `migrate`
4. test suite 8 แอป (lottery_checker, ai_engine, news, lotto_formula, dreams, notebook, lotto_stats, home)
5. `collectstatic`
6. smoke: GET 16 routes สำคัญ + POST `check-draw` (งวดอนาคตต้อง pending สำเร็จ)

เพิ่ม regression test ใหม่ให้วางใน `tests.py` ของแอปนั้น ๆ แล้ว gate จะรันให้อัตโนมัติ
(ไม่ต้องแก้รายชื่อที่ไหน) ส่วน route ใหม่ที่ต้อง smoke ให้เพิ่มใน
`SMOKE_GET_ROUTES` ของ `app/qa/management/commands/quality_gate.py`.

## Staging / Production (Task 22, ไม่ใช้ Docker)

- production รันด้วย gunicorn ผ่าน systemd (`deploy/lekdedai.service`) ห้าม `runserver`
- deploy ด้วย `deploy/deploy.sh`: pull → migrate → collectstatic → `check --deploy` → restart
  ขั้นไหนล้มหยุดทันที ไม่ restart ทับของดี
- ต้องตั้งใน `.env` ของเครื่องจริงก่อน: `SECRET_KEY`, `ALLOWED_HOSTS`,
  `DATABASE_URL` (Postgres), `DJANGO_SUPERUSER_PASSWORD` (ดู `.env.example`)
- เปิด TLS ข้างหน้าแล้วค่อยเปิด `SECURE_SSL_REDIRECT`, `*_COOKIE_SECURE`, `SECURE_HSTS_SECONDS`
- หมายเหตุ: gunicorn รันบน Linux เท่านั้น ตรวจบน Windows ไม่ได้ —
  ความถูกต้องของ WSGI/settings ตรวจด้วย `check --deploy` + `quality_gate` แทน

## Security (Task 23)

- mutation endpoint ทุกตัว: staff-only (ยกเว้นที่ผู้ใช้ต้องใช้เอง: comment/feedback/
  วิเคราะห์ฝัน/บันทึกสูตร/ตรวจหวย) + CSRF + audit log (`AUDIT user=...`)
- public JSON API: rate limit ต่อ IP (`app/utils/rate_limit.py`, ค่า default ต่อ view)
  + จำกัด body 4KB (`read_json_body`) + timeout ปลายทาง
- error 4xx/5xx ส่งข้อความทั่วไปเสมอ (`utils.api.api_server_error`, dev เห็น detail)
  ห้าม `str(e)` ออก response
- ทดสอบ abuse ด้วย `RATELIMIT_OVERRIDES = {"module.view": "2/m"}` ใน tests
  (cache ใช้ร่วมกันทั้ง process — `cache.clear()` ก่อน test ที่กำหนด rate เอง)
- dependency scan: `pip-audit -r requirements.txt` (ต้องอัปเกรดแล้วยิงซ้ำ)
- ค้าง: Django 4.2 EOL มี CVE ที่แก้เฉพาะสาย 5.2+ — ต้องวางแผนย้าย Django 5.x แยก
  (งานใหญ่ แยก task ต่างหาก ไม่รวมใน Task 23)

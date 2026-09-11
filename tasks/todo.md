# LekdeDai Delivery Checklist

เอกสารรายละเอียด: `tasks/plan.md`

## ระยะที่ 0: ยืนยันฐานระบบ

- [x] Task 1 — ทำแผนผัง runtime และเลือกหน้าบ้านที่ใช้งานจริง (Django = production, Next.js/React = prototype; หน้าแรก+ตรวจหวย 200 local)
- [x] Task 2 — คืน dependency วันที่หวยและทำให้ระบบเริ่มได้ (`app/utils/lottery_dates.py`, `manage.py check` 0 issues)
- [x] Task 3 — สร้าง baseline ที่รันซ้ำได้ (`.env.example` + `setup_local.ps1`, local venv, SQLite, ไม่ใช้ Docker)

### Checkpoint A

- [x] Django checks และ migrations ผ่าน
- [x] URL หลักไม่มี import error
- [x] ระบุ frontend production owner แล้ว
- [x] เริ่มระบบจากเครื่องใหม่ได้ตามเอกสาร

## ระยะที่ 1: ความปลอดภัยและความน่าเชื่อถือ

- [x] Task 4 — ปิดช่องทางเปลี่ยนข้อมูลโดยไม่มีสิทธิ์ (clear/refresh/bulk + ai ingestion = staff-only + POST, 13 tests เขียว)
- [x] Task 5 — ลบข้อมูลสาธิตออกจากเส้นทางจริง (score แทน confidence, empty state ซื่อสัตย์, mock ingestion gated, 17 tests เขียว)
- [x] Task 6 — กำหนดเจ้าของข้อมูลผลหวย (LottoResult canonical + sync valid-only + UI provenance, 20 tests เขียว)
- [x] Task 7 — วางขอบเขตข้อมูลส่วนบุคคล (เลิกเก็บ IP, notice ในฟอร์ม, retention 90 วัน, 23 tests เขียว)

### Checkpoint B

- [x] API สำคัญผ่าน authorization tests
- [x] Production UI ไม่มีข้อมูล mock/fallback ที่สื่อเป็นข้อมูลจริง
- [x] ทบทวนข้อความด้านคะแนนและความแม่นยำแล้ว
- [x] ตรวจเส้นทางเก็บและลบข้อมูลผู้ใช้แล้ว

## ระยะที่ 2: MVP ที่ทำให้คนกลับมาใช้

- [x] Task 8 — ทำหน้าแรกตามงานหลักหนึ่งเส้นทาง (CTA ฝัน→ตรวจผล, nav จริง, ตัด default ปลอม, 24 tests เขียว)
- [x] Task 9 — ทำสมุดเลขแบบไม่ล็อกอิน (localStorage + ผูกงวด + prefill, /notebook/ 200, 26 tests เขียว)
- [x] Task 10 — เชื่อมผลจากฝันเข้าสมุดเลข (ปุ่มบันทึกทีละเลข 3 จุด + prefill, 30 tests เขียว)
- [x] Task 11 — ตรวจผลและสร้างประวัติงวด (check-draw read-only: won/lost/pending/stale/error; กติกา 2/3/6 หลักรวมศูนย์นำหน้า; ปุ่มตรวจผลทั้งหมดใน notebook; 74 tests เขียว)
- [x] Task 12 — ปิดข้อบกพร่อง UX ที่ยังมองเห็นได้ (formatter ฝันปลอดภัยไฟล์เดียวใช้ 2 หน้า, heading h1→h2→h3, ตัวอย่างเลขตรงคู่มือ, inline error แทน alert, 78 tests เขียว)
- [x] Task 13 — กำหนดนิยามและแก้ความถูกต้องของสถิติ (แยกเลขท้าย 2 ตัวกับเลขคู่ในรางวัลที่ 1 ทั้งคำนวณ/ชื่อ/UI; fixture 5 งวดรวมเลขซ้ำ+ศูนย์นำหน้าตรงมือ; 92 tests เขียว)
- [x] Task 14 — ทำ contract สูตรหวยและ seed ที่ใช้ production ได้ (code/version/specs/approved + migration; dispatch ตาม code; seed idempotent ไม่สร้างผล/วัดปลอม + ไม่ล้างผลวัดเดิม; ผูกเข้า setup; 100 tests เขียว)
- [x] Task 15 — เชื่อมสูตรกับผลจริงและวัดผลย้อนหลังอย่างซื่อสัตย์ (บันทึกเฉพาะงวดหน้า + recompute กันปลอม, กติกาตรวจประกาศชัด, verify command พร้อม numerator/denominator/ช่วงวันที่, UI ผลย้อนหลัง/รอตรวจ, 111 tests เขียว)
- [x] Task 16 — คืนทะเบียนแหล่งข่าวและ provenance (registry version-controlled 4 แหล่งที่ยืนยันดึงได้จริง, seed idempotent ไม่ล้าง timestamp, หน้า data-sources โชว์สำเร็จ/ล้มเหลวล่าสุด, 115 tests เขียว)
- [x] Task 17 — ทำ RSS ingestion เป็นเส้นทางหลัก (service แยก testable + normalize/dedupe/hash/provenance + draft/published ตามนโยบาย + AI best-effort + dry-run; fixture offline + mocked network; dry-run + จริงกับ feed ไทยรัฐ/INN ได้ 18 ข่าว; 125 tests เขียว)
- [x] Task 18 — ทำ category scraper เป็น fallback พร้อม editorial gate (รวม scraper พัง 2 ตัวเป็น owner เดียว + ลบของเก่า; รันเฉพาะเมื่อ RSS เงียบ; draft เสมอ + admin อนุมัติ/ปฏิเสธ; กันซ้ำแม้ URL เปลี่ยน; staging ได้ร่างจริง 3 ข่าว; 138 tests เขียว)
- [x] Task 19 — เชื่อมข่าวที่ผ่านการคัดเข้าสู่หน้าเว็บ (partial ที่มาชุดเดียวทุกหน้า: source link/วันเผยแพร่/วันดึง/ป้ายวิเคราะห์; banner ตรง ingestion failure/stale; draft ไม่โผล่; 145 tests เขียว)
- [x] Task 20 — ทำ metadata และ readiness gate ของ AI prediction (is_ready/meta/stale ทั้ง 2 ระบบ + featured gate; เลิกสร้างอัตโนมัติเมื่อเปิดหน้า; partial ชุดเดียว 3 หน้า; แก้สเกล ensemble + วิเคราะห์โดย v; stale/incomplete ไม่โชว์ confidence; 160 tests เขียว)

### Checkpoint C

- [ ] เส้นทาง วิเคราะห์ → เลือก → บันทึก → ตรวจผล ผ่าน end-to-end
- [ ] เส้นทาง ข่าว/สถิติ/สูตร → เลือกเลข → บันทึก → ตรวจผล ผ่าน end-to-end
- [ ] empty/error/stale states ทำงานถูกต้อง
- [ ] สูตร ข่าว สถิติ และ AI ไม่มีข้อมูลสุ่มหรือ metadata กำกวม
- [ ] backend tests และ browser tests สำคัญผ่าน
- [ ] เจ้าของผลิตภัณฑ์ทดลองบนมือถือจริง

## ระยะที่ 3: เตรียม staging และ production

- [ ] Task 21 — สร้าง automated quality gate
- [ ] Task 22 — แยก production runtime และจัดการ secrets
- [ ] Task 23 — ปิดช่องโหว่ endpoint และจำกัดการใช้งานเกินขอบเขต
- [ ] Task 24 — ตั้ง schedule และ freshness control
- [ ] Task 25 — เพิ่ม observability, backup และ rollback
- [ ] Task 26 — จัดทำนโยบายผู้ใช้และสิทธิ์เนื้อหา
- [ ] Task 27 — ทำ performance, accessibility และ compatibility gate

### Checkpoint D

- [ ] CI/deploy/browser smoke tests ผ่านจาก clean build
- [ ] production secrets/config/security ผ่าน review
- [ ] scheduler, freshness, alerts, backup, restore และ rollback ผ่าน rehearsal
- [ ] provenance ของสูตร ข่าว สถิติ AI และผลหวยครบ
- [ ] policy/contact/disclaimer และ accessibility gate ผ่าน

## ระยะที่ 4: Beta และเปิดสาธารณะ

- [ ] Task 28 — เพิ่ม analytics ขั้นต่ำแบบรักษาความเป็นส่วนตัว
- [ ] Task 29 — ทำ staging dress rehearsal ครบหนึ่งรอบงวด
- [ ] Task 30 — เปิด closed beta อย่างน้อยสองงวด
- [ ] Task 31 — เปิด public แบบ staged rollout

### Checkpoint E

- [ ] มี activation baseline
- [ ] มี cross-draw retention อย่างน้อยสองงวด
- [ ] ระบุฟีเจอร์ที่ทำให้ผู้ใช้กลับมาได้
- [ ] มีหลักฐานความตั้งใจจ่าย หรือข้อสรุปว่ายังไม่ควรสร้าง billing

## ระยะที่ 5: ทดลองรายได้

- [ ] เลือกทดลอง A — สมุดเลขแบบสมาชิก ตามหลักฐานการใช้ซ้ำ
- [ ] เลือกทดลอง B — เครื่องมือทำคอนเทนต์ ตามหลักฐานการแชร์/เจ้าของเพจ
- [ ] เลือกทดลอง C — Widget/API ตามความสนใจจาก partner
- [ ] ประเมิน D — โฆษณา/สปอนเซอร์ หลังมี traffic และตรวจนโยบายล่าสุด
- [ ] ทดลองทีละสมมติฐานและบันทึกเกณฑ์เดินหน้า/หยุดก่อนเริ่ม

## บันทึกการส่งมอบแต่ละรอบ

- [ ] สรุปสิ่งที่เปลี่ยนและเหตุผล
- [ ] ระบุไฟล์และ migration ที่กระทบ
- [ ] แนบหลักฐานการทดสอบ
- [ ] บันทึกข้อจำกัดและสิ่งที่ยังไม่ยืนยัน
- [ ] ระบุ task ถัดไปและ dependency

"""Task 25: backup/restore ฐานข้อมูล (รองรับ SQLite เต็มรูปแบบ, Postgres ผ่าน pg_dump).

SQLite ใช้ sqlite3 backup API (snapshot สอดคล้อง ไม่ต้องหยุด web).
ไฟล์: <BACKUP_DIR>/lekdedai-YYYYMMDD-HHMMSS.sqlite3.gz (+ .sha256).
"""
import gzip
import hashlib
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.db import connection


def backup_dir():
    path = Path(getattr(settings, "BACKUP_DIR", None) or (settings.BASE_DIR.parent / "backups"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def is_sqlite():
    return connection.vendor == "sqlite"


def sqlite_db_path():
    return Path(connection.settings_dict["NAME"])


def _open_source_ro():
    """เปิด SQLite ต้นทางแบบอ่านอย่างเดียว (รองรับทั้งไฟล์, :memory:, URI)."""
    name = connection.settings_dict["NAME"]
    if not isinstance(name, str) or name == ":memory:" or "?" in name or name.startswith("file:"):
        return sqlite3.connect(name, uri=isinstance(name, str) and name.startswith("file:"))
    return sqlite3.connect(f"file:{name}?mode=ro", uri=True)


def backup_sqlite(dest_dir=None, keep=7, now=None):
    """backup SQLite -> ไฟล์ .gz คืน path; ตัดของเก่าเหลือ keep ไฟล์."""
    dest_dir = Path(dest_dir) if dest_dir else backup_dir()
    dest_dir.mkdir(parents=True, exist_ok=True)
    stamp = (now or datetime.now()).strftime("%Y%m%d-%H%M%S")
    dest = dest_dir / f"lekdedai-{stamp}.sqlite3.gz"

    src = _open_source_ro()
    try:
        raw = dest.with_suffix("").with_suffix(".tmp")
        dst = sqlite3.connect(str(raw))
        try:
            src.backup(dst)
        finally:
            dst.close()
        with open(raw, "rb") as f_in, gzip.open(dest, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
        raw.unlink(missing_ok=True)
    finally:
        src.close()

    digest = hashlib.sha256(dest.read_bytes()).hexdigest()
    (dest.parent / (dest.name + ".sha256")).write_text(f"{digest}  {dest.name}\n")
    prune_backups(dest_dir, keep=keep)
    return dest


def prune_backups(dest_dir=None, keep=7):
    """เหลือไฟล์ .sqlite3.gz ใหม่สุด keep ไฟล์ (พร้อม sidecar)."""
    dest_dir = Path(dest_dir) if dest_dir else backup_dir()
    files = sorted(dest_dir.glob("lekdedai-*.sqlite3.gz"))
    for old in files[:-keep] if len(files) > keep else []:
        old.unlink(missing_ok=True)
        (old.parent / (old.name + ".sha256")).unlink(missing_ok=True)
    return max(0, len(files) - keep)


def restore_sqlite(backup_file, target=None):
    """คืนไฟล์ .gz ทับ SQLite ปลายทาง (ต้องหยุด web ก่อน — ดู runbook).

    คืนจำนวนตารางที่ตรวจพบหลังคืน (0 = ไฟล์เสีย).
    """
    import gzip as _gzip

    target = Path(target) if target else sqlite_db_path()
    data = _gzip.decompress(Path(backup_file).read_bytes())
    target.write_bytes(data)
    conn = sqlite3.connect(str(target))
    try:
        tables = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
        ).fetchone()[0]
    finally:
        conn.close()
    return tables

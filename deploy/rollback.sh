#!/bin/bash
# Rollback แบบไม่ใช้ Docker: ย้อนโค้ด -> migrate -> collectstatic -> restart
# ขั้นไหนล้มหยุดทันที (set -e) — backup ฐานข้อมูลก่อนเสมอ (ดู docs/OPERATIONS.md)
set -e

APP_DIR="${APP_DIR:-/opt/lekdedai}"
SERVICE_NAME="${SERVICE_NAME:-lekdedai}"
REF="${1:?usage: rollback.sh <commit-or-tag>}"

cd "$APP_DIR"
echo "==> backup ฐานข้อมูลก่อนย้อน"
.venv/bin/python app/manage.py backup_db --keep 14

echo "==> checkout $REF"
git fetch origin
git rev-parse --verify "$REF^{commit}" >/dev/null
git checkout "$REF"

echo "==> migrate (ล้มแล้วหยุด)"
.venv/bin/python app/manage.py migrate --noinput

echo "==> collectstatic (ล้มแล้วหยุด)"
.venv/bin/python app/manage.py collectstatic --noinput

echo "==> restart ${SERVICE_NAME}"
sudo systemctl restart "$SERVICE_NAME"
sudo systemctl is-active --quiet "$SERVICE_NAME"

echo "Rollback OK ($REF)"

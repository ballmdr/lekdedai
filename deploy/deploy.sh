#!/bin/bash
# Deploy แบบไม่ใช้ Docker: pull -> migrate -> collectstatic -> restart.
# ขั้นไหนล้มหยุดทันที (set -e) ไม่ restart service ที่พังทับของดี
set -e

APP_DIR="${APP_DIR:-/opt/lekdedai}"
SERVICE_NAME="${SERVICE_NAME:-lekdedai}"

cd "$APP_DIR"
echo "==> git pull"
git pull --ff-only

echo "==> migrate (ล้มแล้วหยุด)"
.venv/bin/python app/manage.py migrate --noinput

echo "==> collectstatic (ล้มแล้วหยุด)"
.venv/bin/python app/manage.py collectstatic --noinput

echo "==> check --deploy"
.venv/bin/python app/manage.py check --deploy

echo "==> restart ${SERVICE_NAME}"
sudo systemctl restart "$SERVICE_NAME"
sudo systemctl is-active --quiet "$SERVICE_NAME"

echo "Deploy OK"

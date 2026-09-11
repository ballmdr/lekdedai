# Rebuild Tailwind CSS แล้วคัดลอก static ไป STATIC_ROOT (สำหรับ DEBUG=False/whitenoise)
# Usage: powershell -ExecutionPolicy Bypass -File build_css.ps1
$ErrorActionPreference = "Stop"

npx --yes tailwindcss@3.4.17 -c assets/tailwind/tailwind.config.js -i assets/tailwind/input.css -o app/static/css/tailwind.css --minify
.\.venv\Scripts\python app/manage.py collectstatic --noinput
Write-Output "Done. Tailwind rebuilt and static collected."

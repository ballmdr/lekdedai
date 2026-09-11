# Local setup for Windows (PowerShell) - no Docker required.
# Usage: powershell -ExecutionPolicy Bypass -File setup_local.ps1
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath ".venv")) {
  python -m venv .venv
}
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\pip install -r requirements.txt

if (-not (Test-Path -LiteralPath ".env")) {
  Copy-Item -Path ".env.example" -Destination ".env"
  Write-Output "Created .env from .env.example - edit SECRET_KEY before sharing."
}

$env:SECRET_KEY = "local-dev-only"
$env:DEBUG = "True"
$env:DJANGO_SUPERUSER_USERNAME = "admin"
$env:DJANGO_SUPERUSER_EMAIL = "admin@lekdedai.com"
$env:DJANGO_SUPERUSER_PASSWORD = "admin123"
.\.venv\Scripts\python app/manage.py migrate --run-syncdb
.\.venv\Scripts\python app/manage.py createsuperuser --noinput
.\.venv\Scripts\python app/manage.py add_dream_data
.\.venv\Scripts\python app/manage.py populate_lottery_data
.\.venv\Scripts\python app/manage.py setup_ai_data_sources --create-sources
.\.venv\Scripts\python app/manage.py collectstatic --noinput
.\.venv\Scripts\python app/manage.py check
Write-Output "Done. Run: .\.venv\Scripts\python app/manage.py runserver"

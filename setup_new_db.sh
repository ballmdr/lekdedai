#!/bin/bash
echo "🚀 Setting up new database..."

# รอให้ database พร้อม
echo "⏳ Waiting for database..."
sleep 10

# สร้าง migrations ใหม่
echo "📝 Creating migrations..."
python manage.py makemigrations home
python manage.py makemigrations dreams
python manage.py makemigrations stats
python manage.py makemigrations news
python manage.py makemigrations ai_engine

# Migrate
echo "🔄 Running migrations..."
python manage.py migrate

# สร้าง superuser
echo "👤 Creating superuser..."
python manage.py shell << END
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@lekdedai.com', 'admin123')
    print('✅ Superuser created: admin/admin123')
else:
    print('ℹ️ Superuser already exists')
END

# เพิ่มข้อมูลตัวอย่าง
echo "📊 Adding sample data..."
python manage.py add_dream_data
python manage.py add_lottery_data
python manage.py add_news_data

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

echo "✅ Setup completed!"
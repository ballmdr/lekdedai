#!/bin/bash
echo "🆕 Fresh Installation of LekDedAI"
echo "================================"

# Stop and clean
echo "🧹 Cleaning old data..."
docker-compose down -v
rm -rf postgres-data/

# Build
echo "🔨 Building Docker images..."
docker-compose build --no-cache

# Database setup
echo "💾 Setting up database..."
docker-compose up -d db
sleep 15

# Run migrations and setup
echo "🔄 Running setup..."
docker-compose run --rm web bash -c "
python manage.py makemigrations
python manage.py migrate
python manage.py shell << 'EOF'
from django.contrib.auth.models import User
User.objects.create_superuser('admin', 'admin@lekdedai.com', 'admin123')
print('Superuser created')
EOF
python manage.py collectstatic --noinput
"

# Add sample data (optional)
echo "📊 Adding sample data..."
docker-compose run --rm web python manage.py add_dream_data || true
docker-compose run --rm web python manage.py add_lottery_data || true
docker-compose run --rm web python manage.py add_news_data || true

# Start all services
echo "🚀 Starting all services..."
docker-compose up -d

echo "✅ Installation completed!"
echo ""
echo "📌 Access info:"
echo "- Website: http://localhost:8000"
echo "- Admin: http://localhost:8000/admin"
echo "- Wagtail CMS: http://localhost:8000/cms"
echo "- Username: admin"
echo "- Password: admin123"
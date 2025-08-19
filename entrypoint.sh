#!/bin/sh

echo "Waiting for postgres..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "PostgreSQL started"

# Run migrations
python manage.py migrate

# Create superuser if it doesn't exist
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@lekdedai.com', 'admin123')
    print('Superuser created')
else:
    print('Superuser already exists')
END

# Collect static files
python manage.py collectstatic --noinput

# Start server
exec "$@"
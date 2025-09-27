FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    postgresql-client \
    netcat-traditional \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app /app/

# Create necessary directories
RUN mkdir -p /app/media /app/static /app/staticfiles

# Set proper permissions
RUN chmod +x /app/manage.py

EXPOSE 8000

# Use entrypoint script if it exists, otherwise run Django directly
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    netcat-traditional \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ใช้ requirements แบบง่ายก่อน
COPY requirements-simple.txt /app/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY ./app /app/

RUN mkdir -p /app/media /app/static /app/staticfiles

EXPOSE 8000

# รันแบบง่ายๆ ก่อน
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
# Simple Dockerfile for Django-based meter dashboard
# Uses a slim Python base and installs only the Django app requirements

FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# System deps needed for some Python packages to build wheels on arm64
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libfreetype6-dev \
    libpng-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# No corporate SSL customizations; rely on default CA bundle inside base image.

# Install only the Django app requirements to keep image smaller
COPY meter_dashboard/requirements.txt /app/meter_dashboard/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/meter_dashboard/requirements.txt

# Copy the full project
COPY . /app

# Environment toggles (override at runtime as needed)
# Keep secrets and DB settings out of the image; pass via docker-compose or -e
ENV DJANGO_SETTINGS_MODULE=meter_dashboard.settings

# Expose Django dev server port
EXPOSE 8000

# Default command: run Django development server (suitable for quick testing)
# For production, consider using gunicorn/uvicorn behind a reverse proxy.
CMD ["python", "meter_dashboard/manage.py", "runserver", "0.0.0.0:8000"]

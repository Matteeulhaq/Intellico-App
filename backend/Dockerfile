FROM python:3.11-slim

# Install build deps if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .

# Install Python deps
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy app
COPY . .

# Create storage folder
RUN mkdir -p /app/storage

ENV FLASK_APP=app.main
ENV FLASK_ENV=production

EXPOSE 5000

# Use gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app.main:app", "--workers", "4", "--threads", "4"]

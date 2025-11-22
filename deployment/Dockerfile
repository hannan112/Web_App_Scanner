# Production Dockerfile for Backend
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    python3-dev \
    libssl-dev \
    libffi-dev \
    curl \
    wget \
    git \
    nodejs \
    npm \
    unzip \
    net-tools \
    netcat-openbsd \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install feroxbuster
RUN curl -sL https://raw.githubusercontent.com/epi052/feroxbuster/master/install-nix.sh | bash \
    && mv feroxbuster /usr/local/bin/feroxbuster \
    && chmod +x /usr/local/bin/feroxbuster

# Install Go for Nuclei
RUN curl -OL https://golang.org/dl/go1.21.3.linux-amd64.tar.gz \
    && tar -C /usr/local -xzf go1.21.3.linux-amd64.tar.gz \
    && rm go1.21.3.linux-amd64.tar.gz
ENV PATH=$PATH:/usr/local/go/bin:/root/go/bin

# Install ProjectDiscovery tools
RUN go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest || true \
    && go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest || true \
    && go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest || true \
    && mkdir -p /root/nuclei-templates \
    && (nuclei -update-templates || true)

# Install Wappalyzer
RUN npm install -g wappalyzer

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn psycopg2-binary

# Create directories
RUN mkdir -p /app/logs /app/media /app/static

# Copy application code
COPY backend /app

# Collect static files
# Note: We need a dummy secret key for collectstatic
RUN python manage.py collectstatic --noinput --settings=backend.settings

# Expose port
EXPOSE 8000

# Start Gunicorn
CMD ["gunicorn", "backend.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "4", "--timeout", "120"]

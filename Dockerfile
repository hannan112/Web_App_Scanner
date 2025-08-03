# Start with Python 3.10 as a base image
FROM python:3.10-slim

# Set a working directory
WORKDIR /app

# Add metadata
LABEL maintainer="Security Scanner Team"
LABEL version="1.0"
LABEL description="Security scanning application with integrated mature tools"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

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
    && rm -rf /var/lib/apt/lists/*

# Install Go for Nuclei
RUN curl -OL https://golang.org/dl/go1.21.3.linux-amd64.tar.gz \
    && tar -C /usr/local -xzf go1.21.3.linux-amd64.tar.gz \
    && rm go1.21.3.linux-amd64.tar.gz
ENV PATH=$PATH:/usr/local/go/bin:/root/go/bin

# Install Nuclei (with error handling)
RUN go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest || true \
    && mkdir -p /root/nuclei-templates \
    && (nuclei -update-templates || true)

# Install Wappalyzer via npm
RUN npm install -g wappalyzer

# Set up OWASP ZAP Python API
RUN pip install --no-cache-dir python-owasp-zap-v2.4
ENV ZAP_HOST=zap
ENV ZAP_PORT=8080
ENV ZAP_API_KEY=changeme123

# Set up Python environment
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
    wheel \
    setuptools \
    cryptography>=39.0.0 \
    requests>=2.26.0 \
    beautifulsoup4>=4.10.0 \
    lxml>=4.6.3 \
    dnspython>=2.2.0

# Install SSLyze
RUN pip install --no-cache-dir sslyze>=5.1.0

# Create and customize requirements.txt
# Removing the problematic wappalyzer-python package
RUN echo "Django>=5.2,<6.0" > requirements.txt \
    && echo "djangorestframework>=3.14.0" >> requirements.txt \
    && echo "djangorestframework-simplejwt>=5.2.2" >> requirements.txt \
    && echo "django-cors-headers>=4.0.0" >> requirements.txt \
    && echo "django-allauth>=0.54.0" >> requirements.txt \
    && echo "dj-rest-auth>=4.0.1" >> requirements.txt \
    && echo "psycopg2-binary>=2.9.5" >> requirements.txt \
    && echo "python-owasp-zap-v2.4>=0.0.20" >> requirements.txt \
    && echo "sslyze>=5.1.0" >> requirements.txt \
    && echo "dnspython>=2.3.0" >> requirements.txt \
    && echo "python-dotenv>=1.0.0" >> requirements.txt \
    && echo "requests>=2.28.2" >> requirements.txt \
    && echo "beautifulsoup4>=4.11.2" >> requirements.txt \
    && echo "pyjwt>=2.6.0" >> requirements.txt

# Install application dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/backend /app/scanning /app/projects /app/authentication

# Copy the application code
# Adjust the file paths to match your structure
COPY ./backend/backend_context_code.txt .
COPY docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh

# Extract files from backend_context_code.txt (you need to replace this with your actual file structure)
RUN mkdir -p backend scanning projects authentication \
    && python -c "\
import os, re\n\
\n\
# Read the backend code\n\
with open('backend_context_code.txt', 'r') as f:\n\
    content = f.read()\n\
\n\
# Extract file sections\n\
file_sections = re.findall(r'### (.*?)\\n\\n```(.*?)```', content, re.DOTALL)\n\
\n\
# Create and write files\n\
for file_path, file_content in file_sections:\n\
    # Skip files we don't need\n\
    if file_path in ['backend_context_code.txt', 'collect_backend_code.py']:\n\
        continue\n\
    \n\
    # Make sure directory exists\n\
    dir_name = os.path.dirname(file_path)\n\
    if dir_name and not os.path.exists(dir_name):\n\
        os.makedirs(dir_name, exist_ok=True)\n\
    \n\
    # Write the file\n\
    with open(file_path, 'w') as f:\n\
        f.write(file_content)\n\
    \n\
    # Make manage.py executable\n\
    if file_path == 'manage.py':\n\
        os.chmod(file_path, 0o755)\n\
" || echo "Extraction failed, but continuing"

# Create a non-root user to run the application
RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Expose port
EXPOSE 8000

# Set up entrypoint and default command
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
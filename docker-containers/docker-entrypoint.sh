#!/bin/bash
set -e

# Function to wait for a service to be ready
wait_for_service() {
  local host="$1"
  local port="$2"
  local service="$3"
  
  echo "Waiting for $service to be ready at $host:$port..."
  
  while ! nc -z "$host" "$port"; do
    echo "$service is not available yet - sleeping for 2 seconds"
    sleep 2
  done
  
  echo "$service is up and ready!"
}

# Check if database migrations need to be run
if [ -n "$RUN_MIGRATIONS" ]; then
  echo "Running database migrations..."
  python manage.py migrate
fi

# Check if we should collect static files
if [ -n "$COLLECT_STATIC" ]; then
  echo "Collecting static files..."
  python manage.py collectstatic --noinput
fi

# Check if we need to wait for ZAP
if [ -n "$WAIT_FOR_ZAP" ]; then
  wait_for_service "${ZAP_HOST:-zap}" "${ZAP_PORT:-8080}" "ZAP"
fi

# Check if we need to create initial admin user
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ]; then
  echo "Creating/updating superuser..."
  python manage.py createsuperuser --noinput || echo "Superuser already exists or creation failed - continuing..."
fi

# Run setup_tools command if requested
if [ -n "$SETUP_TOOLS" ]; then
  echo "Setting up external scanning tools..."
  python manage.py setup_tools
fi

# Execute the command passed to docker run
exec "$@"
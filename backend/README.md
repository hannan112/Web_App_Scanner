# Security Scanner Backend

A comprehensive web application security scanner built with Django REST Framework. This backend provides passive and active security scanning capabilities with support for multiple security tools and integrations.

## Features

- **Passive Security Scanning**: Analyzes web applications without sending malicious requests
- **Active Security Scanning**: Performs vulnerability testing (in development)
- **Multiple Tool Integrations**: OWASP ZAP, SSLyze, Nuclei, Wappalyzer
- **User Authentication**: JWT-based authentication with social login support
- **Project Management**: Organize and track security scans by project
- **Comprehensive Reporting**: Detailed vulnerability reports and findings
- **RESTful API**: Full API for frontend integration

## Tech Stack

- **Framework**: Django 5.2
- **API**: Django REST Framework
- **Authentication**: JWT (Simple JWT) + Social Auth (AllAuth)
- **Database**: SQLite (development) / PostgreSQL (production)
- **Security Tools**: OWASP ZAP, SSLyze, Nuclei, Wappalyzer
- **Code Quality**: Black, isort, flake8

## Project Structure

```
backend/
├── authentication/          # User authentication and management
├── projects/               # Project management
├── scanning/               # Core scanning functionality
│   ├── discovery/          # Web crawling and discovery
│   ├── integrations/       # Third-party tool integrations
│   ├── models/            # Database models
│   ├── passive/           # Passive scanning analyzers
│   └── utils/             # Utility functions
├── backend/               # Django project settings
├── logs/                  # Application logs
├── venv/                  # Virtual environment
├── requirements.txt       # Python dependencies
├── env.example           # Environment variables template
└── README.md             # This file
```

## Setup Instructions

### Prerequisites

- Python 3.8+
- pip
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd backend
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

### Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Email Settings
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=Security Scanner <noreply@securityscanner.com>

# JWT Settings
JWT_SIGNING_KEY=your-jwt-signing-key-here

# Frontend URL
FRONTEND_URL=http://localhost:3000

# Google OAuth (optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

## Security Tool Setup

### OWASP ZAP
```bash
# Using Docker (recommended)
docker run -p 8080:8080 -p 8090:8090 -i owasp/zap2docker-stable zap.sh -daemon -host 0.0.0.0 -port 8080 -config api.addrs.addr.name=.* -config api.addrs.addr.regex=true -config api.key=your-api-key
```

### SSLyze
```bash
pip install sslyze>=5.1.0
```

### Nuclei
```bash
# Download from https://github.com/projectdiscovery/nuclei/releases
# Or use go install
go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest
```

### Wappalyzer
```bash
pip install python-Wappalyzer
```

## API Documentation

### Authentication Endpoints

- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `POST /api/auth/refresh/` - Refresh JWT token

### Project Endpoints

- `GET /api/projects/` - List user projects
- `POST /api/projects/` - Create new project
- `GET /api/projects/{id}/` - Get project details
- `PUT /api/projects/{id}/` - Update project
- `DELETE /api/projects/{id}/` - Delete project

### Scanning Endpoints

- `POST /api/scanning/scans/` - Start new scan
- `GET /api/scanning/scans/` - List scans
- `GET /api/scanning/scans/{id}/` - Get scan details
- `POST /api/scanning/scans/{id}/stop/` - Stop running scan
- `GET /api/scanning/scans/{id}/results/` - Get scan results

## Development

### Code Quality

The project uses several tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting

Run code quality checks:
```bash
# Format code
black . --line-length=88

# Sort imports
isort .

# Lint code
flake8 .
```

### Running Tests

```bash
python manage.py test
```

### Database Migrations

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate
```

## Security Considerations

- **Environment Variables**: Never commit sensitive data to version control
- **Debug Mode**: Disable DEBUG in production
- **CORS**: Configure CORS_ALLOWED_ORIGINS for production
- **HTTPS**: Use HTTPS in production
- **Secret Key**: Use a strong, unique SECRET_KEY
- **Database**: Use PostgreSQL in production

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run code quality checks
5. Submit a pull request

## License

[Add your license information here]

## Support

For support and questions, please [create an issue](link-to-issues) or contact the development team. 
# Security Scanner Platform

A comprehensive web application security scanner built with Django REST Framework and Next.js. This platform provides passive and active security scanning capabilities with support for multiple security tools and integrations.

## 🚀 Quick Start

This guide will help you set up and run the project on your local machine.

### Prerequisites

- **Python 3.8+**
- **Node.js 18+** and npm
- **Git**

### 🛠️ Setup Instructions

#### 1. Clone the Repository

```bash
git clone <repository-url>
cd Web_App_Scanner
```

#### 2. Backend Setup (Django)

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables template
cp .env.example .env

# Edit .env file with your configuration
# (You can use the default values for development)

# Run database migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Run the development server
python manage.py runserver
```

The backend will be available at `http://localhost:8000`

#### 3. Frontend Setup (Next.js)

Open a new terminal window:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

### 🔧 Environment Configuration

#### Backend Environment Variables

Copy `backend/.env.example` to `backend/.env` and configure the following variables:

- `SECRET_KEY`: Django secret key (generate a unique one for production)
- `DEBUG`: Set to `True` for development
- `EMAIL_*`: Email configuration for sending notifications
- `GOOGLE_CLIENT_ID` & `GOOGLE_CLIENT_SECRET`: For Google OAuth (optional)

#### Frontend Environment

The frontend uses environment variables from `frontend/.env.local` (if needed). Check the frontend README for specific requirements.

### 🗄️ Database

The project uses SQLite for development. The database file (`db.sqlite3`) is excluded from version control.

**Important:** Each developer should create their own database by running migrations:
```bash
python manage.py migrate
```

### 📦 Project Structure

```
Web_App_Scanner/
├── backend/              # Django backend application
│   ├── authentication/   # User authentication
│   ├── projects/        # Project management
│   ├── scanning/        # Core scanning functionality
│   ├── manage.py        # Django management script
│   └── requirements.txt # Python dependencies
├── frontend/            # Next.js frontend application
│   ├── src/            # Source code
│   ├── public/         # Static assets
│   └── package.json    # Node dependencies
├── docker-containers/   # Docker configuration
└── README.md           # This file
```

### 🔐 Default Credentials

After creating a superuser, you can log in to the admin panel at:
- URL: `http://localhost:8000/admin/`
- Use the credentials you created with `python manage.py createsuperuser`

### 🧪 Testing

Run tests for the backend:
```bash
cd backend
python manage.py test
```

The frontend doesn't have automated tests set up yet (good first-contribution opportunity). You can at least lint it:
```bash
cd frontend
npm run lint
```

### 🐛 Troubleshooting

#### Backend Issues

1. **ImportError or ModuleNotFoundError**
   - Make sure your virtual environment is activated
   - Run `pip install -r requirements.txt` again

2. **Database errors**
   - Delete the `db.sqlite3` file and run `python manage.py migrate` again
   - Make sure you're in the `backend` directory

3. **Port already in use**
   - Change the port: `python manage.py runserver 8001`
   - Or kill the process using the port

#### Frontend Issues

1. **npm install fails**
   - Clear cache: `npm cache clean --force`
   - Delete `node_modules` and `package-lock.json`, then run `npm install` again

2. **Port already in use**
   - Use a different port: `PORT=3001 npm run dev`

### 📝 Development Workflow

1. **Pull latest changes**
   ```bash
   git pull origin main
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**

4. **Commit and push**
   ```bash
   git add .
   git commit -m "Description of changes"
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request on GitHub**

### 🔗 Useful Links

- **Backend API Documentation**: `http://localhost:8000/api/`
- **Admin Panel**: `http://localhost:8000/admin/`
- **Frontend**: `http://localhost:3000`

### 👥 Contributors

List of contributors:
- [Hannan Ali](https://github.com/hannan112)

### 📄 License

See LICENSE.md for details.

### 🆘 Getting Help

If you encounter any issues:
1. Check the [Troubleshooting](#-troubleshooting) section
2. Review the backend and frontend READMEs in their respective directories
3. Check existing GitHub issues
4. Create a new issue with details about your problem

---

**Note:** The database file (`db.sqlite3`) is not included in this repository. Each developer should create their own local database by running migrations.

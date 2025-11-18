# Local Development Guide

This guide will help you set up the Ideasthesia Creative Prompt Generator on your local machine for development.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Detailed Setup](#detailed-setup)
4. [Running the Application](#running-the-application)
5. [Testing](#testing)
6. [Troubleshooting](#troubleshooting)
7. [Development Workflow](#development-workflow)

---

## Platform-Specific Notes

### Windows Users

This guide includes Windows-specific commands where needed:
- **Git Bash**: Recommended - can run `.sh` scripts and most Unix commands
- **Command Prompt**: Alternative `.bat` scripts provided
- **PowerShell**: Alternative `.ps1` scripts provided
- **WSL**: Can use Linux commands directly

### macOS/Linux Users

Standard Bash commands work throughout this guide.

---

## Prerequisites

Before you begin, ensure you have the following installed on your machine:

### Required Software

- **Node.js** (v14.0.0 or higher)
  - Download from [nodejs.org](https://nodejs.org/)
  - Verify installation: `node --version`

- **Python** (v3.8 or higher)
  - Download from [python.org](https://www.python.org/)
  - Verify installation: `python3 --version`

- **PostgreSQL** (v13 or higher)
  - Download from [postgresql.org](https://www.postgresql.org/download/)
  - Verify installation: `psql --version`

- **Redis** (v6 or higher)
  - macOS: `brew install redis`
  - Ubuntu: `sudo apt-get install redis-server`
  - Windows: [Redis for Windows](https://github.com/microsoftarchive/redis/releases)
  - Verify installation: `redis-cli --version`

- **Git**
  - Download from [git-scm.com](https://git-scm.com/)
  - Verify installation: `git --version`

### API Keys Required

You'll need to obtain the following API keys:

1. **OpenAI API Key** - [Get it here](https://platform.openai.com/api-keys)
2. **Google OAuth Client ID** - [Google Cloud Console](https://console.cloud.google.com/)
3. **PagerDuty API Key** (Optional) - [PagerDuty](https://www.pagerduty.com/)

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/Jdouville8/ideasthesia-creative-prompt-generator.git
cd ideasthesia-creative-prompt-generator

# 2. Install all dependencies
npm run install-all

# 3. Set up environment variables (see Detailed Setup section)
cp frontend/.env.example frontend/.env
cp backend/.env.example backend/.env
cp prompt-service/.env.example prompt-service/.env

# 4. Set up the database
npm run db:setup

# 5. Start all services
npm run dev
```

The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:4000
- **Prompt Service**: http://localhost:5001
- **Prometheus Metrics**: http://localhost:9464/metrics

---

## Detailed Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Jdouville8/ideasthesia-creative-prompt-generator.git
cd ideasthesia-creative-prompt-generator
```

### 2. Install Dependencies

#### Option A: Install All at Once

```bash
npm run install-all
```

#### Option B: Install Manually

```bash
# Frontend dependencies
cd frontend
npm install
cd ..

# Backend dependencies
cd backend
npm install
cd ..

# Python dependencies
cd prompt-service
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

### 3. Set Up PostgreSQL Database

#### Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database and user
CREATE DATABASE writing_prompts;
CREATE USER prompt_user WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE writing_prompts TO prompt_user;
\q
```

#### Run Migrations

```bash
# Navigate to backend directory
cd backend

# Run database migrations
npm run migrate

# Or manually run the SQL schema

# macOS/Linux/Git Bash (Windows):
psql -U prompt_user -d writing_prompts -f database/schema.sql

# Windows Command Prompt:
psql -U prompt_user -d writing_prompts -f database\schema.sql

# Windows PowerShell:
Get-Content database\schema.sql | psql -U prompt_user -d writing_prompts
```

**Database Schema** (`backend/database/schema.sql`):

```sql
-- Users table
CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  google_id VARCHAR(255) UNIQUE NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(255),
  picture TEXT,
  webhook_url TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Prompts table
CREATE TABLE IF NOT EXISTS prompts (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  title VARCHAR(500),
  content TEXT,
  difficulty VARCHAR(50),
  word_count INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Prompt genres junction table
CREATE TABLE IF NOT EXISTS prompt_genres (
  id SERIAL PRIMARY KEY,
  prompt_id INTEGER REFERENCES prompts(id) ON DELETE CASCADE,
  genre VARCHAR(100),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_prompts_user_id ON prompts(user_id);
CREATE INDEX idx_prompts_created_at ON prompts(created_at DESC);
CREATE INDEX idx_prompt_genres_prompt_id ON prompt_genres(prompt_id);
```

### 4. Set Up Redis

#### Start Redis Server

```bash
# macOS/Linux
redis-server

# Or run as a background service
# macOS:
brew services start redis

# Linux (systemd):
sudo systemctl start redis
```

#### Test Redis Connection

```bash
redis-cli ping
# Should return: PONG
```

### 5. Configure Environment Variables

Create `.env` files in each service directory:

#### Frontend (`frontend/.env`)

```bash
# API Configuration
REACT_APP_API_URL=http://localhost:4000

# Google OAuth
REACT_APP_GOOGLE_CLIENT_ID=your_google_client_id_here.apps.googleusercontent.com

# Feature Flags (optional)
REACT_APP_ENABLE_ANALYTICS=false
```

#### Backend (`backend/.env`)

```bash
# Server Configuration
PORT=4000
NODE_ENV=development

# Database
DATABASE_URL=postgresql://prompt_user:your_secure_password@localhost:5432/writing_prompts

# Redis
REDIS_URL=redis://localhost:6379

# JWT Secret (generate a random string)
JWT_SECRET=your_jwt_secret_here_make_it_long_and_random

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id_here.apps.googleusercontent.com

# Webhooks (optional)
WEBHOOK_SECRET=your_webhook_secret_here

# PagerDuty (optional)
PAGERDUTY_API_KEY=your_pagerduty_api_key
PAGERDUTY_ROUTING_KEY=your_pagerduty_routing_key

# OpenTelemetry (optional)
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
```

#### Prompt Service (`prompt-service/.env`)

```bash
# Server Configuration
FLASK_ENV=development
FLASK_APP=app.py
PORT=5001

# OpenAI API
OPENAI_API_KEY=sk-your_openai_api_key_here

# Redis
REDIS_URL=redis://localhost:6379

# Rate Limiting
RATE_LIMIT_PER_MINUTE=30
```

### 6. Generate Secure Secrets

For `JWT_SECRET` and `WEBHOOK_SECRET`, generate random strings:

```bash
# Using Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"

# Using OpenSSL
openssl rand -hex 32

# Using Python
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## Running the Application

### Option 1: Run All Services Together (Recommended)

```bash
# From the root directory
npm run dev
```

This will start:
- Frontend (React) on port 3000
- Backend (Express) on port 4000
- Prompt Service (Flask) on port 5001

### Option 2: Run Services Separately

Open **three separate terminal windows**:

#### Terminal 1: Frontend

```bash
cd frontend
npm start
```

#### Terminal 2: Backend

```bash
cd backend
npm run dev
```

#### Terminal 3: Prompt Service

```bash
cd prompt-service
source venv/bin/activate  # On Windows: venv\Scripts\activate
python app.py
```

### Verify Services Are Running

- Frontend: Open http://localhost:3000 in your browser
- Backend Health Check: `curl http://localhost:4000/health`
- Prompt Service Health Check: `curl http://localhost:5001/health`
- Prometheus Metrics: Open http://localhost:9464/metrics

---

## Testing

### Frontend Tests

```bash
cd frontend

# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Generate coverage report
npm run test:coverage
```

### Backend Tests

```bash
cd backend

# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Generate coverage report
npm run test:coverage
```

### Python Tests

```bash
cd prompt-service

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_prompts.py
```

### Run All Tests

```bash
# From root directory
npm run test:all
```

---

## Troubleshooting

### Common Issues

#### 1. PostgreSQL Connection Error

**Error:** `ECONNREFUSED` or `database "writing_prompts" does not exist`

**Solution:**
```bash
# Verify PostgreSQL is running
pg_isready

# If not running, start it:
# macOS:
brew services start postgresql

# Linux:
sudo systemctl start postgresql

# Create database if missing
psql -U postgres -c "CREATE DATABASE writing_prompts;"
```

#### 2. Redis Connection Error

**Error:** `Error: Redis connection to localhost:6379 failed`

**Solution:**
```bash
# Start Redis server
redis-server

# Or as a service:
# macOS:
brew services start redis

# Linux:
sudo systemctl start redis
```

#### 3. Port Already in Use

**Error:** `EADDRINUSE: address already in use :::3000`

**Solution:**
```bash
# Find and kill process using the port
# macOS/Linux:
lsof -ti:3000 | xargs kill -9

# Or change the port in .env file
```

#### 4. OpenAI API Key Invalid

**Error:** `401 Unauthorized` from prompt service

**Solution:**
- Verify your OpenAI API key is correct in `prompt-service/.env`
- Check your OpenAI account has available credits
- Ensure the key starts with `sk-`

#### 5. Google OAuth Not Working

**Error:** `Invalid client ID`

**Solution:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create/select your project
3. Enable Google+ API
4. Add `http://localhost:3000` to Authorized JavaScript origins
5. Copy the correct Client ID to both frontend and backend `.env` files

#### 6. Frontend Build Errors

**Error:** `Module not found` or dependency issues

**Solution:**
```bash
cd frontend

# Delete node_modules and package-lock.json
rm -rf node_modules package-lock.json

# Reinstall dependencies
npm install

# Clear React cache
rm -rf node_modules/.cache
```

#### 7. Python Virtual Environment Issues

**Error:** `ModuleNotFoundError: No module named 'flask'`

**Solution:**
```bash
cd prompt-service

# Recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### 8. Sound Design 403 or TypeError Error

**Error:** `TypeError: Cannot read properties of undefined (reading 'id')` or `403 Forbidden`

**Root Cause:** The sound design endpoint was trying to require authentication when the user isn't logged in.

**Solution:** This has been fixed in the latest version. The sound design endpoint now works without authentication (like other creative prompts). If you're still seeing this error:

1. **Pull the latest changes:**
   ```bash
   git pull origin main
   ```

2. **Restart the backend server:**
   ```bash
   cd backend
   npm run dev
   ```

3. **Clear browser cache and localStorage:**
   - Open browser DevTools (F12)
   - Go to Application → Local Storage
   - Clear all data
   - Refresh the page

**Note:** Sound design prompts now work for both logged-in and anonymous users, consistent with other creative features.

#### 9. Docker Container Running Old Code

**Error:** Still seeing errors after pulling latest changes when using Docker

**Root Cause:** Docker containers cache the built code. Pulling new code doesn't automatically update running containers.

**Solution:**
```bash
# Stop all containers
docker-compose down

# Rebuild containers with latest code (no cache)
docker-compose build --no-cache

# Start fresh containers
docker-compose up -d

# View logs to confirm it's working
docker-compose logs -f backend
```

**Quick rebuild for just one service:**
```bash
# Rebuild only the backend service
docker-compose build --no-cache backend
docker-compose up -d backend
```

**Check which code version is running:**
```bash
# See when the container was built
docker inspect writing-prompt-generator-backend | grep Created

# View container logs
docker-compose logs backend | tail -50
```

**Pro Tip:** During active development, use volume mounts in docker-compose.yml to avoid constant rebuilds:
```yaml
services:
  backend:
    volumes:
      - ./backend:/app
      - /app/node_modules  # Exclude node_modules
```

### Checking Logs

#### Backend Logs

```bash
cd backend
npm run dev
# Logs will appear in console
```

#### Frontend Logs

Open browser console (F12) to see React errors and warnings

#### Prompt Service Logs

```bash
cd prompt-service
python app.py
# Logs will appear in console
```

---

## Development Workflow

### Making Changes

1. **Create a new branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Edit code in your preferred editor
   - Follow existing code style

3. **Test your changes**
   ```bash
   # Run tests
   npm test  # in frontend or backend
   pytest    # in prompt-service
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

5. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**
   - Go to GitHub
   - Click "New Pull Request"
   - Describe your changes

### Hot Reloading

All services support hot reloading during development:

- **Frontend**: Changes to React components reload automatically
- **Backend**: `nodemon` restarts server on file changes
- **Prompt Service**: Flask dev server reloads on file changes

### Debugging

#### Frontend Debugging

1. Use React Developer Tools browser extension
2. Add breakpoints in browser DevTools
3. Use `console.log()` statements
4. Check Redux state in Redux DevTools extension

#### Backend Debugging

```bash
# Run with Node.js debugger
node --inspect backend/server.js

# Then open chrome://inspect in Chrome
```

#### Python Debugging

```python
# Add breakpoints in code
import pdb; pdb.set_trace()

# Or use VS Code debugger with launch.json
```

### Code Style

- **JavaScript/React**: Follow [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
- **Python**: Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Run linters before committing:
  ```bash
  # Frontend
  npm run lint

  # Python
  flake8 .
  ```

---

## Additional Resources

- [React Documentation](https://react.dev/)
- [Redux Toolkit Documentation](https://redux-toolkit.js.org/)
- [Express.js Documentation](https://expressjs.com/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)
- [OpenAI API Documentation](https://platform.openai.com/docs)

---

## Getting Help

If you encounter issues not covered in this guide:

1. Check existing [GitHub Issues](https://github.com/Jdouville8/ideasthesia-creative-prompt-generator/issues)
2. Create a new issue with:
   - Detailed description of the problem
   - Steps to reproduce
   - Error messages
   - Your environment (OS, Node version, etc.)

---

## Next Steps

Once you have the application running:

1. Explore the codebase structure (see [README.md](README.md))
2. Read the [TESTING.md](TESTING.md) guide for writing tests
3. Check [TESTING-STATUS.md](TESTING-STATUS.md) for current test coverage
4. Review [QUICK-FIXES.md](QUICK-FIXES.md) for known test issues

Happy coding! 🚀

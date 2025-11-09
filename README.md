# 📚 Writing Prompt Generator

An AI-powered web application that generates creative writing exercises and prompts to help writers improve their craft. Built with React, Node.js, Python, and OpenAI's GPT-3.5-turbo.

![Writing Prompt Generator](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## ✨ Features

- **AI-Generated Writing Exercises**: 10 different types of creative writing exercises powered by OpenAI
  - Idea Generation Drills
  - World-Building Techniques
  - Structural Exercises
  - Description Techniques
  - Dialogue Craft
  - Theme & Subtext
  - Genre Convention Study
  - Reverse Engineering
  - Constraint Creativity
  - Revision Techniques

- **Genre Selection**: Choose from 18 different genres including Fantasy, Science Fiction, Mystery, Horror, and more

- **Difficulty Levels**: Weighted distribution of exercise difficulties
  - Very Easy: 30% (250 words)
  - Easy: 30% (500 words)
  - Medium: 25% (750 words)
  - Hard: 15% (1000 words)

- **Writing Interface**:
  - Auto-expanding textarea
  - Live word and character counter
  - Download your writing as .txt
  - Progress tracking toward word count goals

- **Dark Mode**: Full dark mode support with elegant book-themed background patterns

- **Google OAuth Authentication**: Secure login with Google accounts

## 🏗️ Architecture

### Tech Stack

**Frontend:**
- React 18 with Redux Toolkit
- Tailwind CSS
- Google OAuth 2.0
- OpenTelemetry for observability

**Backend:**
- Node.js with Express
- PostgreSQL database
- Redis for caching
- JWT authentication

**Prompt Generation Service:**
- Python Flask
- OpenAI GPT-3.5-turbo API

**Infrastructure:**
- Docker & Docker Compose
- Prometheus for metrics
- Grafana for monitoring
- Jenkins for CI/CD

## 🚀 Getting Started

### Prerequisites

- Docker and Docker Compose
- Google OAuth credentials
- OpenAI API key

### 1. Fork the Repository

Click the "Fork" button at the top right of this repository to create your own copy.

### 2. Clone Your Fork

```bash
git clone https://github.com/YOUR_USERNAME/writing-prompt-generator.git
cd writing-prompt-generator
```

### 3. Set Up Environment Variables

Create a `.env` file in the root directory:

```env
# Database
POSTGRES_USER=promptuser
POSTGRES_PASSWORD=promptpass
POSTGRES_DB=writingprompts

# Backend
JWT_SECRET=your-super-secret-jwt-key-change-this
NODE_ENV=development

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key

# Redis
REDIS_URL=redis://redis:6379
```

### 4. Get Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
5. Set authorized redirect URIs:
   - `http://localhost:4000/api/auth/google/callback`
   - `http://localhost:3000`
6. Copy your Client ID and Client Secret to `.env`

### 5. Get OpenAI API Key

1. Sign up at [OpenAI](https://platform.openai.com/)
2. Go to [API Keys](https://platform.openai.com/api-keys)
3. Create a new API key
4. Add credits to your account
5. Copy the key to `.env`

### 6. Start the Application

```bash
# Build and start all services
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### 7. Initialize the Database

```bash
# Run the database setup script
bash scripts/setup-db.sh
```

### 8. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:4000
- **Prompt Service**: http://localhost:5001
- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Jenkins**: http://localhost:8080

## 📁 Project Structure

```
writing-prompt-generator/
├── frontend/               # React frontend application
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── store/         # Redux store and slices
│   │   ├── contexts/      # React contexts (Theme)
│   │   └── App.js         # Main application component
│   └── Dockerfile
├── backend/               # Node.js Express backend
│   ├── server.js         # Main server file
│   └── Dockerfile
├── prompt-service/        # Python Flask prompt generation
│   ├── app.py            # Flask application
│   └── Dockerfile
├── scripts/              # Utility scripts
│   └── setup-db.sh      # Database initialization
├── docker-compose.yml    # Docker orchestration
└── README.md
```

## 🔧 Development

### Running Locally Without Docker

**Frontend:**
```bash
cd frontend
npm install
npm start
```

**Backend:**
```bash
cd backend
npm install
node server.js
```

**Prompt Service:**
```bash
cd prompt-service
pip install -r requirements.txt
python app.py
```

### Rebuilding Specific Services

```bash
# Rebuild only the frontend
docker-compose up -d --build frontend

# Rebuild only the backend
docker-compose up -d --build backend

# Rebuild only the prompt service
docker-compose up -d --build prompt-service
```

## 🎨 Customization

### Adding New Exercise Types

Edit `prompt-service/app.py` and add your exercise type to the `exercise_types` array in the `generate_prompt_with_ai()` function.

### Changing Difficulty Distribution

Modify the weights in the `get_random_word_count_and_difficulty()` function in `prompt-service/app.py`.

### Updating Genres

Edit the `genres` array in `frontend/src/App.js`.

## 🐛 Troubleshooting

### Container Issues

```bash
# View logs for a specific service
docker-compose logs frontend
docker-compose logs backend
docker-compose logs prompt-service

# Restart a service
docker-compose restart frontend

# Rebuild from scratch
docker-compose down -v
docker-compose up -d --build
```

### Database Issues

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U promptuser -d writingprompts

# List tables
\dt

# View table contents
SELECT * FROM users;
SELECT * FROM prompts;
```

### OpenAI API Issues

- Ensure you have added credits to your OpenAI account
- Check your API key is correct in `.env`
- Verify the prompt-service logs: `docker-compose logs prompt-service`

## 📊 Monitoring

- **Prometheus**: Collects metrics from all services
- **Grafana**: Visualizes metrics with pre-configured dashboards
- **OpenTelemetry**: Distributed tracing for request flows

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for GPT-3.5-turbo API
- Google for OAuth authentication
- The open-source community for all the amazing tools and libraries

## 📧 Support

If you encounter any issues or have questions, please [open an issue](https://github.com/YOUR_USERNAME/writing-prompt-generator/issues) on GitHub.

---

Built with ❤️ by writers, for writers

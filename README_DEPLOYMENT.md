# 🚀 Catalyst Application Deployment Guide

This guide will help you deploy the Catalyst Manufacturing Problem-Solving Platform with both the FastAPI backend and React frontend.

## 📋 Prerequisites

Before deploying, ensure you have:

- **Python 3.8+** installed
- **Node.js 16+** and npm installed
- **Docker and Docker Compose** (for containerized deployment)
- **Google AI API Key** (get from [Google AI Studio](https://makersuite.google.com/app/apikey))

## 🔧 Quick Start (Local Development)

### 1. Clone and Setup Environment

```bash
# Clone the repository (if not already done)
git clone <your-repo-url>
cd testingsoftware

# Copy environment template
cp env.example .env
```

### 2. Configure Environment Variables

Edit the `.env` file and add your Google API key:

```bash
# Required: Get your API key from https://makersuite.google.com/app/apikey
GOOGLE_API_KEY=your_actual_google_api_key_here

# Optional: Backend configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# Optional: Frontend configuration
REACT_APP_BACKEND_URL=http://localhost:8000
```

### 3. Deploy Backend

```bash
# Make the script executable
chmod +x deploy_backend.sh

# Run the deployment script
./deploy_backend.sh
```

The backend will be available at:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000

### 4. Deploy Frontend (in a new terminal)

```bash
# Make the script executable
chmod +x deploy_frontend.sh

# Run the deployment script
./deploy_frontend.sh
```

The frontend will be available at:
- **Application**: http://localhost:3000

## 🐳 Docker Deployment (Recommended for Production)

### 1. Build and Start with Docker Compose

```bash
# Create .env file with your Google API key
echo "GOOGLE_API_KEY=your_actual_api_key_here" > .env

# Build and start all services
docker-compose up --build

# Run in background (detached mode)
docker-compose up -d --build
```

### 2. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Nginx Proxy**: http://localhost (if using the nginx service)

### 3. Stop the Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## 🌐 Production Deployment Options

### Option 1: Traditional VPS/Server

1. **Setup server** with Python 3.8+, Node.js 16+, and nginx
2. **Clone repository** to your server
3. **Configure environment variables**
4. **Run deployment scripts** or use systemd services
5. **Configure nginx** as reverse proxy

### Option 2: Cloud Platforms

#### Deploy Backend on:
- **Railway**: Connect GitHub repo, set environment variables
- **Render**: Deploy as web service, add Google API key
- **Heroku**: Use Heroku CLI or GitHub integration
- **DigitalOcean App Platform**: Deploy directly from Git

#### Deploy Frontend on:
- **Vercel**: Connect GitHub repo, build automatically
- **Netlify**: Drag & drop build folder or Git integration
- **AWS S3 + CloudFront**: Upload build files to S3

### Option 3: Containerized Deployment

Use the provided Docker files with:
- **AWS ECS** with ECR
- **Google Cloud Run**
- **Azure Container Instances**
- **Kubernetes** cluster

## 🔧 Configuration Options

### Backend Configuration

The backend can be configured via environment variables:

```bash
# Required
GOOGLE_API_KEY=your_api_key

# Optional
BACKEND_HOST=0.0.0.0  # Default: 0.0.0.0
BACKEND_PORT=8000     # Default: 8000
ENVIRONMENT=production # Default: development
```

### Frontend Configuration

The frontend can be configured via environment variables:

```bash
# Backend URL (change for production)
REACT_APP_BACKEND_URL=http://localhost:8000

# For production, use your actual backend URL:
# REACT_APP_BACKEND_URL=https://your-backend.com
```

## 🛠️ Manual Deployment Steps

### Backend (Manual)

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "GOOGLE_API_KEY=your_api_key_here" > .env

# Start server
python main.py
```

### Frontend (Manual)

```bash
cd frontend/frontend

# Install dependencies
npm install

# For development
npm start

# For production build
npm run build
# Then serve the build folder with a web server
```

## 📊 Monitoring and Logs

### Check Application Health

```bash
# Backend health check
curl http://localhost:8000/

# Check backend logs (Docker)
docker-compose logs backend

# Check frontend logs (Docker)
docker-compose logs frontend
```

### Common Issues

1. **Backend not starting**: Check Google API key in `.env` file
2. **Frontend can't connect**: Verify `REACT_APP_BACKEND_URL` points to correct backend
3. **CORS errors**: Backend already has CORS configured for frontend
4. **Port conflicts**: Change ports in docker-compose.yml if needed

## 🔐 Security Considerations

1. **Never commit** your `.env` file with real API keys
2. **Use HTTPS** in production
3. **Set proper CORS origins** in production (not `*`)
4. **Use environment-specific** configurations
5. **Keep dependencies updated**

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://reactjs.org/)
- [Docker Documentation](https://docs.docker.com/)
- [Google AI Studio](https://makersuite.google.com/)

## 🆘 Support

If you encounter issues:

1. Check the logs for error messages
2. Verify environment variables are set correctly
3. Ensure all dependencies are installed
4. Check network connectivity between frontend and backend

---

**Happy Deploying! 🎉** 
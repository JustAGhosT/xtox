# Deployment Guide

## Prerequisites

- Python 3.9+
- Node.js 14+
- MongoDB instance
- Azure subscription (for cloud deployment)
- FFmpeg installed (for audio conversion)
- pdflatex installed (for LaTeX conversion)

## Local Development Setup

### 1. Backend Setup

```bash
# Navigate to backend directory
cd xtox/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp ../.env.example .env
# Edit .env with your configuration

# Start MongoDB (if running locally)
mongod

# Run backend server
python server.py
```

Backend will be available at `http://localhost:8000`

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd xtox/frontend

# Install dependencies
yarn install

# Set environment variable
export REACT_APP_BACKEND_URL=http://localhost:8000
# On Windows: set REACT_APP_BACKEND_URL=http://localhost:8000

# Start development server
yarn start
```

Frontend will be available at `http://localhost:3000`

## Production Deployment

### Azure Functions Deployment

1. **Prerequisites:**
   - Azure CLI installed
   - Azure Functions Core Tools installed
   - Azure subscription

2. **Deploy Infrastructure:**
   ```powershell
   cd infra
   .\deploy-infrastructure.ps1 -resourceGroupName "xtox-rg" -location "eastus"
   ```

3. **Configure Environment Variables:**
   - Set in Azure Portal or via Azure CLI
   - Required variables:
     - `MONGO_URL`
     - `JWT_SECRET_KEY`
     - `AZURE_STORAGE_ACCOUNT_NAME`
     - `AZURE_STORAGE_ACCOUNT_KEY`

4. **Deploy Functions:**
   ```bash
   cd xtox/azure-functions
   func azure functionapp publish <function-app-name>
   ```

### Docker Deployment

1. **Build Backend Image:**
   ```bash
   docker build -t xtox-backend -f Dockerfile.backend .
   ```

2. **Run Container:**
   ```bash
   docker run -d \
     -p 8000:8000 \
     -e MONGO_URL=mongodb://mongo:27017 \
     -e JWT_SECRET_KEY=your-secret \
     --name xtox-backend \
     xtox-backend
   ```

### Environment Variables

See `.env.example` for all required environment variables.

**Critical Production Variables:**
- `JWT_SECRET_KEY`: Minimum 32 characters, use Azure Key Vault in production
- `ENVIRONMENT`: Set to `production`
- `ALLOW_MOCK_AUTH`: Set to `false`
- `ALLOWED_ORIGINS`: Comma-separated list of allowed frontend URLs
- `MONGO_URL`: MongoDB connection string
- `RATE_LIMIT_ENABLED`: Set to `true`

## System Dependencies

### FFmpeg Installation

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
Download from https://ffmpeg.org/download.html and add to PATH

### LaTeX Installation

**Ubuntu/Debian:**
```bash
sudo apt-get install texlive-latex-base texlive-latex-extra
```

**macOS:**
```bash
brew install --cask mactex
```

**Windows:**
Download MiKTeX from https://miktex.org/download

## Troubleshooting

### MongoDB Connection Issues

- Verify MongoDB is running: `mongosh --eval "db.adminCommand('ping')"`
- Check connection string format
- Verify network connectivity and firewall rules

### File Conversion Failures

- Verify FFmpeg/pdflatex are installed and in PATH
- Check file permissions on temp directories
- Review logs for specific error messages

### CORS Errors

- Verify `ALLOWED_ORIGINS` includes your frontend URL
- Check browser console for specific CORS error
- Ensure credentials are properly configured

## Monitoring

- Application logs: Check Azure Application Insights or log files
- Database monitoring: MongoDB Atlas or local monitoring tools
- Performance: Monitor conversion times and error rates

## Security Checklist

- [ ] JWT_SECRET_KEY is strong and stored securely
- [ ] ALLOW_MOCK_AUTH is set to false
- [ ] ALLOWED_ORIGINS is restricted to production domains
- [ ] MongoDB is secured with authentication
- [ ] HTTPS is enabled for all endpoints
- [ ] Rate limiting is enabled
- [ ] File upload size limits are configured
- [ ] Error messages don't expose internal details


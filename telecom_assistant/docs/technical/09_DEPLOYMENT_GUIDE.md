# Deployment Guide - Setup & Running Instructions

## Overview

This guide provides comprehensive instructions for setting up, configuring, and deploying the Telecom Service Assistant application.

---

## Prerequisites

### System Requirements

**Operating System**:
- Windows 10/11
- macOS 10.15+
- Linux (Ubuntu 20.04+)

**Software**:
- **Python**: 3.9 or higher (tested on 3.13.3)
- **pip**: Latest version
- **Git**: For cloning repository
- **Virtual environment**: venv or conda

**Hardware**:
- **RAM**: Minimum 4 GB (8 GB recommended)
- **Storage**: 2 GB free space
- **CPU**: Modern multi-core processor

**API Access**:
- **OpenAI API Key**: Required for GPT-4o-mini
  - Sign up at: https://platform.openai.com/
  - Minimum $5 credit recommended

---

## Installation

### Step 1: Clone Repository

```bash
# Clone the repository
git clone <repository-url>
cd telecom_assistant

# Or if already downloaded
cd d:\AI-Training\Hackathon_Final\telecom_assistant
```

### Step 2: Create Virtual Environment

**Using venv (recommended)**:
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

**Using conda**:
```bash
conda create -n telecom python=3.13
conda activate telecom
```

**Verify**:
```bash
python --version  # Should show Python 3.9+
```

### Step 3: Install Dependencies

```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

**Expected Output**:
```
Installing collected packages:
  - openai==1.58.1
  - streamlit==1.41.1
  - langchain==0.3.13
  - langchain-openai==0.2.14
  - llama-index==0.12.9
  - crewai==0.86.0
  - pyautogen==0.2.38
  - langgraph==0.2.59
  ...
Successfully installed <package-list>
```

**Troubleshooting**:

- **Error: No module named 'pip'**
  ```bash
  python -m ensurepip --upgrade
  ```

- **Error: Microsoft Visual C++ required** (Windows)
  - Download: https://visualstudio.microsoft.com/downloads/
  - Install "Desktop development with C++" workload

- **SSL Certificate errors**
  ```bash
  pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
  ```

### Step 4: Verify Installation

```bash
# Test imports
python -c "import openai, streamlit, langchain, llama_index, crewai, autogen, langgraph; print('All imports successful!')"
```

**Expected Output**: `All imports successful!`

---

## Configuration

### Step 1: Create Environment File

Create `.env` file in project root:

```bash
# Windows
New-Item -Path .env -ItemType File

# macOS/Linux
touch .env
```

### Step 2: Add OpenAI API Key

Open `.env` in text editor and add:

```env
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Important**:
- Replace `sk-proj-...` with your actual API key
- Keep this file secure (never commit to Git)
- `.env` is in `.gitignore` by default

**Getting API Key**:
1. Go to https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Copy key (only shown once!)
4. Paste into `.env` file

### Step 3: Verify Configuration

```bash
# Test API key
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('API Key:', os.getenv('OPENAI_API_KEY')[:10] + '...' if os.getenv('OPENAI_API_KEY') else 'Not found')"
```

**Expected Output**: `API Key: sk-proj-...`

---

## Database Setup

### Verify Database Exists

```bash
# Check if database file exists
# Windows
Test-Path data\telecom.db

# macOS/Linux
ls -l data/telecom.db
```

**Expected Output**: `True` or file listing

### Initialize Database (if needed)

If database doesn't exist, create it:

```bash
# Run initialization script
python utils/init_db.py
```

### Verify Database Tables

```bash
# Check tables
python -c "import sqlite3; conn = sqlite3.connect('data/telecom.db'); cursor = conn.cursor(); cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\"'); print([row[0] for row in cursor.fetchall()])"
```

**Expected Output**: List of 13 tables

---

## Running the Application

### Method 1: Using Streamlit Directly

```bash
# Run Streamlit app
streamlit run ui/streamlit_app.py
```

**Expected Output**:
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.1.x:8501
```

### Method 2: Using Entry Point

```bash
# Run via app.py
python app.py
```

**app.py content**:
```python
import os
import sys

if __name__ == "__main__":
    os.system("streamlit run ui/streamlit_app.py")
```

### Method 3: Custom Port

```bash
# Run on custom port
streamlit run ui/streamlit_app.py --server.port 8080
```

### Method 4: Production Mode

```bash
# Run without file watcher (production)
streamlit run ui/streamlit_app.py --server.fileWatcherType none
```

---

## Using the Application

### Customer Login

1. Open browser to http://localhost:8501
2. In sidebar, enter email (e.g., `john.doe@email.com`)
3. Select "customer" as user type
4. Click "Login"
5. Access customer dashboard with 4 tabs

**Test Customer Emails**:
- `john.doe@email.com` (CUST001)
- `jane.smith@email.com` (CUST002)
- `bob.johnson@email.com` (CUST003)

### Admin Login

1. Enter any email
2. Select "admin" as user type
3. Click "Login"
4. Access admin dashboard with 3 tabs

### Sample Queries

**Billing Queries**:
- "Why is my bill higher this month?"
- "Show me my recent bills"
- "Am I on the right plan?"

**Network Queries**:
- "My internet is slow"
- "WiFi keeps disconnecting"
- "No signal on my device"

**Service Queries**:
- "What plan should I get?"
- "Recommend a plan for heavy streaming"
- "Compare Premium 50GB and 100GB plans"

**Knowledge Queries**:
- "How to configure 5G on my phone?"
- "What are the steps to troubleshoot slow internet?"
- "Explain billing cycles"

---

## Testing

### Manual Testing

**Test all frameworks**:
```bash
# Test CrewAI (billing)
python -c "from agents.billing_agents import process_billing_query; print(process_billing_query('CUST001', 'Why is my bill higher?'))"

# Test AutoGen (network)
python -c "from agents.network_agents import process_network_query; print(process_network_query('My internet is slow'))"

# Test LangChain (service)
python -c "from agents.service_agents import process_recommendation_query; print(process_recommendation_query('Recommend a plan'))"

# Test LlamaIndex (knowledge)
python -c "from agents.knowledge_agents import process_knowledge_query; print(process_knowledge_query('How to configure 5G?'))"
```

### Running Test Files

```bash
# Run existing tests
python tests/test_all_queries.py
python tests/test_database_queries.py
python tests/test_edge_cases.py
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'openai'"

**Solution**:
```bash
# Ensure virtual environment is activated
# Windows
.venv\Scripts\activate

# Then reinstall
pip install -r requirements.txt
```

### Issue: "openai.AuthenticationError: Invalid API key"

**Solution**:
```bash
# Check .env file exists
cat .env  # macOS/Linux
type .env  # Windows

# Verify API key is correct
# Re-generate key at https://platform.openai.com/api-keys
```

### Issue: "OperationalError: unable to open database file"

**Solution**:
```bash
# Check database path
ls data/telecom.db

# If missing, initialize database
python utils/init_db.py
```

### Issue: "Address already in use" (Port 8501)

**Solution**:
```bash
# Use different port
streamlit run ui/streamlit_app.py --server.port 8502

# Or kill existing process
# Windows
netstat -ano | findstr :8501
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :8501
kill -9 <PID>
```

### Issue: Slow responses or timeouts

**Causes**:
- Large query processing
- API rate limits
- Network latency

**Solutions**:
```bash
# 1. Check API usage
# Visit: https://platform.openai.com/usage

# 2. Increase timeout in code
# Edit agents files, increase timeout parameter

# 3. Use caching
# Already implemented in agents
```

### Issue: ChromaDB errors

**Solution**:
```bash
# Clear vector database
rm -rf data/chromadb/*  # macOS/Linux
Remove-Item -Recurse -Force data\chromadb\*  # Windows

# Re-index documents
python -c "from agents.knowledge_agents import create_knowledge_engine; create_knowledge_engine()"
```

---

## Production Deployment

### Option 1: Streamlit Cloud (Recommended for Demo)

**Steps**:
1. Push code to GitHub
2. Go to https://share.streamlit.io/
3. Connect GitHub repository
4. Set environment variables (OPENAI_API_KEY)
5. Deploy

**Environment Variables**:
- Add `OPENAI_API_KEY` in Streamlit Cloud settings
- Not in `.env` file

### Option 2: Docker Container

**Dockerfile**:
```dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "ui/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

**Build and Run**:
```bash
# Build image
docker build -t telecom-assistant .

# Run container
docker run -p 8501:8501 -e OPENAI_API_KEY=sk-... telecom-assistant
```

### Option 3: Traditional Server (VPS/EC2)

**Setup**:
```bash
# 1. Install Python
sudo apt update
sudo apt install python3.13 python3-pip python3-venv

# 2. Clone repository
git clone <repo-url>
cd telecom_assistant

# 3. Install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 4. Set environment variables
export OPENAI_API_KEY=sk-...

# 5. Run with screen/tmux
screen -S telecom
streamlit run ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0
# Detach: Ctrl+A, D
```

**Nginx Reverse Proxy** (optional):
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

### Option 4: Serverless (AWS Lambda + API Gateway)

**Not recommended** - Streamlit not designed for serverless
**Alternative**: Use FastAPI for API-only deployment

---

## Monitoring & Maintenance

### Log Files

**Streamlit Logs**:
```bash
# View logs
streamlit run ui/streamlit_app.py --logger.level=debug
```

**Application Logs**:
```python
# Add logging in code
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

### Performance Monitoring

**Check Response Times**:
```python
import time

start = time.time()
response = process_query(query)
end = time.time()
print(f"Query took {end - start:.2f} seconds")
```

**Monitor API Usage**:
- Visit: https://platform.openai.com/usage
- Set up billing alerts

### Database Backups

```bash
# Backup database
# Windows
Copy-Item data\telecom.db data\telecom.db.backup

# macOS/Linux
cp data/telecom.db data/telecom.db.backup

# Automated daily backup (cron)
0 2 * * * cp /path/to/data/telecom.db /path/to/backups/telecom_$(date +\%Y\%m\%d).db
```

---

## Security Best Practices

### 1. API Key Security

- **Never** commit `.env` to Git
- Use environment variables in production
- Rotate keys regularly
- Set up usage limits

### 2. Database Security

- Use read-only connections where possible
- Sanitize user inputs
- Implement proper authentication (not just email)

### 3. Network Security

- Use HTTPS in production
- Implement rate limiting
- Add CORS headers if needed

### 4. Access Control

- Implement proper role-based access
- Add password authentication
- Use OAuth/SSO for enterprise

---

## Performance Optimization

### 1. Caching

Already implemented:
- LangGraph workflow cached in session
- Knowledge engine cached globally
- Database connections pooled

### 2. Async Processing

**Future enhancement**:
```python
import asyncio

async def process_query_async(query):
    # Process multiple frameworks in parallel
    results = await asyncio.gather(
        process_billing_query_async(query),
        process_network_query_async(query),
        # ...
    )
    return results
```

### 3. Database Indexing

```sql
-- Add indexes for frequently queried columns
CREATE INDEX idx_customer_email ON customers(email);
CREATE INDEX idx_bills_customer ON bills(customer_id);
CREATE INDEX idx_usage_customer ON usage_history(customer_id);
```

---

## Scaling Considerations

### Horizontal Scaling

- Deploy multiple Streamlit instances
- Use load balancer (Nginx/HAProxy)
- Share session state via Redis

### Vertical Scaling

- Increase server resources
- Use faster database (PostgreSQL)
- Optimize LLM calls

### Cost Optimization

- Use cheaper models for classification (gpt-4o-mini ✓)
- Implement aggressive caching
- Batch API requests where possible

---

## Appendix

### A. Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| OPENAI_API_KEY | Yes | None | OpenAI API key |
| DATABASE_PATH | No | data/telecom.db | Database location |
| LOG_LEVEL | No | INFO | Logging level |
| STREAMLIT_PORT | No | 8501 | Web server port |

### B. Dependencies

See `requirements.txt` for full list:
- openai==1.58.1
- streamlit==1.41.1
- langchain==0.3.13
- llama-index==0.12.9
- crewai==0.86.0
- pyautogen==0.2.38
- langgraph==0.2.59

### C. File Structure

```
telecom_assistant/
├── agents/                  # AI framework implementations
├── data/                    # Database and documents
├── docs/                    # Documentation
├── orchestration/           # LangGraph workflow
├── tests/                   # Test files
├── ui/                      # Streamlit application
├── utils/                   # Utility functions
├── .env                     # Environment variables (create this)
├── .gitignore              # Git ignore rules
├── app.py                  # Entry point
├── README.md               # Project overview
└── requirements.txt        # Python dependencies
```

### D. Support & Resources

**Documentation**:
- LangGraph: https://langchain-ai.github.io/langgraph/
- CrewAI: https://docs.crewai.com/
- AutoGen: https://microsoft.github.io/autogen/
- LangChain: https://python.langchain.com/
- LlamaIndex: https://docs.llamaindex.ai/
- Streamlit: https://docs.streamlit.io/

**Community**:
- GitHub Issues: <repository-url>/issues
- Stack Overflow: Tag [telecom-assistant]

---

**Last Updated**: December 1, 2025
**Version**: 1.0
**Python Version**: 3.13.3
**Status**: Production Ready

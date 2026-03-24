# GitHub AI Project Manager 🤖

A **single-file, deployable** full-stack application that connects to any public GitHub repository and provides AI-powered project management insights using Claude.

**One command to run. Zero build step. Zero npm install.**

---

## ✨ Features

| Feature | Description |
|---|---|
| **Repo Loader** | Paste any public GitHub `owner/repo` or full URL |
| **Issue Browser** | Filter, search, and view all issues with stale/unassigned badges |
| **AI Issue Summary** | Claude reads issue + all comments → structured Status/Blockers/Next Actions |
| **AI Bulk Triage** | Prioritises all open issues, flags risks, gives a health score 1–10 |
| **Migration Tracker** | Auto-detects migration issues, produces leadership dashboard |
| **Structured Templates** | Converts free-form engineer updates into structured format |
| **Executive Report** | Weekly programme health report with RAG status for leadership |
| **Labels & Workload** | Visual charts of label frequency and assignee load |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip

### 1. Install dependencies
```bash
pip install flask requests
```

### 2. Configure environment
```bash
cp .env .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 3. Run
```bash
python app.py
```

### 4. Open
```
http://localhost:8000
```

That's it. The app serves both the React frontend and the Python API from the same process.

---

## 🔑 API Keys

### Anthropic API Key (Required for AI features)
1. Go to https://console.anthropic.com/
2. Create an account and generate an API key
3. Add to `.env`: `ANTHROPIC_API_KEY=sk-ant-...`

> Without this key, the app still works for GitHub browsing — it just shows a message instead of AI output.

### GitHub Token (Recommended)
Without a token: **60 API requests/hour** (fine for demos)  
With a token: **5,000 requests/hour**

1. Go to https://github.com/settings/tokens
2. Generate a classic token with `public_repo` scope
3. Add to `.env`: `GITHUB_TOKEN=ghp_...`

---

## 📁 Project Structure

```
github-ai-pm/
├── app.py          ← Everything: Flask API + React frontend (HTML served inline)
├── .env.example    ← Copy to .env and fill in your keys
├── .env            ← Your local secrets (never commit this)
└── README.md
```

---

## 🌐 Deployment

### Deploy to Railway (Recommended - Free tier)
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up

# Set environment variables in Railway dashboard
```

### Deploy to Render
1. Push to GitHub
2. New Web Service → connect repo
3. Build command: `pip install flask requests`
4. Start command: `python app.py`
5. Add env vars in Render dashboard

### Deploy to Fly.io
```bash
# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY app.py .
RUN pip install flask requests
ENV PORT=8080
CMD ["python", "app.py"]
EOF

fly launch
fly secrets set ANTHROPIC_API_KEY=your_key_here
fly secrets set GITHUB_TOKEN=your_token_here
fly deploy
```

### Deploy to Heroku
```bash
# Create Procfile
echo "web: python app.py" > Procfile

# Create requirements.txt
echo -e "flask\nrequests" > requirements.txt

heroku create your-app-name
heroku config:set ANTHROPIC_API_KEY=your_key_here
git push heroku main
```

### Docker
```bash
docker build -t github-ai-pm .
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY=your_key \
  -e GITHUB_TOKEN=your_token \
  github-ai-pm
```

---

## 🎯 Demo Repos to Try

These are large public repos with lots of issues — great for demos:

- `facebook/react` — React framework
- `microsoft/vscode` — VS Code editor
- `vercel/next.js` — Next.js framework
- `kubernetes/kubernetes` — Kubernetes
- `your-org/your-repo` — Your own repos!

---

## 🏗️ Architecture

```
Browser (React via CDN)
    │
    │  HTTP
    ▼
Flask App (app.py, port 8000)
    ├── GET  /              → Serves React HTML
    ├── POST /api/repo/info → GitHub Issues API
    ├── POST /api/issues/summarize  → Claude AI
    ├── POST /api/issues/triage     → Claude AI
    ├── POST /api/issues/migration  → Claude AI
    ├── POST /api/issues/template   → Claude AI
    └── POST /api/report/executive  → Claude AI
```

React is loaded via CDN (no npm/build needed). Babel Standalone transpiles JSX in the browser.

---

## 📋 AI Capabilities Explained

### Issue Summary
Claude reads the full issue description + up to 15 comments and produces:
- Status Snapshot
- What & Why (problem context)
- Blockers & Risks
- Next Actions
- ETA Assessment
- Suggested Labels

### Bulk Triage
Claude analyses all open issues and produces:
- Critical issues requiring immediate attention
- High priority items for this sprint
- Pattern analysis (recurring themes)
- Risk flags (stale, unassigned, poorly scoped)
- Workload balance check
- Process recommendations
- Programme Health Score (1-10)

### Migration Dashboard
Auto-detects migration-related issues (by keywords in title/labels) and produces:
- Migration overview
- Completed vs in-progress vs blocked items
- Health metrics (% complete, blocked count, avg age)
- BAU vs migration effort split
- Forecast and top unblocking actions

### Executive Report
Weekly programme health briefing with:
- RAG status (Green/Amber/Red)
- Key metrics
- Top risks for leadership
- Wins this week
- Recommended leadership actions
- Next week outlook

---

## 🔒 Security Notes

- Never commit your `.env` file
- The app only reads public repos (no write access needed)
- GitHub token should be read-only (`public_repo` scope)
- API keys are only used server-side, never exposed to the browser

---

## 📄 License

MIT — free to use, modify, and deploy.

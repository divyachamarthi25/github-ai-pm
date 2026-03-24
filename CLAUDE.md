# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Application

```bash
# Install dependencies
pip install flask requests python-dotenv

# Configure environment (copy and edit .env)
cp .env .env

# Run
python app.py
```

No build step is needed. The app runs on port 8000 (configurable via `PORT` env var).

## Environment Variables

- `ANTHROPIC_API_KEY` — Required for all AI features
- `GITHUB_TOKEN` — Optional; raises GitHub API rate limit from 60 to 5000 req/hr
- `PORT` — Server port (default: 8000)

## Architecture

This is an intentionally **single-file application** (`app.py`, ~1000 lines). All Flask backend code and the React frontend (embedded as an HTML string) live in this one file.

**Request flow:**
```
Browser (React 18 via CDN + Babel Standalone)
  ↓ JSON over HTTP
Flask (app.py, port 8000)
  ├── GET  /                     → serves the React SPA (HTML string in app.py)
  ├── POST /api/health            → checks API key status
  ├── POST /api/repo/info         → fetches GitHub repo data + issues
  ├── POST /api/issues/summarize  → Claude: single issue analysis
  ├── POST /api/issues/triage     → Claude: bulk triage + health score (1–10)
  ├── POST /api/issues/migration  → Claude: migration vs BAU dashboard
  ├── POST /api/issues/template   → Claude: free-form → structured template
  └── POST /api/report/executive  → Claude: weekly executive health report
  ↓
GitHub API v2022-11-28 (public repos)
Anthropic API (model: claude-sonnet-4-6, max_tokens: 2000–2500)
```

**Key design decisions:**
- React is loaded from CDN; JSX is transpiled in the browser by Babel Standalone — no npm, no build tooling
- All API keys are used server-side only and never sent to the browser
- The frontend uses only React hooks (`useState`, `useCallback`, `useRef`, `useEffect`, `useMemo`) with no external state management
- Markdown rendering is a custom pure-JS implementation embedded in the frontend (no markdown library)

## Frontend Structure (inside app.py)

React components are defined inline in the HTML template string:

| Component | Purpose |
|-----------|---------|
| `App` | Root; handles repo loading, tabs, issue filtering |
| `IssueRow` | Single issue with stale/unassigned badges and AI action buttons |
| `Panel` | Right-side drawer for AI-generated summaries and reports |
| `MdView` | Custom markdown renderer |
| `TmplEditor` | Free-form text → structured template editor |

The UI uses CSS custom properties for theming (no CSS framework).

## Issue Enrichment Logic

Issues are augmented client-side with:
- Days open / days since last update
- Stale flag: no update in >3 days
- Migration detection via keywords: `migrat`, `cloud`, `legacy`, `infra`, `k8s`, `kubernetes`, `aws`, `gcp`, `azure`, `terraform`, `docker`, `refactor`, `port`, `containeris`, `moderniz`

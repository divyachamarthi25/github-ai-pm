#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║     PM Assist  —  v1.0                      ║
║     Single-file deployable: Flask API + React Frontend       ║
║     Run: python app.py                                       ║
║     Open: http://localhost:8000                              ║
╚══════════════════════════════════════════════════════════════╝

Requirements: pip install flask requests python-dotenv
Environment:  ANTHROPIC_API_KEY and optionally GITHUB_TOKEN
"""

import os, json, re, urllib.request, urllib.error
from datetime import datetime, timezone
from flask import Flask, request, jsonify, Response

# ── Load .env if present ──────────────────────────────────────────────────────
def load_dotenv():
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_file):
        with open(env_file, encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_dotenv()

app = Flask(__name__)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GITHUB_TOKEN       = os.environ.get("GITHUB_TOKEN", "")

# ── CORS ──────────────────────────────────────────────────────────────────────
@app.after_request
def cors(r):
    r.headers["Access-Control-Allow-Origin"]  = "*"
    r.headers["Access-Control-Allow-Headers"] = "Content-Type"
    r.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return r

@app.route("/", defaults={"p": ""}, methods=["OPTIONS"])
@app.route("/<path:p>", methods=["OPTIONS"])
def preflight(p): return jsonify({}), 200

# ── GitHub helper ─────────────────────────────────────────────────────────────
def gh(url):
    hdrs = {"Accept":"application/vnd.github+json","User-Agent":"GH-AI-PM/1.0","X-GitHub-Api-Version":"2022-11-28"}
    if GITHUB_TOKEN:
        hdrs["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=hdrs), timeout=15) as r:
        return json.loads(r.read())

# ── Claude helper ─────────────────────────────────────────────────────────────
def claude(system, user, max_tokens=2000):
    if not ANTHROPIC_API_KEY:
        return "⚠️ **AI features disabled** — add `ANTHROPIC_API_KEY` to your `.env` file.\n\nSee `.env` for instructions."
    payload = json.dumps({"model":"claude-sonnet-4-6","max_tokens":max_tokens,
                          "system":system,"messages":[{"role":"user","content":user}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=payload,
        headers={"Content-Type":"application/json","x-api-key":ANTHROPIC_API_KEY,
                 "anthropic-version":"2023-06-01"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return json.loads(r.read())["content"][0]["text"]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        try:
            msg = json.loads(body).get("error", {}).get("message", body)
        except Exception:
            msg = body
        raise Exception(f"Anthropic API error {e.code}: {msg}")

# ── Parsing ───────────────────────────────────────────────────────────────────
def parse_repo(s):
    s = s.strip()
    if "github.com" in s:
        m = re.search(r"github\.com[/:]([^/]+)/([^/\s#?]+)", s)
        if m: return m.group(1), m.group(2).rstrip(".git")
    parts = s.split("/")
    if len(parts) >= 2: return parts[-2], parts[-1].rstrip(".git")
    raise ValueError("Use 'owner/repo' or a GitHub URL")

def enrich(i):
    now = datetime.now(timezone.utc)
    cr  = datetime.fromisoformat(i["created_at"].replace("Z","+00:00"))
    up  = datetime.fromisoformat(i["updated_at"].replace("Z","+00:00"))
    return {
        "number": i["number"], "title": i["title"], "state": i["state"],
        "body": (i.get("body") or "")[:600],
        "labels":    [l["name"] for l in i.get("labels",[])],
        "assignees": [a["login"] for a in i.get("assignees",[])],
        "author": i["user"]["login"],
        "created_at": i["created_at"], "updated_at": i["updated_at"],
        "days_open":         (now-cr).days,
        "days_since_update": (now-up).days,
        "comments_count": i.get("comments",0),
        "url": i["html_url"],
        "is_stale": (now-up).days > 3,
        "milestone": (i.get("milestone") or {}).get("title"),
    }

# ═══════════════════════════════════════════════════════════════
# API ROUTES
# ═══════════════════════════════════════════════════════════════

@app.route("/api/health")
def health():
    return jsonify({"status":"ok","claude":bool(ANTHROPIC_API_KEY),"github_token":bool(GITHUB_TOKEN)})

@app.route("/api/repo/info", methods=["POST"])
def repo_info():
    try:
        owner, repo = parse_repo((request.json or {}).get("repo",""))
        info = gh(f"https://api.github.com/repos/{owner}/{repo}")
        open_raw   = [x for x in gh(f"https://api.github.com/repos/{owner}/{repo}/issues?state=open&per_page=100&sort=updated")   if "pull_request" not in x]
        closed_raw = [x for x in gh(f"https://api.github.com/repos/{owner}/{repo}/issues?state=closed&per_page=30&sort=updated") if "pull_request" not in x]
        open_issues   = [enrich(i) for i in open_raw]
        closed_issues = [enrich(i) for i in closed_raw]
        lf, aw = {}, {}
        for i in open_issues:
            for l in i["labels"]:   lf[l] = lf.get(l,0)+1
            for a in i["assignees"]: aw[a] = aw.get(a,0)+1
        return jsonify({
            "owner": owner, "repo": repo,
            "full_name": info.get("full_name"), "description": info.get("description"),
            "stars": info.get("stargazers_count",0), "forks": info.get("forks_count",0),
            "language": info.get("language"), "topics": info.get("topics",[]),
            "open_issues_count":   len(open_issues),
            "closed_issues_count": len(closed_issues),
            "stale_count":      sum(1 for i in open_issues if i["is_stale"]),
            "unassigned_count": sum(1 for i in open_issues if not i["assignees"]),
            "open_issues":   open_issues[:40],
            "closed_issues": closed_issues[:10],
            "label_frequency":  dict(sorted(lf.items(), key=lambda x:-x[1])[:12]),
            "assignee_workload": aw,
        })
    except ValueError as e: return jsonify({"error":str(e)}), 400
    except urllib.error.HTTPError as e:
        msg = "Repository not found or is private." if e.code==404 else f"GitHub error {e.code}"
        return jsonify({"error":msg}), e.code
    except Exception as e: return jsonify({"error":str(e)}), 500

@app.route("/api/issues/summarize", methods=["POST"])
def summarize():
    d = request.json or {}
    try:
        owner,repo,num = d["owner"],d["repo"],d["issue_number"]
        iss  = enrich(gh(f"https://api.github.com/repos/{owner}/{repo}/issues/{num}"))
        try:
            comments = gh(f"https://api.github.com/repos/{owner}/{repo}/issues/{num}/comments?per_page=15")
        except: comments = []
        ctxt = "\n".join(f"@{c['user']['login']}: {(c.get('body') or '')[:300]}" for c in comments[:10])
        summary = claude(
            "You are a senior engineering PM. Provide structured, actionable GitHub issue analysis for leadership and dev teams.",
            f"""Analyze issue #{num}: {iss['title']}
State: {iss['state']} | Author: @{iss['author']} | Assignees: {', '.join(iss['assignees']) or 'None'}
Labels: {', '.join(iss['labels']) or 'None'} | Days open: {iss['days_open']} | Days since update: {iss['days_since_update']}
Milestone: {iss['milestone'] or 'None'} | Comments: {iss['comments_count']}

Description:
{iss['body']}

Recent comments:
{ctxt or 'None'}

Respond with EXACTLY these sections:
## 📋 Status Snapshot
## 🎯 What & Why
## 🚧 Blockers & Risks
## ✅ Next Actions
## ⏱️ ETA Assessment
## 🏷️ Suggested Labels""")
        return jsonify({"issue":iss,"summary":summary,"comments":len(comments)})
    except Exception as e: return jsonify({"error":str(e)}), 500

@app.route("/api/issues/triage", methods=["POST"])
def triage():
    d = request.json or {}
    issues = d.get("issues",[])
    if not issues: return jsonify({"error":"No issues"}), 400
    listing = "\n".join(
        f"#{i['number']} [{i['state'].upper()}] {i['title']}\n"
        f"  Labels:{','.join(i['labels']) or 'none'} Assignees:{','.join(i['assignees']) or 'UNASSIGNED'} "
        f"DaysOpen:{i['days_open']} DaysSinceUpdate:{i['days_since_update']} Comments:{i['comments_count']}"
        for i in issues[:30])
    try:
        report = claude(
            "You are a senior engineering programme manager. Triage GitHub issues intelligently with risk flags and prioritisation.",
            f"""Triage {len(issues)} issues for {d.get('owner')}/{d.get('repo')}:

{listing}

Write a structured triage report:
## 🚨 Critical — Immediate Attention Required
## 🔥 High Priority This Sprint (Top 5)
## 📊 Pattern Analysis
## ⚠️ Risk Flags
## 👥 Workload & Ownership Issues
## 💡 Process Improvement Recommendations
## 📈 Programme Health Score (1–10 with justification)""", max_tokens=2500)
        return jsonify({"triage":report,"count":len(issues)})
    except Exception as e: return jsonify({"error":str(e)}), 500

@app.route("/api/issues/migration", methods=["POST"])
def migration():
    d = request.json or {}
    issues = d.get("issues",[])
    kws = ["migrat","cloud","legacy","infra","k8s","kubernetes","aws","gcp","azure",
           "terraform","docker","refactor","port","move","containeris","moderniz"]
    mig = [i for i in issues if any(k in (i["title"]+" "+" ".join(i["labels"])).lower() for k in kws)]
    listing = ""
    for i in issues[:35]:
        tag = "🔁 MIG" if i in mig else "📋 BAU"
        listing += f"{tag} #{i['number']} [{i['state'].upper()}]: {i['title']}\n"
        listing += f"     Labels:{','.join(i['labels']) or 'none'} | {i['days_open']}d open | {i['days_since_update']}d since update\n"
    try:
        report = claude(
            "You are a cloud migration programme manager. Produce clear, data-driven migration dashboards for engineering leadership.",
            f"""Analyse {len(issues)} issues from {d.get('owner')}/{d.get('repo')}.
{len(mig)} appear migration-related.

{listing}

Produce:
## 🗺️ Migration Programme Overview
## ✅ Completed / Closed Migration Items
## 🔄 In Progress
## 🚧 Blocked / At Risk
## 📊 Migration Health Metrics
  - Estimated % complete:
  - Items blocked:
  - Items unassigned:
  - Avg age of open migration items:
## 📋 BAU vs Migration Effort Split
## 🔮 Forecast & Top 3 Unblocking Actions""", max_tokens=2500)
        return jsonify({"report":report,"migration_count":len(mig),"total":len(issues),"migration_issues":mig[:15]})
    except Exception as e: return jsonify({"error":str(e)}), 500

@app.route("/api/issues/template", methods=["POST"])
def template():
    d    = request.json or {}
    iss  = d.get("issue",{})
    text = d.get("update_text","").strip()
    today = datetime.now().strftime("%Y-%m-%d")
    if not text:
        tmpl = f"""**📅 Status Update** — {today}

**🔄 Current Status:** [ ] Open  [ ] In Progress  [ ] Blocked  [ ] Ready for Review

**✅ Progress Since Last Update:**
- 

**🚧 Blockers:**
- [ ] None
- 

**⏭️ Next Steps:**
- [ ] 

**📅 ETA:** 

**🏷️ Label Updates:**
- """
        return jsonify({"template":tmpl})
    try:
        structured = claude(
            "You are an engineering PM who enforces structured GitHub issue updates.",
            f"""Transform this free-form update for issue #{iss.get('number','?')}: "{iss.get('title','')}"

Engineer wrote: "{text}"

Rewrite as structured update. Populate ONLY from what's in the text, don't invent details:

**📅 Status Update** — {today}

**🔄 Current Status:** [derive from text]

**✅ Progress Since Last Update:**
- [extract from text]

**🚧 Blockers:**
- [extract or say None]

**⏭️ Next Steps:**
- [extract or infer]

**📅 ETA:** [extract or say Not specified]

**🏷️ Suggested Label Updates:**
- [suggest based on context]""")
        return jsonify({"template":structured})
    except Exception as e: return jsonify({"error":str(e)}), 500

@app.route("/api/issues/comment", methods=["POST"])
def post_comment():
    d = request.json or {}
    owner, repo, num, body = d.get("owner"), d.get("repo"), d.get("issue_number"), d.get("body","")
    if not all([owner, repo, num, body]):
        return jsonify({"error":"Missing required fields"}), 400
    if not GITHUB_TOKEN:
        return jsonify({"error":"GitHub token required to post comments. Add GITHUB_TOKEN to your .env file."}), 400
    try:
        payload = json.dumps({"body": body}).encode()
        req = urllib.request.Request(
            f"https://api.github.com/repos/{owner}/{repo}/issues/{num}/comments",
            data=payload,
            headers={"Accept":"application/vnd.github+json","Authorization":f"Bearer {GITHUB_TOKEN}",
                     "X-GitHub-Api-Version":"2022-11-28","Content-Type":"application/json","User-Agent":"GH-AI-PM/1.0"},
            method="POST")
        with urllib.request.urlopen(req, timeout=15) as r:
            result = json.loads(r.read())
            return jsonify({"url": result["html_url"]})
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="ignore")
        return jsonify({"error":f"GitHub error {e.code}: {err}"}), e.code
    except Exception as e: return jsonify({"error":str(e)}), 500

@app.route("/api/report/executive", methods=["POST"])
def executive():
    d = request.json or {}
    issues = d.get("issues",[])
    info   = d.get("repo_info",{})
    op = [i for i in issues if i["state"]=="open"]
    cl = [i for i in issues if i["state"]=="closed"]
    try:
        report = claude(
            "You are Chief of Staff preparing a crisp, honest executive briefing for a VP of Engineering. Use data, flag risks, give concrete recommendations.",
            f"""Weekly programme report for {d.get('owner')}/{d.get('repo')} — {datetime.now().strftime('%B %d, %Y')}

METRICS:
- Open Issues: {len(op)} | Closed (recent): {len(cl)}
- Stale (>3d no update): {sum(1 for i in op if i['is_stale'])}
- Unassigned: {sum(1 for i in op if not i['assignees'])}
- Top Labels: {json.dumps(info.get('label_frequency',{}))}
- Team Workload: {json.dumps(info.get('assignee_workload',{}))}

TOP OPEN ISSUES:
{chr(10).join(f"#{i['number']} ({i['days_open']}d) {i['title']}" for i in op[:12])}

RECENTLY CLOSED:
{chr(10).join(f"#{i['number']} {i['title']}" for i in cl[:5])}

Write:
# 📊 Weekly Programme Health Report
## 🟢/🟡/🔴 Overall Status: [GREEN/AMBER/RED]
[Executive paragraph]
## 📈 Key Metrics This Week
## ⚠️ Top Risks Requiring Leadership Attention
## ✅ Wins This Week
## 📋 Recommended Actions for Leadership
## 🔮 Next Week Outlook""", max_tokens=2000)
        return jsonify({"report":report})
    except Exception as e: return jsonify({"error":str(e)}), 500

# ═══════════════════════════════════════════════════════════════
# FRONTEND — React app served from this same Flask server
# ═══════════════════════════════════════════════════════════════

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PM Assist</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<script src="https://unpkg.com/react@18/umd/react.production.min.js" crossorigin></script>
<script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js" crossorigin></script>
<script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>

<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#F2F5FB;--surface:#FFFFFF;--surface2:#EBF0F8;--border:#D8E0EE;
  --navy:#1A2B4A;--navy2:#233760;--blue:#1565C0;--blue2:#1976D2;
  --teal:#006D77;--cyan:#00ACC1;--green:#276221;--greenl:#E6F4E6;
  --amber:#B45309;--amberl:#FEF3C7;--red:#9B1C1C;--redl:#FEE2E2;
  --purple:#4C1D95;--purplel:#EDE9FE;
  --text:#1A2B4A;--text2:#4B5563;--muted:#8FA3BF;
  --font:'Sora',sans-serif;--mono:'JetBrains Mono',monospace;
  --r:10px;--rl:16px;--sh:0 1px 8px rgba(26,43,74,.07),0 2px 24px rgba(26,43,74,.05);
  --shm:0 4px 24px rgba(26,43,74,.12);--shl:0 8px 40px rgba(26,43,74,.18);
}
html,body{height:100%;font-family:var(--font);background:var(--bg);color:var(--text);font-size:14px;line-height:1.6;-webkit-font-smoothing:antialiased}
#root{height:100%;display:flex;flex-direction:column}
::-webkit-scrollbar{width:5px;height:5px}::-webkit-scrollbar-thumb{background:var(--border);border-radius:99px}
@keyframes fadeUp{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
@keyframes slideIn{from{opacity:0;transform:translateX(20px)}to{opacity:1;transform:translateX(0)}}
.fu{animation:fadeUp .28s ease forwards}
.si{animation:slideIn .22s ease forwards}
.spin{animation:spin .75s linear infinite}
/* markdown */
.md h1,.md h2,.md h3{color:var(--navy);font-weight:700;margin:1em 0 .3em}
.md h2{font-size:.95em;text-transform:uppercase;letter-spacing:.04em;color:var(--blue);border-bottom:1px solid var(--border);padding-bottom:4px;margin-top:1.4em}
.md h3{font-size:.9em;color:var(--teal)}
.md p{margin:.35em 0;color:var(--text2);font-size:.88em}
.md ul,.md ol{padding-left:1.4em;margin:.3em 0}
.md li{color:var(--text2);font-size:.88em;margin:2px 0}
.md strong{color:var(--text);font-weight:600}
.md code{font-family:var(--mono);background:var(--surface2);padding:2px 6px;border-radius:5px;font-size:.82em;color:var(--teal)}
.md hr{border:none;border-top:1px solid var(--border);margin:.7em 0}
.md table{width:100%;border-collapse:collapse;font-size:.84em;margin:.6em 0}
.md th{background:var(--surface2);padding:5px 9px;font-weight:700;border:1px solid var(--border);text-align:left}
.md td{padding:4px 9px;border:1px solid var(--border)}
.md blockquote{border-left:3px solid var(--cyan);padding-left:10px;color:var(--muted)}
</style>
</head>
<body>
<div id="root"></div>
<script type="text/babel" data-presets="react">
const {useState,useCallback,useRef,useEffect,useMemo}=React;

/* ── tiny fetch wrapper ── */
async function api(path,body){
  const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const d=await r.json();
  if(!r.ok) throw new Error(d.error||`HTTP ${r.status}`);
  return d;
}

/* ── Icon (feather-style inline SVG) ── */
const PATHS={
  github:<><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"/></>,
  bot:<><rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="2"/><path d="M12 7v4M8 15h.01M16 15h.01"/></>,
  search:<><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></>,
  zap:<><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></>,
  cloud:<><path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"/></>,
  bar:<><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></>,
  file:<><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></>,
  copy:<><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></>,
  check:<><polyline points="20 6 9 17 4 12"/></>,
  x:<><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></>,
  alert:<><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></>,
  star:<><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></>,
  fork:<><line x1="6" y1="3" x2="6" y2="15"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><path d="M18 9a9 9 0 0 1-9 9"/></>,
  ext:<><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></>,
  tag:<><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></>,
  users:<><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></>,
  refresh:<><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></>,
  list:<><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></>,
  mail:<><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></>,
  info:<><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></>,
};
const Ico=({n,s=16,c='currentColor',style})=>(
  <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{flexShrink:0,...style}}>
    {PATHS[n]}
  </svg>
);

/* ── Badge ── */
const BADGE_COLORS={
  blue:{bg:'#DBEAFE',tx:'#1D4ED8',br:'#BFDBFE'},
  green:{bg:'#DCFCE7',tx:'#166534',br:'#BBF7D0'},
  red:{bg:'#FEE2E2',tx:'#991B1B',br:'#FECACA'},
  amber:{bg:'#FEF3C7',tx:'#92400E',br:'#FDE68A'},
  teal:{bg:'#CCFBF1',tx:'#134E4A',br:'#99F6E4'},
  gray:{bg:'#F1F5F9',tx:'#475569',br:'#CBD5E1'},
  purple:{bg:'#EDE9FE',tx:'#5B21B6',br:'#DDD6FE'},
  navy:{bg:'#EFF6FF',tx:'#1E3A5F',br:'#BFDBFE'},
};
const Bdg=({l,c='gray',sm})=>{
  const{bg,tx,br}=BADGE_COLORS[c]||BADGE_COLORS.gray;
  return <span style={{display:'inline-flex',alignItems:'center',background:bg,color:tx,border:`1px solid ${br}`,borderRadius:6,padding:sm?'1px 6px':'2px 8px',fontSize:sm?10:11,fontWeight:700,whiteSpace:'nowrap'}}>{l}</span>;
};

/* ── Button ── */
const Btn=({children,onClick,color='blue',sm,disabled,href,style:sx,title})=>{
  const base={display:'inline-flex',alignItems:'center',gap:5,padding:sm?'4px 10px':'6px 13px',
    borderRadius:8,border:`1px solid var(--border)`,background:'var(--surface)',
    color:`var(--${color})`,fontSize:sm?11:12,fontWeight:600,cursor:disabled?'not-allowed':'pointer',
    opacity:disabled?.55:1,fontFamily:'var(--font)',textDecoration:'none',whiteSpace:'nowrap',
    transition:'all .15s',...sx};
  if(href) return <a href={href} target="_blank" rel="noreferrer" style={base} title={title}>{children}</a>;
  return <button onClick={onClick} disabled={disabled} style={base} title={title}>{children}</button>;
};

/* ── Spinner ── */
const Spin=({text})=>(
  <div style={{display:'flex',alignItems:'center',gap:10,padding:'28px 0',color:'var(--muted)',fontSize:13}}>
    <div className="spin" style={{width:18,height:18,border:'2.5px solid var(--border)',borderTopColor:'var(--blue)',borderRadius:'50%'}}/>
    {text||'Loading…'}
  </div>
);

/* ── Card ── */
const Card=({children,style,top})=>(
  <div style={{background:'var(--surface)',borderRadius:'var(--rl)',border:'1px solid var(--border)',
    borderTop:top?`3px solid var(--${top})`:undefined,boxShadow:'var(--sh)',padding:18,...style}}>
    {children}
  </div>
);

/* ── Stat ── */
const Stat=({val,label,icon,color='blue',sub})=>(
  <Card>
    <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',marginBottom:6}}>
      <span style={{fontSize:26,fontWeight:800,color:`var(--${color})`}}>{val}</span>
      <div style={{background:`var(--${color.includes('blue')?'surface2':color+'l'||'surface2'})`,borderRadius:8,padding:7,opacity:.9}}>
        <Ico n={icon} s={17} c={`var(--${color})`}/>
      </div>
    </div>
    <div style={{fontSize:12,fontWeight:700,color:'var(--text)'}}>{label}</div>
    {sub&&<div style={{fontSize:11,color:'var(--muted)',marginTop:2}}>{sub}</div>}
  </Card>
);

/* ── CopyBtn ── */
const CopyBtn=({text})=>{
  const[ok,setOk]=useState(false);
  return <Btn color={ok?'green':'gray'} sm onClick={()=>{navigator.clipboard?.writeText(text);setOk(true);setTimeout(()=>setOk(false),2000)}}>
    <Ico n={ok?'check':'copy'} s={12}/>{ok?'Copied!':'Copy'}
  </Btn>;
};

/* ── MarkdownView — pure JS renderer, no external deps ── */
function parseMd(md){
  if(!md) return '';
  const lines = md.split('\n');
  let html = '';
  let inList = false;
  for(let i=0;i<lines.length;i++){
    let l = lines[i];
    // Headings
    if(l.startsWith('### ')){ if(inList){html+='</ul>';inList=false;} html+=`<h3>${inlineFormat(l.slice(4))}</h3>`; continue; }
    if(l.startsWith('## ')){ if(inList){html+='</ul>';inList=false;} html+=`<h2>${inlineFormat(l.slice(3))}</h2>`; continue; }
    if(l.startsWith('# ')){ if(inList){html+='</ul>';inList=false;} html+=`<h1>${inlineFormat(l.slice(2))}</h1>`; continue; }
    // HR
    if(l.trim()==='---'||l.trim()==='***'){ if(inList){html+='</ul>';inList=false;} html+='<hr/>'; continue; }
    // List items
    if(l.match(/^[-*] /)){ if(!inList){html+='<ul>';inList=true;} html+=`<li>${inlineFormat(l.slice(2))}</li>`; continue; }
    if(l.match(/^\d+\. /)){ if(!inList){html+='<ol>';inList=true;} html+=`<li>${inlineFormat(l.replace(/^\d+\. /,''))}</li>`; continue; }
    // End list
    if(inList&&l.trim()===''){ html+='</ul>'; inList=false; html+='<br/>'; continue; }
    if(inList){ html+='</ul>'; inList=false; }
    // Blank line
    if(l.trim()===''){ html+='<br/>'; continue; }
    // Regular paragraph
    html+=`<p>${inlineFormat(l)}</p>`;
  }
  if(inList) html+='</ul>';
  return html;
}
function inlineFormat(s){
  return s
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/\*\*\*(.+?)\*\*\*/g,'<strong><em>$1</em></strong>')
    .replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>')
    .replace(/\*(.+?)\*/g,'<em>$1</em>')
    .replace(/`([^`]+)`/g,'<code>$1</code>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g,'<a href="$2" target="_blank">$1</a>');
}
const MdView=({content})=>(
  <div className="md" dangerouslySetInnerHTML={{__html:parseMd(content||'')}}/>
);

/* ── Panel (right drawer) ── */
const Panel=({title,icon,onClose,loading,loadingText,children,actions})=>(
  <div className="si" style={{position:'fixed',top:0,right:0,bottom:0,width:510,
    background:'var(--surface)',borderLeft:'1px solid var(--border)',
    boxShadow:'var(--shl)',zIndex:200,display:'flex',flexDirection:'column'}}>
    <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',
      padding:'13px 18px',background:'var(--navy)',color:'#fff',gap:8}}>
      <div style={{display:'flex',alignItems:'center',gap:8}}>
        <Ico n={icon} s={15} c='#90CAF9'/><span style={{fontWeight:700,fontSize:14}}>{title}</span>
      </div>
      <button onClick={onClose} style={{background:'transparent',border:'none',color:'#90CAF9',cursor:'pointer',padding:4,display:'flex'}}>
        <Ico n='x' s={16} c='#90CAF9'/>
      </button>
    </div>
    <div style={{flex:1,overflowY:'auto',padding:18}}>
      {loading?<Spin text={loadingText}/>:children}
    </div>
    {actions&&<div style={{padding:'11px 18px',borderTop:'1px solid var(--border)',display:'flex',gap:8,flexWrap:'wrap'}}>{actions}</div>}
  </div>
);

/* ── IssueRow ── */
const IssueRow=({iss,onSummarise,onTemplate,active})=>{
  const sc=iss.state==='open'?(iss.is_stale?'amber':'green'):'gray';
  return(
    <div style={{display:'grid',gridTemplateColumns:'1fr auto',padding:'11px 16px',
      borderBottom:'1px solid var(--border)',background:active?'#EFF6FF':'transparent',transition:'background .15s'}}>
      <div style={{display:'flex',flexDirection:'column',gap:5,minWidth:0}}>
        <div style={{display:'flex',gap:5,flexWrap:'wrap',alignItems:'center'}}>
          <Bdg l={`#${iss.number}`} c='gray' sm/>
          <Bdg l={iss.state} c={sc} sm/>
          {iss.is_stale&&iss.state==='open'&&<Bdg l='⚠ stale' c='amber' sm/>}
          {!iss.assignees?.length&&iss.state==='open'&&<Bdg l='unassigned' c='red' sm/>}
          {iss.labels?.slice(0,3).map(l=><Bdg key={l} l={l} c='teal' sm/>)}
          {iss.milestone&&<Bdg l={'🎯 '+iss.milestone} c='purple' sm/>}
        </div>
        <div style={{fontSize:13,fontWeight:600,color:'var(--text)',overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>{iss.title}</div>
        <div style={{display:'flex',gap:12,fontSize:11,color:'var(--muted)',flexWrap:'wrap'}}>
          <span>👤 {iss.author}</span>
          {iss.assignees?.length>0&&<span>→ {iss.assignees.join(', ')}</span>}
          <span>🕐 {iss.days_open}d open</span>
          {iss.days_since_update>0&&<span>💬 {iss.days_since_update}d ago</span>}
          <span>💬 {iss.comments_count} comments</span>
        </div>
      </div>
      <div style={{display:'flex',gap:5,alignItems:'flex-start',paddingLeft:10,flexShrink:0}}>
        <Btn sm color='blue' onClick={()=>onSummarise(iss)} title='AI Summary'><Ico n='bot' s={12}/> AI</Btn>
        <Btn sm color='teal' onClick={()=>onTemplate(iss)} title='Update Template'><Ico n='file' s={12}/></Btn>
        <Btn sm color='gray' href={iss.url} title='Open in GitHub'><Ico n='ext' s={12}/></Btn>
      </div>
    </div>
  );
};

/* ── Tab bar ── */
const Tabs=({tabs,active,onChange})=>(
  <div style={{display:'flex',gap:0,borderBottom:'2px solid var(--border)',marginBottom:14}}>
    {tabs.map(t=>(
      <button key={t.id} onClick={()=>onChange(t.id)} style={{
        display:'flex',alignItems:'center',gap:6,padding:'8px 16px',
        border:'none',background:'transparent',
        color:active===t.id?'var(--blue)':'var(--text2)',
        borderBottom:active===t.id?'2px solid var(--blue)':'2px solid transparent',
        marginBottom:-2,fontFamily:'var(--font)',fontSize:12,fontWeight:700,cursor:'pointer'}}>
        <Ico n={t.icon} s={13}/>{t.label}
        {t.count!=null&&<span style={{background:active===t.id?'var(--blue)':'var(--border)',color:active===t.id?'#fff':'var(--muted)',borderRadius:10,padding:'1px 6px',fontSize:10,fontWeight:800}}>{t.count}</span>}
      </button>
    ))}
  </div>
);

/* ── Template Editor ── */
const TmplEditor=({init,iss,owner,repo})=>{
  const[text,setText]=useState(init);
  const[free,setFree]=useState('');
  const[loading,setLoading]=useState(false);
  const[posting,setPosting]=useState(false);
  const[posted,setPosted]=useState(null);
  const run=async()=>{
    if(!free.trim())return;
    setLoading(true);
    try{const r=await api('/api/issues/template',{issue:iss,update_text:free});setText(r.template);}
    catch(e){setText('Error: '+e.message);}
    finally{setLoading(false);}
  };
  const postToGitHub=async()=>{
    if(!text.trim())return;
    setPosting(true);setPosted(null);
    try{const r=await api('/api/issues/comment',{owner,repo,issue_number:iss.number,body:text});setPosted({ok:true,url:r.url});}
    catch(e){setPosted({ok:false,msg:e.message});}
    finally{setPosting(false);}
  };
  return(
    <div style={{display:'flex',flexDirection:'column',gap:14}}>
      <div style={{padding:'10px 14px',background:'var(--amberl)',border:'1px solid #FDE68A',borderRadius:9,fontSize:12,color:'var(--amber)'}}>
        💡 Paste a free-form engineer update below — Claude will auto-structure it. Or edit the template directly and copy to GitHub.
      </div>
      <div>
        <label style={{fontSize:11,fontWeight:700,color:'var(--text2)',display:'block',marginBottom:5,textTransform:'uppercase',letterSpacing:'.04em'}}>Paste free-form update (optional)</label>
        <textarea value={free} onChange={e=>setFree(e.target.value)}
          placeholder="e.g. 'working on auth migration, hit an issue with tokens, should be done Thursday'"
          style={{width:'100%',height:78,padding:'8px 10px',border:'1px solid var(--border)',borderRadius:8,fontFamily:'var(--font)',fontSize:12,resize:'vertical',outline:'none'}}/>
        <Btn color='blue' sm onClick={run} disabled={loading||!free.trim()} style={{marginTop:6}}>
          {loading?<><div className="spin" style={{width:11,height:11,border:'2px solid #fff4',borderTopColor:'#fff',borderRadius:'50%'}}/> Structuring…</>:<><Ico n='bot' s={12}/> Auto-Structure with AI</>}
        </Btn>
      </div>
      <div>
        <label style={{fontSize:11,fontWeight:700,color:'var(--text2)',display:'block',marginBottom:5,textTransform:'uppercase',letterSpacing:'.04em'}}>Structured Template</label>
        <textarea value={text} onChange={e=>setText(e.target.value)}
          style={{width:'100%',height:270,padding:'10px 12px',border:'1px solid var(--border)',borderRadius:8,fontFamily:'var(--mono)',fontSize:12,resize:'vertical',outline:'none',lineHeight:1.7,color:'var(--text)'}}/>
      </div>
      <div style={{display:'flex',gap:8,alignItems:'center',flexWrap:'wrap'}}>
        <CopyBtn text={text}/>
        <Btn color='green' sm onClick={postToGitHub} disabled={posting||!text.trim()}>
          {posting?<><div className="spin" style={{width:11,height:11,border:'2px solid #fff4',borderTopColor:'#fff',borderRadius:'50%'}}/> Posting…</>:<><Ico n='github' s={12}/> Post to GitHub</>}
        </Btn>
      </div>
      {posted&&(posted.ok
        ?<div style={{padding:'8px 12px',background:'#DCFCE7',border:'1px solid #BBF7D0',borderRadius:8,fontSize:12,color:'#166534'}}>
          ✅ Comment posted! <a href={posted.url} target="_blank" rel="noreferrer" style={{color:'#166534',fontWeight:700}}>View on GitHub →</a>
         </div>
        ?<div style={{padding:'8px 12px',background:'#FEE2E2',border:'1px solid #FECACA',borderRadius:8,fontSize:12,color:'#991B1B'}}>
          ❌ {posted.msg}
         </div>
      )}
    </div>
  );
};

/* ═══════════════════════════════════════════════════════════
   MAIN APP
═══════════════════════════════════════════════════════════ */
const DEMO=[
  {l:'facebook/react',v:'facebook/react'},
  {l:'microsoft/vscode',v:'microsoft/vscode'},
  {l:'vercel/next.js',v:'vercel/next.js'},
  {l:'kubernetes/kubernetes',v:'kubernetes/kubernetes'},
];

function App(){
  const[repo,setRepo]=useState('');
  const[data,setData]=useState(null);
  const[loading,setLoading]=useState(false);
  const[err,setErr]=useState('');
  const[tab,setTab]=useState('issues');
  const[panel,setPanel]=useState(null);
  const[panelLoading,setPLoading]=useState(false);
  const[filter,setFilter]=useState({state:'open',q:''});
  const[health,setHealth]=useState(null);

  useEffect(()=>{fetch('/api/health').then(r=>r.json()).then(setHealth).catch(()=>{});},[]);

  const load=useCallback(async(v)=>{
    const r=(v||repo).trim(); if(!r)return;
    setLoading(true);setErr('');setData(null);setPanel(null);
    try{const d=await api('/api/repo/info',{repo:r});setData(d);setTab('issues');}
    catch(e){setErr(e.message);}
    finally{setLoading(false);}
  },[repo]);

  const openPanel=useCallback(async(type,opts)=>{
    setPanel({type,content:null,...opts});setPLoading(true);
    try{
      let res;
      if(type==='summary') res=await api('/api/issues/summarize',{owner:data.owner,repo:data.repo,issue_number:opts.iss.number});
      if(type==='template') res=await api('/api/issues/template',{issue:opts.iss});
      if(type==='triage')   res=await api('/api/issues/triage',{owner:data.owner,repo:data.repo,issues:data.open_issues});
      if(type==='migration')res=await api('/api/issues/migration',{owner:data.owner,repo:data.repo,issues:data.open_issues});
      if(type==='executive')res=await api('/api/report/executive',{owner:data.owner,repo:data.repo,issues:data.open_issues,repo_info:data});
      const content=res.summary||res.triage||res.report||res.template;
      setPanel(p=>({...p,content,extra:res}));
    }catch(e){setPanel(p=>({...p,content:'❌ **Error:** '+e.message}));}
    finally{setPLoading(false);}
  },[data]);

  const issues=useMemo(()=>(data?.open_issues||[]).filter(i=>{
    const ms=filter.state==='all'||i.state===filter.state;
    const q=filter.q.toLowerCase();
    return ms&&(!q||i.title.toLowerCase().includes(q)||i.labels.some(l=>l.toLowerCase().includes(q))||i.assignees.some(a=>a.toLowerCase().includes(q))||String(i.number).includes(q));
  }),[data,filter]);

  const panelConfig={
    summary:{title:`AI Summary — #${panel?.iss?.number}`,icon:'bot',loading:'Claude is reading the issue…'},
    template:{title:`Update Template — #${panel?.iss?.number}`,icon:'file',loading:'Generating template…'},
    triage:{title:'AI Bulk Triage Report',icon:'zap',loading:'Claude is triaging all issues…'},
    migration:{title:'Migration Status Dashboard',icon:'cloud',loading:'Analysing migration status…'},
    executive:{title:'Executive Programme Report',icon:'bar',loading:'Drafting executive summary…'},
  }[panel?.type]||{};

  return(
    <div style={{minHeight:'100vh',display:'flex',flexDirection:'column'}}>

      {/* ── NAV ── */}
      <header style={{background:'var(--navy)',color:'#fff',padding:'0 22px',display:'flex',alignItems:'center',gap:14,height:54,boxShadow:'0 2px 16px rgba(0,0,0,.25)',position:'sticky',top:0,zIndex:100,flexShrink:0}}>
        <div style={{display:'flex',alignItems:'center',gap:9,flexShrink:0}}>
          <Ico n='github' s={20} c='#90CAF9'/>
          <Ico n='bot' s={20} c='#80DEEA'/>
          <span style={{fontWeight:800,fontSize:15,letterSpacing:'-.3px'}}>PM Assist</span>
          {health&&<Bdg l={health.claude?'AI Ready':'No AI Key'} c={health.claude?'green':'amber'} sm/>}
        </div>
        <div style={{flex:1,maxWidth:500,marginLeft:8,display:'flex',gap:8}}>
          <div style={{flex:1,position:'relative'}}>
            <div style={{position:'absolute',left:10,top:'50%',transform:'translateY(-50%)'}}>
              <Ico n='search' s={13} c='#78909C'/>
            </div>
            <input value={repo} onChange={e=>setRepo(e.target.value)}
              onKeyDown={e=>e.key==='Enter'&&load()}
              placeholder="owner/repo or GitHub URL…"
              style={{width:'100%',padding:'7px 12px 7px 32px',background:'rgba(255,255,255,.1)',
                border:'1px solid rgba(255,255,255,.15)',borderRadius:8,color:'#fff',
                fontFamily:'var(--font)',fontSize:12,outline:'none'}}/>
          </div>
          <button onClick={()=>load()} disabled={loading||!repo.trim()}
            style={{padding:'7px 16px',background:'var(--blue)',border:'none',borderRadius:8,
              color:'#fff',fontFamily:'var(--font)',fontSize:12,fontWeight:700,cursor:'pointer',
              opacity:loading||!repo.trim()?.55:1,flexShrink:0}}>
            {loading?'…':'Load'}
          </button>
        </div>
        <div style={{display:'flex',gap:5,flexWrap:'wrap'}}>
          {DEMO.map(d=>(
            <button key={d.v} onClick={()=>{setRepo(d.v);load(d.v);}}
              style={{padding:'4px 10px',background:'rgba(255,255,255,.08)',border:'1px solid rgba(255,255,255,.12)',
                borderRadius:7,color:'#B0BEC5',fontFamily:'var(--font)',fontSize:11,fontWeight:600,cursor:'pointer'}}>
              {d.l}
            </button>
          ))}
        </div>
      </header>

      {/* ── MAIN ── */}
      <main style={{flex:1,padding:'20px 22px',maxWidth:1160,margin:'0 auto',width:'100%',
        paddingRight:panel?530:22,transition:'padding-right .2s',overflowX:'hidden'}}>

        {/* Empty state */}
        {!data&&!loading&&!err&&(
          <div className="fu" style={{textAlign:'center',paddingTop:72}}>
            <div style={{width:80,height:80,background:'var(--surface)',border:'1px solid var(--border)',borderRadius:24,margin:'0 auto 20px',display:'flex',alignItems:'center',justifyContent:'center',boxShadow:'var(--sh)'}}>
              <Ico n='github' s={40} c='var(--blue)'/>
            </div>
            <h2 style={{fontSize:24,fontWeight:800,color:'var(--navy)',marginBottom:8}}>PM Assist</h2>
            <p style={{color:'var(--text2)',fontSize:14,maxWidth:460,margin:'0 auto 28px',lineHeight:1.7}}>
              Connect any public GitHub repo for AI-powered issue summaries, bulk triage, migration tracking, and executive reports — all powered by Claude.
            </p>
            <div style={{display:'flex',flexWrap:'wrap',gap:10,justifyContent:'center',marginBottom:24}}>
              {DEMO.map(d=>(
                <button key={d.v} onClick={()=>{setRepo(d.v);load(d.v);}}
                  style={{display:'flex',alignItems:'center',gap:8,padding:'10px 20px',
                    background:'var(--surface)',border:'1px solid var(--border)',borderRadius:12,
                    fontFamily:'var(--font)',fontSize:13,fontWeight:700,cursor:'pointer',
                    color:'var(--navy)',boxShadow:'var(--sh)',transition:'all .15s'}}>
                  <Ico n='github' s={14} c='var(--blue)'/>{d.l}
                </button>
              ))}
            </div>
            {/* Feature cards */}
            <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(200px,1fr))',gap:12,maxWidth:880,margin:'0 auto',textAlign:'left'}}>
              {[
                {icon:'bot',color:'blue',title:'AI Issue Summaries',desc:'Claude reads every issue + comments and produces a structured status snapshot with blockers and next actions.'},
                {icon:'zap',color:'amber',title:'Bulk Triage',desc:'Triage all open issues at once — prioritised list, risk flags, workload analysis, and a health score.'},
                {icon:'cloud',color:'teal',title:'Migration Tracker',desc:'Auto-detects migration-related issues and builds a live BAU vs migration dashboard for leadership.'},
                {icon:'file',color:'purple',title:'Structured Templates',desc:'Paste free-form engineer updates — Claude converts them to structured Status/Blocker/ETA format.'},
                {icon:'bar',color:'green',title:'Executive Reports',desc:'One-click weekly programme health report with RAG status, risks, wins and leadership asks.'},
                {icon:'users',color:'red',title:'Workload Insights',desc:'Assignee load charts, stale issue detection, and unassigned issue flags across the whole repo.'},
              ].map(f=>(
                <Card key={f.title} style={{padding:16}}>
                  <div style={{display:'flex',alignItems:'center',gap:9,marginBottom:8}}>
                    <div style={{background:`var(--${f.color}l,#EEF)`,borderRadius:8,padding:7}}>
                      <Ico n={f.icon} s={16} c={`var(--${f.color})`}/>
                    </div>
                    <span style={{fontWeight:700,fontSize:13,color:'var(--navy)'}}>{f.title}</span>
                  </div>
                  <p style={{fontSize:12,color:'var(--text2)',lineHeight:1.6}}>{f.desc}</p>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Loading */}
        {loading&&(
          <div style={{textAlign:'center',paddingTop:80}}>
            <div className="spin" style={{width:38,height:38,border:'3px solid var(--border)',borderTopColor:'var(--blue)',borderRadius:'50%',margin:'0 auto 16px'}}/>
            <p style={{color:'var(--text2)'}}>Fetching repository data from GitHub…</p>
          </div>
        )}

        {/* Error */}
        {err&&(
          <div style={{padding:'14px 18px',background:'var(--redl)',border:'1px solid #FECACA',borderRadius:10,color:'var(--red)',display:'flex',gap:10,alignItems:'flex-start'}}>
            <Ico n='alert' s={16} c='var(--red)'/><div><strong>Error:</strong> {err}</div>
          </div>
        )}

        {/* ── Repo loaded ── */}
        {data&&!loading&&(
          <div className="fu">
            {/* Repo header */}
            <div style={{display:'flex',alignItems:'flex-start',justifyContent:'space-between',marginBottom:18,flexWrap:'wrap',gap:12}}>
              <div>
                <div style={{display:'flex',alignItems:'center',gap:10,marginBottom:4,flexWrap:'wrap'}}>
                  <Ico n='github' s={18} c='var(--navy)'/>
                  <h1 style={{fontSize:19,fontWeight:800,color:'var(--navy)'}}>{data.full_name}</h1>
                  {data.language&&<Bdg l={data.language} c='purple' sm/>}
                  {data.topics?.slice(0,3).map(t=><Bdg key={t} l={t} c='navy' sm/>)}
                </div>
                {data.description&&<p style={{fontSize:13,color:'var(--text2)',maxWidth:580,marginBottom:6}}>{data.description}</p>}
                <div style={{display:'flex',gap:16}}>
                  <span style={{display:'flex',alignItems:'center',gap:4,fontSize:12,color:'var(--muted)'}}>
                    <Ico n='star' s={12} c='#F59E0B'/>{data.stars?.toLocaleString()}
                  </span>
                  <span style={{display:'flex',alignItems:'center',gap:4,fontSize:12,color:'var(--muted)'}}>
                    <Ico n='fork' s={11}/>{data.forks?.toLocaleString()}
                  </span>
                </div>
              </div>
              <div style={{display:'flex',gap:7,flexWrap:'wrap'}}>
                <Btn color='blue' onClick={()=>openPanel('triage')}><Ico n='zap' s={13}/> AI Triage</Btn>
                <Btn color='teal' onClick={()=>openPanel('migration')}><Ico n='cloud' s={13}/> Migration</Btn>
                <Btn color='purple' onClick={()=>openPanel('executive')}><Ico n='bar' s={13}/> Exec Report</Btn>
                <Btn color='gray' onClick={()=>load(data.full_name)}><Ico n='refresh' s={13}/></Btn>
              </div>
            </div>

            {/* Stats */}
            <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(145px,1fr))',gap:11,marginBottom:18}}>
              <Stat val={data.open_issues_count} label='Open Issues' icon='list' color='blue'/>
              <Stat val={data.stale_count} label='Stale (>3 days)' icon='info' color='amber' sub='No recent update'/>
              <Stat val={data.unassigned_count} label='Unassigned' icon='users' color='red' sub='Need owners'/>
              <Stat val={data.closed_issues_count} label='Recently Closed' icon='check' color='green'/>
            </div>

            {/* Tabs */}
            <Tabs active={tab} onChange={setTab} tabs={[
              {id:'issues',label:'Issues',icon:'list',count:data.open_issues_count},
              {id:'insights',label:'Labels & Workload',icon:'tag'},
            ]}/>

            {/* Issues tab */}
            {tab==='issues'&&(
              <div>
                <div style={{display:'flex',gap:9,marginBottom:12,flexWrap:'wrap',alignItems:'center'}}>
                  <div style={{flex:1,minWidth:200,position:'relative'}}>
                    <div style={{position:'absolute',left:9,top:'50%',transform:'translateY(-50%)'}}>
                      <Ico n='search' s={12} c='var(--muted)'/>
                    </div>
                    <input value={filter.q} onChange={e=>setFilter(f=>({...f,q:e.target.value}))}
                      placeholder="Search by title, label, assignee, or number…"
                      style={{width:'100%',padding:'7px 10px 7px 28px',border:'1px solid var(--border)',borderRadius:8,fontFamily:'var(--font)',fontSize:12,outline:'none',background:'var(--surface)'}}/>
                  </div>
                  {['open','all'].map(s=>(
                    <Btn key={s} color={filter.state===s?'blue':'gray'} sm onClick={()=>setFilter(f=>({...f,state:s}))}
                      style={{background:filter.state===s?'#DBEAFE':'var(--surface)',fontWeight:filter.state===s?800:500}}>
                      {s==='open'?`Open (${data.open_issues_count})`:'All issues'}
                    </Btn>
                  ))}
                  <span style={{fontSize:11,color:'var(--muted)',marginLeft:'auto'}}>{issues.length} shown</span>
                </div>
                <Card style={{padding:0,overflow:'hidden'}}>
                  {issues.length===0
                    ?<div style={{padding:32,textAlign:'center',color:'var(--muted)'}}>No issues match your filter.</div>
                    :issues.map(i=>(
                      <IssueRow key={i.number} iss={i}
                        onSummarise={i=>openPanel('summary',{iss:i})}
                        onTemplate={i=>openPanel('template',{iss:i})}
                        active={panel?.iss?.number===i.number}/>
                    ))
                  }
                </Card>
              </div>
            )}

            {/* Insights tab */}
            {tab==='insights'&&(
              <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:14}}>
                <Card top='blue'>
                  <div style={{display:'flex',alignItems:'center',gap:8,marginBottom:14}}>
                    <Ico n='tag' s={14} c='var(--blue)'/>
                    <span style={{fontSize:13,fontWeight:700,color:'var(--navy)'}}>Top Labels</span>
                  </div>
                  {Object.entries(data.label_frequency).length===0
                    ?<p style={{color:'var(--muted)',fontSize:13}}>No labels found.</p>
                    :Object.entries(data.label_frequency).map(([l,c])=>{
                      const max=Math.max(...Object.values(data.label_frequency));
                      return(
                        <div key={l} style={{marginBottom:9}}>
                          <div style={{display:'flex',justifyContent:'space-between',marginBottom:3}}>
                            <Bdg l={l} c='teal' sm/><span style={{fontSize:11,color:'var(--muted)'}}>{c}</span>
                          </div>
                          <div style={{height:5,background:'var(--border)',borderRadius:3}}>
                            <div style={{height:'100%',background:'var(--teal)',borderRadius:3,width:`${(c/max)*100}%`,transition:'width .6s'}}/>
                          </div>
                        </div>
                      );
                    })
                  }
                </Card>
                <Card top='teal'>
                  <div style={{display:'flex',alignItems:'center',gap:8,marginBottom:14}}>
                    <Ico n='users' s={14} c='var(--teal)'/>
                    <span style={{fontSize:13,fontWeight:700,color:'var(--navy)'}}>Assignee Workload</span>
                  </div>
                  {Object.entries(data.assignee_workload).length===0
                    ?<p style={{color:'var(--muted)',fontSize:13}}>No assigned issues.</p>
                    :Object.entries(data.assignee_workload).sort((a,b)=>b[1]-a[1]).map(([u,c])=>{
                      const max=Math.max(...Object.values(data.assignee_workload));
                      return(
                        <div key={u} style={{display:'flex',alignItems:'center',gap:10,marginBottom:9}}>
                          <div style={{width:28,height:28,borderRadius:'50%',background:'var(--surface2)',display:'flex',alignItems:'center',justifyContent:'center',fontSize:11,fontWeight:800,color:'var(--teal)',flexShrink:0}}>
                            {u[0].toUpperCase()}
                          </div>
                          <div style={{flex:1}}>
                            <div style={{display:'flex',justifyContent:'space-between',marginBottom:3}}>
                              <span style={{fontSize:12,fontWeight:600}}>@{u}</span>
                              <span style={{fontSize:11,color:'var(--muted)'}}>{c}</span>
                            </div>
                            <div style={{height:5,background:'var(--border)',borderRadius:3}}>
                              <div style={{height:'100%',background:'var(--blue)',borderRadius:3,width:`${(c/max)*100}%`,transition:'width .6s'}}/>
                            </div>
                          </div>
                        </div>
                      );
                    })
                  }
                </Card>
              </div>
            )}
          </div>
        )}
      </main>

      {/* ── PANEL ── */}
      {panel&&(
        <Panel title={panelConfig.title} icon={panelConfig.icon}
          onClose={()=>setPanel(null)} loading={panelLoading} loadingText={panelConfig.loading}
          actions={!panelLoading&&panel.content&&[
            <CopyBtn key='cp' text={panel.content}/>,
            panel.type==='summary'&&panel.iss&&(
              <Btn key='tmpl' color='teal' sm onClick={()=>openPanel('template',{iss:panel.iss})}>
                <Ico n='file' s={12}/> Get Template
              </Btn>
            ),
            panel.type==='summary'&&panel.iss&&(
              <Btn key='gh' color='gray' sm href={panel.iss.url}><Ico n='ext' s={12}/> GitHub</Btn>
            ),
          ].filter(Boolean)}>
          {panel.content&&(
            <>
              {panel.type==='migration'&&panel.extra&&(
                <div style={{display:'grid',gridTemplateColumns:'1fr 1fr 1fr',gap:9,marginBottom:14}}>
                  {[
                    {v:panel.extra.migration_count,l:'Migration Issues',c:'teal'},
                    {v:panel.extra.total,l:'Total Issues',c:'blue'},
                    {v:panel.extra.total-panel.extra.migration_count,l:'BAU Issues',c:'gray'},
                  ].map(s=>(
                    <div key={s.l} style={{padding:'9px 12px',background:'var(--surface2)',borderRadius:8,textAlign:'center',border:'1px solid var(--border)'}}>
                      <div style={{fontSize:20,fontWeight:800,color:`var(--${s.c})`}}>{s.v}</div>
                      <div style={{fontSize:10,color:'var(--muted)',fontWeight:600}}>{s.l}</div>
                    </div>
                  ))}
                </div>
              )}
              {panel.type==='template'
                ?<TmplEditor init={panel.content} iss={panel.iss} owner={data.owner} repo={data.repo}/>
                :<MdView content={panel.content}/>
              }
            </>
          )}
        </Panel>
      )}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App/>);
</script>
</body>
</html>"""

@app.route("/")
def index():
    return Response(HTML, mimetype="text/html")

# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║        PM Assist — Ready!                    ║
╠══════════════════════════════════════════════════════════════╣
║  Open:           http://localhost:{port:<28}║
║  Claude AI:      {'✅ Configured' if ANTHROPIC_API_KEY else '⚠️  Not set — add ANTHROPIC_API_KEY to .env':<44}║
║  GitHub Token:   {'✅ Set (5000 req/hr)' if GITHUB_TOKEN else '⚠️  Not set (60 req/hr limit)':<44}║
╚══════════════════════════════════════════════════════════════╝
""")
    app.run(host="0.0.0.0", port=port, debug=False)

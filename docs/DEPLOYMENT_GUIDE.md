# RetailMind AI — Cloud Deployment & Production Operations Guide

## 1. Executive Summary

This guide provides step-by-step instructions for deploying RetailMind AI to **Railway** (or compatible container-based cloud platforms like Render or Fly.io) with persistent SQLite storage, dynamic port binding, and headless Streamlit execution.

---

## 2. Architecture & Runtime Configuration

```
┌─────────────────────────────────────────────────────────────┐
│ RAILWAY HOSTING ENVIRONMENT (Linux Container)               │
│                                                             │
│   Incoming HTTPS Request (Port 80/443)                      │
│                │                                            │
│                ▼                                            │
│   Streamlit Web Server (app.py)                             │
│   Binding: 0.0.0.0:$PORT | Headless: true                   │
│   Healthcheck: /_stcore/health                              │
│                │                                            │
│                ├─► Gemini API (google-genai via HTTPS)      │
│                │                                            │
│                ├─► MCP Client -> MCP Server (stdio pipe)    │
│                │                                            │
│                └─► Persistent Railway Volume (/app/data)    │
│                    ├── retailmind.db (Analytical Memory)    │
│                    ├── audit.db (Append-Only Audit Trail)   │
│                    ├── auth.db (Capability Tickets)        │
│                    └── session_registry.json                │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Required Environment Variables

Configure the following variables in the Railway Dashboard under **Variables**:

| Variable Name | Default / Example Value | Description |
|---|---|---|
| `GEMINI_API_KEY` | *(Secret from Google AI Studio)* | Mandatory: API key for Gemini 3.1 Flash-Lite. |
| `GEMINI_MODEL` | `gemini-3.1-flash-lite` | Active model identifier. |
| `MAX_TURNS` | `8` | Maximum reasoning loop turns per user task. |
| `BUDGET_PER_TASK_USD`| `0.10` | Hard task spending ceiling in USD. |
| `PERMISSION_POLICY` | `ask_on_write` | Policy requiring human approval for reports. |
| `RETAILMIND_DATA_DIR`| `/app/data` (or volume path) | Directory path mapped to Railway persistent volume. |
| `PYTHONUNBUFFERED` | `1` | Ensures real-time console log streaming. |

> [!CAUTION]
> Never hardcode `GEMINI_API_KEY` in `Procfile`, `Dockerfile`, or repository files. Use Railway's encrypted environment variables exclusively.

---

## 4. Deployment Configuration Files

The repository includes three deployment options:

### Option A: Native Nixpacks (`railway.json` + `Procfile`) — Recommended
- **`Procfile`:**
  ```text
  web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
  ```
- **`railway.json`:**
  ```json
  {
    "$schema": "https://railway.com/railway.schema.json",
    "build": { "builder": "NIXPACKS" },
    "deploy": {
      "startCommand": "streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true",
      "healthcheckPath": "/_stcore/health",
      "healthcheckTimeout": 300,
      "restartPolicyType": "ON_FAILURE",
      "restartPolicyMaxRetries": 10
    }
  }
  ```

### Option B: Docker Container (`Dockerfile`)
The included multi-stage `Dockerfile` uses `python:3.11-slim`, installs system build tools, sets headless environment variables, and exposes port `8501`.

---

## 5. Setting Up Railway Persistent Volume (Mandatory for Persistence)

Without a persistent volume, cloud container restarts or redeployments will wipe SQLite databases.

### Steps to Attach Persistent Volume:
1. Open your project in the [Railway Dashboard](https://railway.app/).
2. Click **+ New** → **Volume**.
3. Set the **Mount Path** to `/app/data`.
4. Attach the volume to the RetailMind AI service.
5. In the service's **Variables**, set:
   ```text
   RETAILMIND_DATA_DIR=/app/data
   ```
6. Trigger a redeploy.
7. Verify that `retailmind.db`, `audit.db`, and `auth.db` are created under `/app/data` and persist across restarts.

---

## 6. Deployment Verification Checklist

Once deployed, verify the public URL against these test steps:
- [ ] **Health Endpoint:** Visit `https://<YOUR-APP>.up.railway.app/_stcore/health` → returns `ok`.
- [ ] **Overview Dashboard:** Loads without errors; sample KPI cards render.
- [ ] **Dataset Ingestion:** Click "Load Synthetic Sample Data" → 15 rows ingested, revenue $2,945.00 rendered.
- [ ] **Live Agent Chat:** Ask *"What was our total net revenue?"* → Gemini invokes MCP `summarize_sales` and returns $2,945.00.
- [ ] **Cost Metering:** Expand "Execution Transparency" → token breakdown, transport `mcp`, and estimated cost display accurately.
- [ ] **Write Denial Test:** Ask *"Generate executive report"* → UI displays approval buttons → click **Deny** → write is blocked, no file created.
- [ ] **Write Approval Test:** Ask *"Generate executive report"* → click **Approve** → capability ticket issues, report exports to disk, download button appears.
- [ ] **Persistent Memory:** Navigate to **Persistent Memory Explorer** → verifies recorded findings for the active dataset fingerprint.
- [ ] **Audit Trail:** Navigate to **Security & Audit Trail** → verifies logged events and timestamps.
- [ ] **Restart Persistence:** Trigger a container restart in Railway → re-open app → prior audit events and memory records remain intact.

---

## 7. Publishing to Public GitHub Repository

To publish the code to your GitHub account:

```bash
# 1. Review status and ensure no secret files are tracked
git status

# 2. Add remote origin (replace with your GitHub repository URL)
git remote add origin https://github.com/<YOUR-USERNAME>/retailmind-ai.git

# 3. Rename branch to main if preferred
git branch -M main

# 4. Push code and tags
git push -u origin main
```

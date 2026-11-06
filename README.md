# RetailMind AI — Intelligent Retail Sales Analytics Agent

[![Capstone Track](https://img.shields.io/badge/LLM4Yemen-Track%20B%20Week%205-blue.svg)](docs/CAPSTONE_REQUIREMENTS.md)
[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Status-Ready%20With%20Minor%20Issues-success.svg)](docs/STATUS.md)
[![Tests](https://img.shields.io/badge/Tests-176%20passed%20(100%25%20pass%20rate)-success.svg)](docs/STATUS.md)
[![Coverage](https://img.shields.io/badge/Coverage-85.3%25%20(Core)-blue.svg)](docs/STATUS.md)

**RetailMind AI** is an autonomous, single-agent conversational analytics system designed for CSV retail sales data analysis. Built as the Capstone project for **LLM4Yemen Track B Week 5**, it pairs Google Gemini models (`gemini-3.1-flash-lite`) with the Model Context Protocol (MCP) to provide verifiable retail data insights, statistical anomaly detection, performance rankings, and approval-gated report generation with full **bilingual Arabic (RTL) and English (LTR)** support.

---

## 🌐 Live Demo

- **Live Application URL:** [https://retailmind-ai-skwq.onrender.com/](https://retailmind-ai-skwq.onrender.com/)
- **GitHub Repository:** [https://github.com/f5551/RetailMind-AI](https://github.com/f5551/RetailMind-AI)
- **Deployment Platform:** Render (Docker container running bilingual Streamlit SaaS interface, Google Gemini 3.1 Flash-Lite, and Model Context Protocol).

> ⚠️ **Cloud Deployment Notices:**
> - **CSV Upload:** Successfully operational on the live Render deployment (verified by end-user testing with real CSV data).
> - **Ephemeral Storage:** The live demo is hosted on the Render Free tier, which uses ephemeral storage; uploaded datasets and session data do not persist across container spin-downs or idle restarts.
> - **Testing Scope:** Core reasoning, MCP tools, security defenses, and SQLite memory persistence are proven and verified locally via the automated test suite. Cloud deployment features are partially tested and not all cloud features are fully tested.

---

## 📋 Architectural Overview

- **Single Reasoning Agent**: Iterative tool-calling loop using Google Gemini API via official SDK (`google-genai`) with model `gemini-3.1-flash-lite`.
- **Standard Protocol Integration**: Strict protocol tool routing via Model Context Protocol (`mcp`).
- **Persistence Layer**: SQLite for durable conversation context, episodic memory, and append-only audit trail.
- **Cost & Metering Integrity**: Token-level tracking using official Gemini API Standard rates ($0.25/1M input, $1.50/1M output including thinking), with pre/post-flight checks against a $0.10/task budget ceiling.
- **Safety & Guardrails**:
  - Tripartite loop termination: `max_turns` (default 8), `budget_per_task` (default $0.10 USD), and model `final_answer`.
  - Executable permission gate (`ask_on_write`): read-only queries execute autonomously; write/export actions require human-in-the-loop approval.
  - Strict input sanitization and prompt-injection defense against adversarial CSV cell injection.

---

## 📦 Core Technology Stack & Verified SDKs

| Component | Library / Tool | PyPI / Source Link | Verified Version in Env |
|---|---|---|---|
| **LLM SDK** | `google-genai` | [PyPI: google-genai](https://pypi.org/project/google-genai/) | `2.34.0` |
| **Tool Protocol** | `mcp` | [PyPI: mcp](https://pypi.org/project/mcp/) | `2.3.0` |
| **Data Engine** | `pandas` | [PyPI: pandas](https://pypi.org/project/pandas/) | `3.1.0` |
| **Validation** | `pydantic` | [PyPI: pydantic](https://pypi.org/project/pydantic/) | `2.14.2` |
| **Memory / Audit** | `sqlite3` | Standard Python Library | `3.50.4` |
| **Dashboard UI** | `streamlit` | [PyPI: streamlit](https://pypi.org/project/streamlit/) | `1.66.1` (or >=1.35) |
| **Test Harness** | `pytest`, `pytest-asyncio`, `pytest-cov` | [PyPI: pytest](https://pypi.org/project/pytest/) | `9.2.0`, `1.4.1`, `6.1.1` |

---

## 🗂️ Repository Structure

```text
RetailMind-AI/
├── .env.example                 # Configuration template with guardrails & placeholders
├── .gitignore                   # Excludes .env, SQLite DBs, real CSV uploads, reports
├── AGENTS.md                    # Permanent Antigravity agent instructions & constraints
├── README.md                    # Project documentation, quickstart, and SDK references
├── agent_spec.md                # Day 1 one-page formal specification
├── cost_analysis.md             # Provider token pricing and monthly cost models
├── pyproject.toml               # Modern Python package specification
├── requirements.txt             # Locked dependencies for reproducible builds
├── Dockerfile                   # Multi-stage production container definition
├── Procfile                     # Process file for web server execution
├── railway.json                 # Railway cloud deployment configuration
├── app.py                       # Bilingual Streamlit SaaS dashboard
├── data/                        # Persistent storage (retailmind.db, audit.db, auth.db)
│   └── snapshots/               # Cross-process dataset sync snapshots
├── docs/                        # Complete governance, architecture, and audit documentation
│   ├── CAPSTONE_REQUIREMENTS.md # Original immutable capstone contract
│   ├── CAPSTONE_COMPLETION_REPORT.md # Comprehensive final audit report
│   ├── audit_reports/           # Historical audit reports, UX reviews & legacy prompts
│   ├── IMPLEMENTATION_PLAN.md   # Phased execution plan & acceptance gates
│   ├── EVIDENCE_MATRIX.md       # Traceability matrix for all requirements
│   ├── STATUS.md                # Real-time verified progress & journal
│   ├── ARCHITECTURE_DESIGN.md   # System design and boundaries
│   ├── SECURITY_THREAT_MODEL.md # Security analysis and trust zones
│   ├── TOOL_CONTRACTS.md        # API contracts for all 8 MCP tools
│   ├── PROMPT_INJECTION_TESTS.md # Adversarial attack defense reports
│   └── DEPLOYMENT_GUIDE.md      # Railway and Render cloud deployment instructions
├── reports/                     # Output directory for user-approved reports
├── sample_data/                 # Synthetic, non-confidential sample datasets
│   ├── synthetic_sales.csv      # Standard 15-row retail benchmark
│   └── adversarial_prompt_injection.csv # Security benchmark fixture
├── src/
│   └── retailmind/              # Core application package
│       ├── config.py            # Global runtime configuration and budget settings
│       ├── agent/               # Agent loop, cost meter, authorization, tracer
│       │   ├── loop.py          # Gemini single-agent reasoning loop
│       │   ├── cost_meter.py    # Usage metadata meter & budget enforcement
│       │   ├── auth_service.py  # Cryptographic capability tickets (WAL SQLite)
│       │   ├── permissions.py   # Executable ask_on_write policy manager
│       │   └── tracer.py        # JSONL execution tracer
│       ├── audit/               # Persistent SQLite audit subsystem
│       │   ├── logger.py        # Append-only audit logger with secret redaction
│       │   └── schema.py        # Versioned SQLite audit schema
│       ├── data/                # Ingestion, validation, formula sanitization
│       │   └── loader.py        # DatasetManager, schema validation, snapshots
│       ├── mcp/                 # Model Context Protocol subsystem
│       │   ├── client.py        # Client adapter with dynamic tool discovery
│       │   └── server.py        # MCPServer exposing 8 tools over stdio
│       ├── memory/              # SQLite persistent memory subsystem
│       │   ├── manager.py       # Isolated, fingerprint-scoped episodic memory
│       │   └── schema.py        # Versioned analytical memory schema
│       ├── tools/               # 8 deterministic Python analytics tools
│       │   ├── schemas.py       # Pydantic input/output schemas
│       │   ├── implementations.py # Pure-Python arithmetic engines
│       │   └── registry.py      # Tool dispatch registry
│       └── ui/                  # Internationalization and presentation
│           └── i18n.py          # Centralized English/Arabic translations & RTL
├── tests/                       # Automated test suite (176 tests across 24 test files)
└── traces/                      # Authentic JSONL execution logs
    ├── success_1.jsonl          # Submission Item C: Successful analytical run (Gemini 3.1 Flash-Lite)
    ├── near_failure_recovery.jsonl # Submission Item C: Near-failure recovery (Gemini 3.1 Flash-Lite)
    ├── explicit_failure.jsonl   # Submission Item C: MAX_TURNS_REACHED failure (Mock LLM + Real MCP)
    └── archive/                 # Historical safety traces (e.g. permission-gated report denial)
```

---

## 🚀 Local Setup & Quickstart

### Prerequisites
- Python 3.11 or higher (Python 3.13.7 verified).
- Git installed.
- Gemini API Key from [Google AI Studio](https://aistudio.google.com/).

### 1. Clone the repository & create Virtual Environment
```powershell
# In PowerShell / Command Prompt
git clone https://github.com/f5551/RetailMind-AI.git
cd "RetailMind A"

# Create virtual environment (inherit global packages if desired)
py -3.13 -m venv --system-site-packages .venv

# Activate virtual environment
.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```powershell
# Using pip for runtime and baseline testing dependencies
pip install -r requirements.txt

# (Optional) Install code coverage audit package if running coverage verification
pip install pytest-cov
```

### 3. Configure Environment Variables
```powershell
# Copy the example file to .env
Copy-Item .env.example .env

# Edit .env and insert your real GEMINI_API_KEY
# Note: .env is git-ignored and will NEVER be committed.
```

### 4. Run Automated Test Suite
```powershell
# Run the complete test suite across all 24 test files (176 tests passing, 100% pass rate)
pytest -v tests/

# Optional: Install coverage measurement dependency if not already installed
python -m pip install pytest-cov

# Run test suite with actual code coverage (measured: 85.3% core backend, 65.0% total)
pytest --cov=src/retailmind --cov=app tests/

# Run the live Gemini + MCP multi-tool demonstration
python scripts/run_mcp_live_scenarios.py

# Run Phase 4 adversarial prompt injection attacks & trace verification
python scripts/run_phase4_scenarios.py
```

### 5. Launch the Streamlit Web Application
```powershell
# Launch the local Streamlit SaaS dashboard
streamlit run app.py
```
Open your browser to `http://localhost:8501`.

---

## ☁️ Cloud Deployment (Render & Railway)

> **Live Demo Available:** [https://retailmind-ai-skwq.onrender.com/](https://retailmind-ai-skwq.onrender.com/)  
> **Deployment Architecture:** Multi-stage production `Dockerfile` running on Render Web Service, exposing the bilingual Streamlit SaaS dashboard connected to the Gemini agent and standard MCP tools.  
> **Persistence Notice:** Render Free tier operates on ephemeral storage. While production persistent disk volume attachment is defined for `/app/data` (`RETAILMIND_DATA_DIR`), the Render free tier does not guarantee persistence across container idle sleep cycles or restarts.  
> **Operational Status:** CSV dataset upload has been verified operational on the live Render cloud deployment by end-user testing. Core reasoning, MCP tools, security defenses, and SQLite memory persistence are proven and verified locally via the automated test suite; end-to-end cloud reasoning calls remain to be verified live.

RetailMind AI is fully configured for cloud deployment on [Render](https://render.com/) and [Railway](https://railway.app/) using `Dockerfile`, `Procfile`, or `railway.json`.

1. **Volume Attachment:** Attach a Railway Volume to `/app/data` and configure `RETAILMIND_DATA_DIR=/app/data` to ensure SQLite memory and audit records persist across deployments.
2. **Environment Variables:** Configure `GEMINI_API_KEY`, `GEMINI_MODEL`, `MAX_TURNS`, `BUDGET_PER_TASK_USD`, and `PERMISSION_POLICY`.
3. **Healthcheck:** Validated on `/_stcore/health`.
4. Detailed setup instructions: see [`docs/DEPLOYMENT_GUIDE.md`](docs/DEPLOYMENT_GUIDE.md).

---

## 🔒 Security & Data Hygiene Rules

1. **No Real Secrets in Version Control**: API keys must be loaded exclusively via environment variables (`.env`).
2. **Customer Data Isolation**: Uploaded CSV files and SQLite databases containing customer records are git-ignored. Only non-confidential synthetic data in `sample_data/` is versioned.
3. **Prompt Injection Defense**: All CSV cell contents, column headers, and filenames are treated strictly as untrusted data inputs, never as execution instructions.
4. **Approval Enforcement**: Write operations (`generate_report`) are gated by executable code-level approvals and capability tickets.

---

## 📜 Capstone Progress & Roadmap

- [x] **Phase 0 — Project Control & Setup**: Repository initialized, strict hygiene configured, dependencies verified, smoke test passing (9/9).
- [x] **Phase 1 — Planning & Spec**: One-page `agent_spec.md`, 8 tool contracts, CSV data contract, test plan, and architecture design passing (6/6).
- [x] **Phase 2 — Agent Loop & Tool Calling**: Gemini iterative tool loop, 5 test inputs, JSONL traces, deterministic tools passing (16/16).
- [x] **Phase 2.1 — Final Quality & Cost Verification**: Corrected standard pricing ($0.25/$1.50), missing-cost test, termination tests, regression tests (35/35 passing).
- [x] **Phase 2.2 — Final Cost Accounting Audit**: 100% reconciled arithmetic, verified cached rates, cost tests (42/42 passing).
- [x] **Phase 3 — MCP & Persistent Memory**: Real MCP SDK v2 (`mcp==2.3.0`) stdio server & client, 8 tools routed dynamically, persistent SQLite memory surviving complete process restart, live Gemini+MCP traces (53/53 tests passing).
- [x] **Phase 4 — Safety, Approvals & Cost Metering**: 3 hostile injection tests defended, capability-based write approval tickets, append-only SQLite audit log, official submission traces (60/60 tests passing).
- [x] **Phase 5 — Streamlit UI & Cloud Deployment**: Full 5-view SaaS interface (`app.py`), live chat with Gemini+MCP, human write approval banner, Railway deployment configs, automated UI tests (67/67 tests passing).
- [x] **Phase 5.1 — Full Bilingual (Arabic/English) Toggle**: Centralized `i18n.py` dictionary, scoped RTL layout with Cairo typography, trusted language directives for Gemini, session state preservation (74/74 tests passing).
- [x] **Remediation Phase A — Critical Access Control & Validation**: Session snapshot sync across MCP subprocesses, tenant isolation, session ownership check on all 8 tools, non-finite numeric quarantine (80/80 tests passing).
- [x] **Remediation Phase B — Financial Correctness & Cost Accounting**: Distinct order counting, correct zero-base growth conventions, dynamic IQR multiplier, formula-sanitized CSV export, deterministic memory verification, exact token reconciliation (91/91 tests passing).
- [x] **Remediation Phase C — Final Quality & Acceptance**: Synthetic-only demo policy, genuine chronological near-failure recovery trace, missing i18n keys eliminated, storage path traversal defense, pre/post budget enforcement (98/98 tests passing).
- [x] **Capstone Comprehensive Audit**: Day 1–5 requirements verification, 5 submission artifacts validation, audit reports generated (`docs/CAPSTONE_COMPLETION_REPORT.md`, `docs/audit_reports/REMAINING_WORK_CHECKLIST.md`). Status: Ready With Minor Issues.

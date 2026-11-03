# RetailMind AI — Intelligent Retail Sales Analytics Agent

[![Capstone Track](https://img.shields.io/badge/LLM4Yemen-Track%20B%20Week%205-blue.svg)](docs/CAPSTONE_REQUIREMENTS.md)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Phase-Phase%202.1%20Verified-success.svg)](docs/STATUS.md)

**RetailMind AI** is an autonomous, single-agent conversational analytics system designed for CSV retail sales data analysis. Built as the Capstone project for **LLM4Yemen Track B Week 5**, it pairs Google Gemini models (`gemini-3.1-flash-lite`) with the Model Context Protocol (MCP) to provide verifiable retail data insights, statistical anomaly detection, performance rankings, and approval-gated report generation.

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
| **Test Harness** | `pytest`, `pytest-asyncio` | [PyPI: pytest](https://pypi.org/project/pytest/) | `9.2.0`, `1.4.1` |

---

## 🗂️ Repository Structure

```text
RetailMind-AI/
├── .env.example                 # Configuration template with guardrails & placeholders
├── .gitignore                   # Excludes .env, SQLite DBs, real CSV uploads, reports
├── AGENTS.md                    # Permanent Antigravity agent instructions & constraints
├── README.md                    # Project documentation, quickstart, and SDK references
├── pyproject.toml               # Modern Python package specification
├── requirements.txt             # Locked dependencies for reproducible builds
├── data/                        # Persistent SQLite database storage (git-ignored)
├── docs/                        # Governance and audit documentation
│   ├── CAPSTONE_REQUIREMENTS.md # Original immutable capstone contract
│   ├── IMPLEMENTATION_PLAN.md   # Phased execution plan & acceptance gates
│   ├── EVIDENCE_MATRIX.md       # Traceability matrix for all requirements
│   └── STATUS.md                # Real-time verified progress & journal
├── prompts/                     # Step-by-step phase prompts
│   ├── PHASE_00_START.md        # Phase 0 instructions (Project Control)
│   └── PHASE_01_PLANNING.md     # Phase 1 instructions (Planning & Spec)
├── reports/                     # Output directory for user-approved reports
├── sample_data/                 # Synthetic, non-confidential sample datasets
│   └── synthetic_sales.csv      # Sample sales dataset conforming to schema
├── src/
│   └── retailmind/              # Core application package
│       └── __init__.py          # Package initialization
├── tests/                       # Automated test suite
│   ├── __init__.py
│   └── test_smoke.py            # Phase 0 environment smoke check
└── traces/                      # Authentic JSONL execution logs (submission artifacts)
    ├── README.md                # Trace requirements documentation
    ├── success_1.jsonl          # (To be generated in Phase 2)
    ├── near_failure_recovery.jsonl # (To be generated in Phase 2)
    └── explicit_failure.jsonl   # (To be generated in Phase 4)
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
git clone <YOUR_REPO_URL>
cd "RetailMind A"

# Create virtual environment (inherit global packages if desired)
py -3.13 -m venv --system-site-packages .venv

# Activate virtual environment
.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```powershell
# Using pip
pip install -r requirements.txt
```

### 3. Configure Environment Variables
```powershell
# Copy the example file to .env
Copy-Item .env.example .env

# Edit .env and insert your real GEMINI_API_KEY
# Note: .env is git-ignored and will NEVER be committed.
```

### 4. Run Smoke Verification
```powershell
# Run the Phase 0 smoke test
pytest -v tests/test_smoke.py
```

---

## 🔒 Security & Data Hygiene Rules

1. **No Real Secrets in Version Control**: API keys must be loaded exclusively via environment variables (`.env`).
2. **Customer Data Isolation**: Uploaded CSV files and SQLite databases containing customer records are git-ignored. Only non-confidential synthetic data in `sample_data/` is versioned.
3. **Prompt Injection Defense**: All CSV cell contents, column headers, and filenames are treated strictly as untrusted data inputs, never as execution instructions.
4. **Approval Enforcement**: Write operations (`generate_report`) are gated by executable code-level approvals.

---

## 📜 Capstone Progress & Roadmap

- [x] **Phase 0 — Project Control & Setup**: Repository initialized, strict hygiene configured, dependencies verified, smoke test passing (9/9).
- [x] **Phase 1 — Planning & Spec**: One-page `agent_spec.md`, 8 tool contracts, CSV data contract, test plan, and architecture design passing (6/6).
- [x] **Phase 2 — Agent Loop & Tool Calling**: Gemini iterative tool loop, 5 test inputs, JSONL traces, deterministic tools passing (16/16).
- [x] **Phase 2.1 — Final Quality & Cost Verification**: Corrected standard pricing ($0.25/$1.50), missing-cost test, termination tests, regression tests (35/35 passing).
- [ ] **Phase 3 — MCP & Persistent Memory**: MCP server/client routing, SQLite restart persistence.
- [ ] **Phase 4 — Safety, Approvals & Cost Metering**: Hostile injection tests, write approval gating, USD cost tracking.
- [ ] **Phase 5 — Streamlit UI & Public Deployment**: Interactive UI, cloud deployment, final submission validation.

"""RetailMind AI — Configuration and Runtime Settings."""

import os
from dataclasses import dataclass
from pathlib import Path

# Inject Windows native SSL certificates to resolve Python SSL verification on Windows
try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

from dotenv import load_dotenv

# Load local .env if present
load_dotenv()

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent


@dataclass(frozen=True)
class Settings:
    """Immutable project configuration settings."""

    # Gemini LLM Settings (verified active model)
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

    # Agent Loop Guardrails
    max_turns: int = int(os.getenv("MAX_TURNS", "8"))
    budget_per_task_usd: float = float(os.getenv("BUDGET_PER_TASK_USD", "0.10"))
    permission_policy: str = os.getenv("PERMISSION_POLICY", "ask_on_write")

    # Pricing (Official Gemini API Standard paid-tier reference rates per 1M tokens)
    # Source: https://ai.google.dev/gemini-api/docs/pricing
    # Input: $0.25 / 1M, Output (including thinking): $1.50 / 1M, Cached prompt: $0.0625 / 1M
    usd_per_million_input_tokens: float = 0.25
    usd_per_million_output_tokens: float = 1.50
    usd_per_million_cached_tokens: float = 0.0625

    # Paths
    workspace_root: Path = WORKSPACE_ROOT
    reports_dir: Path = WORKSPACE_ROOT / "reports"
    traces_dir: Path = WORKSPACE_ROOT / "traces"
    sample_data_dir: Path = WORKSPACE_ROOT / "sample_data"
    sqlite_db_path: Path = WORKSPACE_ROOT / os.getenv("SQLITE_DB_PATH", "data/retailmind.db")


settings = Settings()

"""RetailMind AI — Production Streamlit Web Application.

A professional, single-agent retail analytics dashboard powered by:
- Google Gemini API (gemini-3.1-flash-lite)
- Model Context Protocol (MCP) Python SDK v2 over stdio transport
- Persistent SQLite Memory & Audit Logging
- Human-in-the-Loop write approvals (ask_on_write)
- Exact token metering and budget guardrails ($0.10 cap)
"""

import asyncio
import io
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Windows SSL certificate resolution
try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

import pandas as pd
import streamlit as st

# Configure Root Workspace
WORKSPACE_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from src.retailmind.agent.auth_service import AuthorizationService
from src.retailmind.agent.loop import AgentResult, RetailMindAgent
from src.retailmind.audit.logger import AuditLogger
from src.retailmind.config import settings
from src.retailmind.data.loader import DatasetManager, ProcessedDataset
from src.retailmind.mcp.client import RetailMindMCPClient
from src.retailmind.memory.manager import SQLiteMemoryManager

# -----------------------------------------------------------------------------
# Streamlit Page Configuration & Modern SaaS Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="RetailMind AI — Autonomous Retail Analytics",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    /* Global Styles */
    .main { background-color: #0e1117; }
    h1, h2, h3 { color: #f8fafc; font-weight: 700; }
    
    /* Metrics Card Styling */
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .metric-label { font-size: 0.85rem; color: #94a3b8; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-value { font-size: 1.8rem; color: #f8fafc; font-weight: 700; margin-top: 4px; }
    .metric-delta { font-size: 0.8rem; margin-top: 2px; }
    .delta-pos { color: #10b981; }
    .delta-neg { color: #ef4444; }

    /* Badge & Status Styles */
    .status-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-success { background-color: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid #059669; }
    .badge-info { background-color: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid #2563eb; }
    .badge-warning { background-color: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid #d97706; }
    
    /* Chat message spacing */
    .stChatMessage { margin-bottom: 12px; }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# Session State Initialization
# -----------------------------------------------------------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = f"sess_{uuid.uuid4().hex[:8]}"

if "user_id" not in st.session_state:
    st.session_state.user_id = "retail_analyst_demo"

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "pending_approval" not in st.session_state:
    st.session_state.pending_approval = None

if "dataset_loaded" not in st.session_state:
    st.session_state.dataset_loaded = False
    st.session_state.active_csv_path = None
    st.session_state.active_filename = "None"
    st.session_state.dataset_fingerprint = ""

if "last_generated_report" not in st.session_state:
    st.session_state.last_generated_report = None


# -----------------------------------------------------------------------------
# Dataset Helper Functions
# -----------------------------------------------------------------------------
def load_dataset_from_path(file_path: Path, filename: str) -> ProcessedDataset:
    processed = DatasetManager.register_dataset(st.session_id, file_path)
    st.session_state.dataset_loaded = True
    st.session_state.active_csv_path = file_path
    st.session_state.active_filename = filename
    st.session_state.dataset_fingerprint = processed.fingerprint
    return processed


def load_dataset_from_bytes(file_bytes: bytes, filename: str) -> ProcessedDataset:
    df = pd.read_csv(io.BytesIO(file_bytes))
    processed = DatasetManager.register_dataset(st.session_id, df)
    st.session_state.dataset_loaded = True
    st.session_state.active_csv_path = None
    st.session_state.active_filename = filename
    st.session_state.dataset_fingerprint = processed.fingerprint
    return processed


# -----------------------------------------------------------------------------
# Sidebar Navigation & System Controls
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🛍️ RetailMind AI")
    st.caption("Autonomous Retail Analytics Agent")

    st.markdown(
        """
        <div style='margin-bottom: 15px;'>
            <span class='status-badge badge-success'>● Gemini 3.1 Flash-Lite</span>
            <span class='status-badge badge-info'>● MCP v2 (stdio)</span>
            <span class='status-badge badge-warning'>● ask_on_write</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    nav_selection = st.radio(
        "Navigation Menu",
        [
            "📊 Overview Dashboard",
            "💬 AI Sales Agent (Gemini + MCP)",
            "📁 Dataset Ingestion & Validation",
            "🧠 Persistent Memory Explorer",
            "🛡️ Security & Audit Trail",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("#### 📁 Active Dataset")

    if st.session_state.dataset_loaded:
        st.success(f"**Loaded:** `{st.session_state.active_filename}`")
        st.caption(f"Fingerprint: `{st.session_state.dataset_fingerprint[:12]}...`")
    else:
        st.info("No dataset loaded yet.")

    sample_csv_path = WORKSPACE_ROOT / "sample_data" / "synthetic_sales.csv"
    if sample_csv_path.exists():
        if st.button("⚡ Load Synthetic Sample Data", use_container_width=True):
            with st.spinner("Ingesting sample retail dataset..."):
                load_dataset_from_path(sample_csv_path, "synthetic_sales.csv")
                st.rerun()

    st.markdown("---")
    st.markdown("#### ⚙️ Guardrails & Runtime")
    st.text(f"Session: {st.session_state.session_id}")
    st.text(f"User: {st.session_state.user_id}")
    st.text(f"Budget Cap: ${settings.budget_per_task_usd:.2f}/task")
    st.text(f"Max Turns: {settings.max_turns}")

    if st.button("🧹 Reset Conversation", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.pending_approval = None
        st.session_state.last_generated_report = None
        st.rerun()


# -----------------------------------------------------------------------------
# View 1: 📊 Overview Dashboard
# -----------------------------------------------------------------------------
if nav_selection == "📊 Overview Dashboard":
    st.title("📊 Executive Sales Overview")
    st.caption("Real-time deterministic KPIs and trend analysis computed directly from the active dataset.")

    if not st.session_state.dataset_loaded:
        st.warning("⚠️ No dataset loaded. Please upload a CSV file or load the sample dataset in the sidebar.")
    else:
        dataset = DatasetManager.get_dataset(st.session_state.session_id)
        df = dataset.valid_df

        if len(df) == 0:
            st.error("Active dataset has 0 valid rows.")
        else:
            # 1. KPI Cards
            net_revenue = float(df["line_revenue"].sum())
            total_units = float(df["quantity"].sum())
            total_orders = len(df["order_id"].dropna().unique()) if "order_id" in df.columns else len(df)
            has_cost = dataset.has_cost_data

            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.markdown(
                    f"""
                    <div class='metric-card'>
                        <div class='metric-label'>Net Revenue</div>
                        <div class='metric-value'>${net_revenue:,.2f}</div>
                        <div class='metric-delta delta-pos'>Verified Ground Truth</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col2:
                st.markdown(
                    f"""
                    <div class='metric-card'>
                        <div class='metric-label'>Units Sold</div>
                        <div class='metric-value'>{int(total_units):,}</div>
                        <div class='metric-delta delta-pos'>Total Volume</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col3:
                st.markdown(
                    f"""
                    <div class='metric-card'>
                        <div class='metric-label'>Total Orders</div>
                        <div class='metric-value'>{total_orders}</div>
                        <div class='metric-delta'>Completed Transactions</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col4:
                if has_cost:
                    net_profit = float(df["line_profit"].sum())
                    st.markdown(
                        f"""
                        <div class='metric-card'>
                            <div class='metric-label'>Gross Profit</div>
                            <div class='metric-value'>${net_profit:,.2f}</div>
                            <div class='metric-delta delta-pos'>Unit Cost Available</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        """
                        <div class='metric-card'>
                            <div class='metric-label'>Gross Profit</div>
                            <div class='metric-value' style='font-size: 1.1rem; color: #94a3b8;'>UNAVAILABLE</div>
                            <div class='metric-delta delta-neg'>No unit_cost column</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            with col5:
                if has_cost and net_revenue > 0:
                    net_profit = float(df["line_profit"].sum())
                    margin_pct = (net_profit / net_revenue) * 100.0
                    st.markdown(
                        f"""
                        <div class='metric-card'>
                            <div class='metric-label'>Gross Margin</div>
                            <div class='metric-value'>{margin_pct:.1f}%</div>
                            <div class='metric-delta delta-pos'>Profitability Ratio</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        """
                        <div class='metric-card'>
                            <div class='metric-label'>Gross Margin</div>
                            <div class='metric-value' style='font-size: 1.1rem; color: #94a3b8;'>N/A</div>
                            <div class='metric-delta delta-neg'>Requires cost data</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            st.markdown("<br>", unsafe_allow_html=True)

            # 2. Charts Row
            chart_col1, chart_col2 = st.columns(2)

            with chart_col1:
                st.subheader("📈 Revenue by Date")
                if "date" in df.columns:
                    date_df = df.groupby("date")["line_revenue"].sum().reset_index()
                    date_df = date_df.sort_values("date")
                    st.line_chart(date_df.set_index("date")["line_revenue"], use_container_width=True)

            with chart_col2:
                st.subheader("🏆 Top 5 Products by Revenue")
                if "product" in df.columns:
                    prod_df = df.groupby("product")["line_revenue"].sum().reset_index()
                    prod_df = prod_df.sort_values("line_revenue", ascending=False).head(5)
                    st.bar_chart(prod_df.set_index("product")["line_revenue"], use_container_width=True)

            chart_col3, chart_col4 = st.columns(2)
            with chart_col3:
                st.subheader("📦 Revenue by Category")
                if "category" in df.columns:
                    cat_df = df.groupby("category")["line_revenue"].sum().reset_index()
                    st.bar_chart(cat_df.set_index("category")["line_revenue"], use_container_width=True)
                else:
                    st.info("No category column present in dataset.")

            with chart_col4:
                st.subheader("🌍 Revenue by Region")
                if "region" in df.columns:
                    reg_df = df.groupby("region")["line_revenue"].sum().reset_index()
                    st.bar_chart(reg_df.set_index("region")["line_revenue"], use_container_width=True)
                else:
                    st.info("No region column present in dataset.")


# -----------------------------------------------------------------------------
# View 2: 💬 AI Sales Agent (Gemini + MCP)
# -----------------------------------------------------------------------------
elif nav_selection == "💬 AI Sales Agent (Gemini + MCP)":
    st.title("💬 RetailMind AI Conversational Agent")
    st.caption("Powered by Google Gemini 3.1 Flash-Lite, official Model Context Protocol (MCP v2), and SQLite memory.")

    if not st.session_state.dataset_loaded:
        st.warning("⚠️ Please load or upload a dataset before asking analytical questions.")

    # Quick prompt buttons
    st.markdown("**Suggested Analytical Queries:**")
    prompt_cols = st.columns(4)
    suggested_prompt = None
    if prompt_cols[0].button("📊 Net Revenue & Margin"):
        suggested_prompt = "What was our total net revenue, profit, and gross margin for the dataset?"
    if prompt_cols[1].button("🏆 Top 3 Products"):
        suggested_prompt = "Which are our top 3 products by revenue and what is their revenue share?"
    if prompt_cols[2].button("📅 Jan vs Feb Comparison"):
        suggested_prompt = "Compare sales performance between January 2026 and February 2026."
    if prompt_cols[3].button("📑 Generate Executive Report"):
        suggested_prompt = "Please generate an executive sales performance report."

    # Render Chat History
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "transparency" in msg and msg["transparency"]:
                t = msg["transparency"]
                with st.expander(f"🔍 Execution Transparency — {t.get('tool_calls_count', 0)} tool(s) | {t.get('turns_executed', 0)} turn(s) | ${t.get('total_cost_usd', 0):.6f} USD"):
                    st.markdown(f"**Execution Transport:** `{t.get('execution_transport', 'mcp')}` (stdio subprocess)")
                    st.markdown(f"**Stop Reason:** `{t.get('stop_reason')}`")
                    st.markdown(f"**Total Tokens:** `{t.get('total_tokens')}` (Paid-Tier Cost: `${t.get('total_cost_usd'):.6f}` USD)")
                    st.progress(min(1.0, t.get('total_cost_usd', 0) / settings.budget_per_task_usd))
                    st.caption(f"Budget consumed: {min(100.0, (t.get('total_cost_usd', 0) / settings.budget_per_task_usd) * 100):.1f}% of ${settings.budget_per_task_usd:.2f} limit")
                    
                    if t.get("tool_calls_history"):
                        st.markdown("**Tool Calls Audit:**")
                        for tc in t["tool_calls_history"]:
                            st.markdown(f"- Turn {tc.get('turn')}: `{tc.get('tool')}` via transport `{tc.get('transport')}` → **{tc.get('status')}**")

    # Pending Approval Banner
    if st.session_state.pending_approval:
        pending = st.session_state.pending_approval
        st.warning("⚠️ **Human Authorization Required (ask_on_write Policy)**")
        st.markdown(f"The agent requested to write an executive report titled: **{pending.get('title', 'Sales Report')}**")
        st.info("No report file has been written to disk. Please explicitly approve or deny this write operation:")

        col_app, col_deny = st.columns([1, 1])
        if col_app.button("✅ Approve & Export Report", use_container_width=True):
            with st.spinner("Authorizing and exporting report through MCP server..."):
                auth_service = AuthorizationService.get_default_service()
                ticket = auth_service.issue_ticket(
                    user_id=st.session_state.user_id,
                    session_id=st.session_state.session_id,
                    tool_name="generate_report",
                    params=pending["args"],
                )

                async def execute_approved_report():
                    client = RetailMindMCPClient()
                    async with client:
                        call_args = dict(pending["args"], auth_ticket=ticket)
                        return await client.call_tool("generate_report", call_args)

                result = asyncio.run(execute_approved_report())
                st.session_state.pending_approval = None

                if result.get("status") == "success":
                    st.success(f"Report exported successfully: `{result.get('file_path')}` ({result.get('file_size_bytes')} bytes)")
                    st.session_state.last_generated_report = result.get("file_path")
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": f"✅ **Report Exported:** `{result.get('file_path')}`\n\nThe executive sales report has been verified and saved to disk with explicit user approval.",
                    })
                else:
                    st.error(f"Report generation failed: {result.get('message')}")
                st.rerun()

        if col_deny.button("❌ Deny Write Action", use_container_width=True):
            st.session_state.pending_approval = None
            AuditLogger.get_default_logger().log_event(
                task_id=f"denial_{uuid.uuid4().hex[:6]}",
                user_id=st.session_state.user_id,
                session_id=st.session_state.session_id,
                tool_name="generate_report",
                action_type="WRITE",
                decision="DENIED",
                authorization_outcome="REJECTED_BY_USER_UI",
                execution_status="BLOCKED",
                reason_code="UI_USER_DENIED_APPROVAL",
                transport="mcp",
            )
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": "❌ **Action Denied:** The write operation `generate_report` was rejected by the user. No file was created.",
            })
            st.rerun()

    # Download Button for last generated report
    if st.session_state.last_generated_report:
        report_p = Path(st.session_state.last_generated_report)
        if report_p.exists():
            st.download_button(
                label=f"📥 Download Approved Report ({report_p.name})",
                data=report_p.read_text(encoding="utf-8"),
                file_name=report_p.name,
                mime="text/markdown",
            )

    # Chat Input Box
    user_input = st.chat_input("Ask RetailMind AI about your sales data...") or suggested_prompt
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("RetailMind AI is reasoning and invoking MCP tools..."):
                agent = RetailMindAgent(
                    model_id=settings.gemini_model,
                    execution_transport="mcp",
                )

                # Custom approval callback that flags pending UI state if generate_report is requested
                def ui_approval_callback(tool_name: str, args: Dict[str, Any]) -> bool:
                    if tool_name == "generate_report":
                        st.session_state.pending_approval = {
                            "title": args.get("title", "Executive Report"),
                            "args": args,
                        }
                        # Deny immediate autonomous execution to show UI approval prompt
                        return False
                    return True

                result: AgentResult = agent.run_task(
                    user_query=user_input,
                    session_id=st.session_state.session_id,
                    user_id=st.session_state.user_id,
                    csv_path=st.session_state.active_csv_path,
                    approval_callback=ui_approval_callback,
                )

                st.markdown(result.final_answer)

                transparency_data = {
                    "tool_calls_count": result.tool_calls_count,
                    "turns_executed": result.turns_executed,
                    "stop_reason": result.stop_reason,
                    "total_tokens": result.total_tokens,
                    "total_cost_usd": result.total_cost_usd,
                    "execution_transport": result.execution_transport,
                    "tool_calls_history": result.tool_calls_history,
                }

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": result.final_answer,
                    "transparency": transparency_data,
                })
                st.rerun()


# -----------------------------------------------------------------------------
# View 3: 📁 Dataset Ingestion & Validation
# -----------------------------------------------------------------------------
elif nav_selection == "📁 Dataset Ingestion & Validation":
    st.title("📁 CSV Ingestion & Data Quality Audit")
    st.caption("Upload sales data with automated formula sanitization, schema audit, and row quarantining.")

    uploaded_file = st.file_uploader(
        "Upload Retail CSV File (Max 10MB, Max 50,000 rows)",
        type=["csv"],
        help="Required columns: date, product, quantity, unit_price. Optional: unit_cost, category, region, order_id.",
    )

    if uploaded_file is not None:
        if uploaded_file.size > 10 * 1024 * 1024:
            st.error("File size exceeds 10MB limit.")
        else:
            bytes_data = uploaded_file.getvalue()
            with st.spinner("Validating and parsing CSV..."):
                try:
                    processed = load_dataset_from_bytes(bytes_data, uploaded_file.name)
                    st.success(f"Successfully processed `{uploaded_file.name}`!")
                except Exception as exc:
                    st.error(f"Error parsing dataset: {exc}")

    if st.session_state.dataset_loaded:
        dataset = DatasetManager.get_dataset(st.session_state.session_id)
        
        st.subheader("📋 Dataset Audit Summary")
        aud_col1, aud_col2, aud_col3, aud_col4 = st.columns(4)
        aud_col1.metric("Total Rows Ingested", len(dataset.raw_df))
        aud_col2.metric("Valid Rows", len(dataset.valid_df))
        aud_col3.metric("Quarantined Rows", len(dataset.quarantined_df))
        aud_col4.metric("Duplicates Detected", dataset.duplicate_rows_count)

        if not dataset.has_cost_data:
            st.warning("⚠️ **Notice:** This dataset lacks a `unit_cost` column. Net revenue and units sold will compute normally, but gross profit and margins will be marked UNAVAILABLE.")
        else:
            st.success("✅ **Cost Data Detected:** Unit cost information is available for profit and gross margin analysis.")

        st.subheader("🔍 Valid Data Preview")
        st.dataframe(dataset.valid_df.head(20), use_container_width=True)

        if len(dataset.quarantined_df) > 0:
            st.subheader("⚠️ Quarantined Invalid Rows")
            st.dataframe(dataset.quarantined_df, use_container_width=True)


# -----------------------------------------------------------------------------
# View 4: 🧠 Persistent Memory Explorer
# -----------------------------------------------------------------------------
elif nav_selection == "🧠 Persistent Memory Explorer":
    st.title("🧠 Persistent SQLite Analytical Memory")
    st.caption("Inspect verified analytical findings stored persistently in SQLite. Memories survive process restarts and are isolated by user and dataset fingerprint.")

    mem_manager = SQLiteMemoryManager()
    if not st.session_state.dataset_fingerprint:
        st.info("Please load a dataset to view associated memories.")
    else:
        records = mem_manager.retrieve_relevant_context(
            user_id=st.session_state.user_id,
            dataset_fingerprint=st.session_state.dataset_fingerprint,
            limit=10,
        )

        st.markdown(f"**Active User ID:** `{st.session_state.user_id}`")
        st.markdown(f"**Dataset SHA-256 Fingerprint:** `{st.session_state.dataset_fingerprint}`")
        st.markdown(f"**Verified Memories Found:** `{len(records)}`")

        if not records:
            st.info("No prior memories recorded for this specific dataset. Ask the AI agent queries to generate verified findings!")
        else:
            for idx, r in enumerate(records, 1):
                with st.expander(f"Memory #{idx}: {r.get('query')} ({r.get('created_at')})", expanded=(idx == 1)):
                    st.markdown(f"**Task ID:** `{r.get('task_id')}`")
                    st.markdown(f"**Verified Summary:**\n{r.get('summary')}")
                    if r.get("tool_calls"):
                        st.json(r.get("tool_calls"))


# -----------------------------------------------------------------------------
# View 5: 🛡️ Security & Audit Trail
# -----------------------------------------------------------------------------
elif nav_selection == "🛡️ Security & Audit Trail":
    st.title("🛡️ Security Audit Log")
    st.caption("Immutable append-only audit trail recorded in SQLite (WAL mode). Logs all tool executions, permission gates, and adversarial attack blocks.")

    audit_logger = AuditLogger.get_default_logger()
    events = audit_logger.query_events(limit=50)

    st.markdown(f"**Database Location:** `{audit_logger.db_path}`")
    st.markdown(f"**Recent Logged Events:** `{len(events)}`")

    if not events:
        st.info("No audit events recorded yet.")
    else:
        # Format table for display
        display_data = []
        for e in events:
            display_data.append({
                "Timestamp (UTC)": e["timestamp"],
                "Tool": e["tool_name"],
                "Action": e["action_type"],
                "Decision": e["decision"],
                "Outcome": e["authorization_outcome"],
                "Reason Code": e["reason_code"],
                "Transport": e["transport"],
                "Task ID": e["task_id"],
            })
        st.dataframe(pd.DataFrame(display_data), use_container_width=True)

"""RetailMind AI — Production Streamlit Web Application (Bilingual Arabic/English).

A professional, single-agent retail analytics dashboard powered by:
- Google Gemini API (gemini-3.1-flash-lite)
- Model Context Protocol (MCP) Python SDK v2 over stdio transport
- Persistent SQLite Memory & Audit Logging
- Human-in-the-Loop write approvals (ask_on_write)
- Exact token metering and budget guardrails ($0.10 cap)
- Full Arabic (RTL) & English (LTR) language switching with complete translations
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
from src.retailmind.ui.i18n import get_layout_css, t

# -----------------------------------------------------------------------------
# Streamlit Page Configuration & Modern SaaS Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="RetailMind AI — Autonomous Retail Analytics",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Session State Initialization
# -----------------------------------------------------------------------------
if "language" not in st.session_state:
    st.session_state.language = "en"

if "current_view_key" not in st.session_state:
    st.session_state.current_view_key = "overview"

if "session_id" not in st.session_state:
    st.session_state.session_id = f"sess_{uuid.uuid4().hex[:8]}"

if "user_id" not in st.session_state:
    st.session_state.user_id = f"user_{uuid.uuid4().hex[:12]}"

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

lang = st.session_state.language

# Inject Base Styling and Scoped Bilingual RTL/LTR Styles
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

    /* Top Language Switcher Container */
    .top-lang-container {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        padding: 4px 0 12px 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown(get_layout_css(lang), unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Top Header Language Switcher
# -----------------------------------------------------------------------------
header_col1, header_col2 = st.columns([5, 1.5])
with header_col2:
    def on_language_toggle():
        chosen = st.session_state.lang_radio_choice
        st.session_state.language = "ar" if chosen == "العربية" else "en"

    st.radio(
        label=t("lang_toggle_label", lang),
        options=["English", "العربية"],
        index=0 if lang == "en" else 1,
        horizontal=True,
        key="lang_radio_choice",
        on_change=on_language_toggle,
        label_visibility="collapsed",
    )


# -----------------------------------------------------------------------------
# Dataset Helper Functions
# -----------------------------------------------------------------------------
def load_dataset_from_path(file_path: Path, filename: str) -> ProcessedDataset:
    processed = DatasetManager.register_dataset(
        st.session_state.session_id, file_path, user_id=st.session_state.user_id
    )
    st.session_state.dataset_loaded = True
    st.session_state.active_csv_path = processed.snapshot_path
    st.session_state.active_filename = filename
    st.session_state.dataset_fingerprint = processed.fingerprint
    return processed


def load_dataset_from_bytes(file_bytes: bytes, filename: str) -> ProcessedDataset:
    df = pd.read_csv(io.BytesIO(file_bytes))
    processed = DatasetManager.register_dataset(
        st.session_state.session_id, df, user_id=st.session_state.user_id
    )
    st.session_state.dataset_loaded = True
    st.session_state.active_csv_path = processed.snapshot_path
    st.session_state.active_filename = filename
    st.session_state.dataset_fingerprint = processed.fingerprint
    return processed


# -----------------------------------------------------------------------------
# Sidebar Navigation & System Controls
# -----------------------------------------------------------------------------
view_keys = ["overview", "agent", "dataset", "memory", "audit"]
nav_display_names = [
    t("nav_overview", lang),
    t("nav_agent", lang),
    t("nav_dataset", lang),
    t("nav_memory", lang),
    t("nav_audit", lang),
]

with st.sidebar:
    st.markdown(f"### 🛍️ {t('app_title', lang)}")
    st.caption(t("app_caption", lang))

    st.markdown(
        f"""
        <div style='margin-bottom: 15px;'>
            <span class='status-badge badge-success'>{t('status_model', lang)}</span>
            <span class='status-badge badge-info'>{t('status_mcp', lang)}</span>
            <span class='status-badge badge-warning'>{t('status_policy', lang)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cur_view = st.session_state.get("current_view_key", "overview")
    default_idx = view_keys.index(cur_view) if cur_view in view_keys else 0

    def on_nav_change():
        selected = st.session_state.nav_radio_widget
        idx = nav_display_names.index(selected)
        st.session_state.current_view_key = view_keys[idx]

    selected_nav_label = st.radio(
        t("nav_menu", lang) if "nav_menu" in t("nav_menu", lang) else "Menu",
        nav_display_names,
        index=default_idx,
        label_visibility="collapsed",
        key="nav_radio_widget",
        on_change=on_nav_change,
    )

    active_view = view_keys[nav_display_names.index(selected_nav_label)]
    st.session_state.current_view_key = active_view

    st.markdown("---")
    st.markdown(f"#### {t('active_dataset_header', lang)}")

    if st.session_state.dataset_loaded:
        st.success(t("dataset_loaded_label", lang, filename=st.session_state.active_filename))
        st.caption(t("fingerprint_label", lang, fp=st.session_state.dataset_fingerprint[:12]))
    else:
        st.info(t("no_dataset_loaded", lang))

    sample_csv_path = WORKSPACE_ROOT / "sample_data" / "synthetic_sales.csv"
    if sample_csv_path.exists():
        if st.button(t("btn_load_sample", lang), use_container_width=True):
            with st.spinner(t("spinner_load_sample", lang)):
                load_dataset_from_path(sample_csv_path, "synthetic_sales.csv")
                st.rerun()

    st.markdown("---")
    st.markdown(f"#### {t('guardrails_header', lang)}")
    st.text(t("lbl_session", lang, session=st.session_state.session_id))
    st.text(t("lbl_user", lang, user=st.session_state.user_id))
    st.text(t("lbl_budget_cap", lang, cap=settings.budget_per_task_usd))
    st.text(t("lbl_max_turns", lang, turns=settings.max_turns))

    if st.button(t("btn_reset_chat", lang), use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.pending_approval = None
        st.session_state.last_generated_report = None
        st.rerun()


# -----------------------------------------------------------------------------
# View 1: 📊 Overview Dashboard
# -----------------------------------------------------------------------------
if active_view == "overview":
    st.title(t("overview_title", lang))
    st.caption(t("overview_caption", lang))

    if not st.session_state.dataset_loaded:
        st.warning(t("warn_no_dataset", lang))
    else:
        dataset = DatasetManager.get_dataset(st.session_state.session_id)
        df = dataset.valid_df

        if len(df) == 0:
            st.error(t("err_zero_rows", lang))
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
                        <div class='metric-label'>{t('kpi_net_revenue', lang)}</div>
                        <div class='metric-value'>${net_revenue:,.2f}</div>
                        <div class='metric-delta delta-pos'>{t('kpi_revenue_delta', lang)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col2:
                st.markdown(
                    f"""
                    <div class='metric-card'>
                        <div class='metric-label'>{t('kpi_units_sold', lang)}</div>
                        <div class='metric-value'>{int(total_units):,}</div>
                        <div class='metric-delta delta-pos'>{t('kpi_units_delta', lang)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col3:
                st.markdown(
                    f"""
                    <div class='metric-card'>
                        <div class='metric-label'>{t('kpi_total_orders', lang)}</div>
                        <div class='metric-value'>{total_orders}</div>
                        <div class='metric-delta'>{t('kpi_orders_delta', lang)}</div>
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
                            <div class='metric-label'>{t('kpi_gross_profit', lang)}</div>
                            <div class='metric-value'>${net_profit:,.2f}</div>
                            <div class='metric-delta delta-pos'>{t('kpi_profit_delta_avail', lang)}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"""
                        <div class='metric-card'>
                            <div class='metric-label'>{t('kpi_gross_profit', lang)}</div>
                            <div class='metric-value' style='font-size: 1.1rem; color: #94a3b8;'>{t('kpi_profit_unavail', lang)}</div>
                            <div class='metric-delta delta-neg'>{t('kpi_profit_delta_unavail', lang)}</div>
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
                            <div class='metric-label'>{t('kpi_gross_margin', lang)}</div>
                            <div class='metric-value'>{margin_pct:.1f}%</div>
                            <div class='metric-delta delta-pos'>{t('kpi_margin_delta_avail', lang)}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"""
                        <div class='metric-card'>
                            <div class='metric-label'>{t('kpi_gross_margin', lang)}</div>
                            <div class='metric-value' style='font-size: 1.1rem; color: #94a3b8;'>{t('kpi_margin_na', lang)}</div>
                            <div class='metric-delta delta-neg'>{t('kpi_margin_delta_na', lang)}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            st.markdown("<br>", unsafe_allow_html=True)

            # 2. Charts Row
            chart_col1, chart_col2 = st.columns(2)

            with chart_col1:
                st.subheader(t("chart_revenue_by_date", lang))
                if "date" in df.columns:
                    date_df = df.groupby("date")["line_revenue"].sum().reset_index()
                    date_df = date_df.sort_values("date")
                    st.line_chart(date_df.set_index("date")["line_revenue"], use_container_width=True)

            with chart_col2:
                st.subheader(t("chart_top_products", lang))
                if "product" in df.columns:
                    prod_df = df.groupby("product")["line_revenue"].sum().reset_index()
                    prod_df = prod_df.sort_values("line_revenue", ascending=False).head(5)
                    st.bar_chart(prod_df.set_index("product")["line_revenue"], use_container_width=True)

            chart_col3, chart_col4 = st.columns(2)
            with chart_col3:
                st.subheader(t("chart_revenue_by_category", lang))
                if "category" in df.columns:
                    cat_df = df.groupby("category")["line_revenue"].sum().reset_index()
                    st.bar_chart(cat_df.set_index("category")["line_revenue"], use_container_width=True)
                else:
                    st.info(t("info_no_category", lang))

            with chart_col4:
                st.subheader(t("chart_revenue_by_region", lang))
                if "region" in df.columns:
                    reg_df = df.groupby("region")["line_revenue"].sum().reset_index()
                    st.bar_chart(reg_df.set_index("region")["line_revenue"], use_container_width=True)
                else:
                    st.info(t("info_no_region", lang))


# -----------------------------------------------------------------------------
# View 2: 💬 AI Sales Agent (Gemini + MCP)
# -----------------------------------------------------------------------------
elif active_view == "agent":
    st.title(t("agent_title", lang))
    st.caption(t("agent_caption", lang))

    if not st.session_state.dataset_loaded:
        st.warning(t("warn_agent_no_dataset", lang))

    # Quick prompt buttons
    st.markdown(t("suggested_queries_label", lang))
    prompt_cols = st.columns(4)
    suggested_prompt = None
    if prompt_cols[0].button(t("btn_prompt_revenue", lang), use_container_width=True):
        suggested_prompt = t("query_revenue", lang)
    if prompt_cols[1].button(t("btn_prompt_top_prods", lang), use_container_width=True):
        suggested_prompt = t("query_top_prods", lang)
    if prompt_cols[2].button(t("btn_prompt_compare", lang), use_container_width=True):
        suggested_prompt = t("query_compare", lang)
    if prompt_cols[3].button(t("btn_prompt_report", lang), use_container_width=True):
        suggested_prompt = t("query_report", lang)

    # Render Chat History
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "transparency" in msg and msg["transparency"]:
                t_data = msg["transparency"]
                header_text = t(
                    "transparency_header",
                    lang,
                    tools=t_data.get("tool_calls_count", 0),
                    turns=t_data.get("turns_executed", 0),
                    cost=t_data.get("total_cost_usd", 0.0),
                )
                with st.expander(header_text):
                    st.markdown(t("lbl_transport", lang, transport=t_data.get("execution_transport", "mcp")))
                    st.markdown(t("lbl_stop_reason", lang, reason=t_data.get("stop_reason")))
                    st.markdown(
                        t(
                            "lbl_tokens_cost",
                            lang,
                            tokens=t_data.get("total_tokens"),
                            cost=t_data.get("total_cost_usd", 0.0),
                        )
                    )
                    st.progress(min(1.0, t_data.get("total_cost_usd", 0.0) / settings.budget_per_task_usd))
                    pct = min(100.0, (t_data.get("total_cost_usd", 0.0) / settings.budget_per_task_usd) * 100)
                    st.caption(t("caption_budget_pct", lang, pct=pct, cap=settings.budget_per_task_usd))

                    if t_data.get("tool_calls_history"):
                        st.markdown(t("tool_audit_title", lang))
                        for tc in t_data["tool_calls_history"]:
                            st.markdown(
                                t(
                                    "tool_audit_line",
                                    lang,
                                    turn=tc.get("turn"),
                                    tool=tc.get("tool"),
                                    transport=tc.get("transport"),
                                    status=tc.get("status"),
                                )
                            )

    # Pending Approval Banner
    if st.session_state.pending_approval:
        pending = st.session_state.pending_approval
        st.warning(t("approval_req_title", lang))
        st.markdown(t("approval_req_desc", lang, title=pending.get("title", "Sales Report")))
        st.info(t("approval_req_info", lang))

        col_app, col_deny = st.columns([1, 1])
        if col_app.button(t("btn_approve_report", lang), use_container_width=True):
            with st.spinner(t("spinner_authorizing_report", lang)):
                auth_service = AuthorizationService.get_default_service()
                ticket = auth_service.issue_ticket(
                    user_id=st.session_state.user_id,
                    session_id=st.session_state.session_id,
                    tool_name="generate_report",
                    params=pending["args"],
                )

                async def execute_approved_report():
                    client = RetailMindMCPClient(caller_user_id=st.session_state.user_id)
                    async with client:
                        call_args = dict(pending["args"], auth_ticket=ticket)
                        return await client.call_tool("generate_report", call_args)

                result = asyncio.run(execute_approved_report())
                st.session_state.pending_approval = None

                if result.get("status") == "success":
                    st.success(
                        t(
                            "msg_report_success",
                            lang,
                            path=result.get("file_path"),
                            size=result.get("file_size_bytes"),
                        )
                    )
                    st.session_state.last_generated_report = result.get("file_path")
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": t("chat_report_approved_content", lang, path=result.get("file_path")),
                    })
                else:
                    st.error(t("msg_report_failed", lang, error=result.get("message")))
                st.rerun()

        if col_deny.button(t("btn_deny_report", lang), use_container_width=True):
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
                "content": t("chat_report_denied_content", lang),
            })
            st.rerun()

    # Download Button for last generated report
    if st.session_state.last_generated_report:
        report_p = Path(st.session_state.last_generated_report)
        if report_p.exists():
            mime_type = "text/csv" if report_p.suffix.lower() == ".csv" else "text/markdown"
            st.download_button(
                label=t("btn_download_report", lang, filename=report_p.name),
                data=report_p.read_text(encoding="utf-8"),
                file_name=report_p.name,
                mime=mime_type,
            )

    # Chat Input Box
    user_input = st.chat_input(t("chat_input_prompt", lang)) or suggested_prompt
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner(t("spinner_agent_thinking", lang)):
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
                    language=lang,
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
elif active_view == "dataset":
    st.title(t("ingestion_title", lang))
    st.caption(t("ingestion_caption", lang))

    uploaded_file = st.file_uploader(
        t("uploader_label", lang),
        type=["csv"],
        help=t("uploader_help", lang),
    )

    if uploaded_file is not None:
        if uploaded_file.size > 10 * 1024 * 1024:
            st.error(t("err_file_size", lang))
        else:
            bytes_data = uploaded_file.getvalue()
            with st.spinner(t("spinner_validating_csv", lang)):
                try:
                    processed = load_dataset_from_bytes(bytes_data, uploaded_file.name)
                    st.success(t("msg_csv_success", lang, name=uploaded_file.name))
                except Exception as exc:
                    st.error(t("err_csv_parse", lang, error=exc))

    if st.session_state.dataset_loaded:
        dataset = DatasetManager.get_dataset(st.session_state.session_id)

        st.subheader(t("audit_summary_title", lang))
        aud_col1, aud_col2, aud_col3, aud_col4 = st.columns(4)
        aud_col1.metric(t("metric_total_rows", lang), len(dataset.raw_df))
        aud_col2.metric(t("metric_valid_rows", lang), len(dataset.valid_df))
        aud_col3.metric(t("metric_quarantined_rows", lang), len(dataset.quarantined_df))
        aud_col4.metric(t("metric_duplicates", lang), dataset.duplicate_rows_count)

        if not dataset.has_cost_data:
            st.warning(t("warn_no_cost_column", lang))
        else:
            st.success(t("success_has_cost_column", lang))

        st.subheader(t("preview_valid_data", lang))
        st.dataframe(dataset.valid_df.head(20), use_container_width=True)

        if len(dataset.quarantined_df) > 0:
            st.subheader(t("preview_quarantined_data", lang))
            st.dataframe(dataset.quarantined_df, use_container_width=True)


# -----------------------------------------------------------------------------
# View 4: 🧠 Persistent Memory Explorer
# -----------------------------------------------------------------------------
elif active_view == "memory":
    st.title(t("memory_title", lang))
    st.caption(t("memory_caption", lang))

    mem_manager = SQLiteMemoryManager()
    if not st.session_state.dataset_fingerprint:
        st.info(t("info_memory_no_dataset", lang))
    else:
        records = mem_manager.retrieve_relevant_context(
            user_id=st.session_state.user_id,
            dataset_fingerprint=st.session_state.dataset_fingerprint,
            limit=10,
        )

        st.markdown(t("lbl_active_user", lang, user_id=st.session_state.user_id))
        st.markdown(t("lbl_dataset_fingerprint", lang, fingerprint=st.session_state.dataset_fingerprint))
        st.markdown(t("lbl_memories_found", lang, count=len(records)))

        if not records:
            st.info(t("info_no_memories", lang))
        else:
            for idx, r in enumerate(records, 1):
                header = t("memory_item_expander", lang, idx=idx, query=r.get("query"), date=r.get("created_at"))
                with st.expander(header, expanded=(idx == 1)):
                    st.markdown(t("lbl_task_id", lang, task_id=r.get("task_id")))
                    st.markdown(t("lbl_verified_summary", lang, summary=r.get("summary")))
                    if r.get("tool_calls"):
                        st.json(r.get("tool_calls"))


# -----------------------------------------------------------------------------
# View 5: 🛡️ Security & Audit Trail
# -----------------------------------------------------------------------------
elif active_view == "audit":
    st.title(t("audit_title", lang))
    st.caption(t("audit_caption", lang))

    audit_logger = AuditLogger.get_default_logger()
    events = audit_logger.query_events(user_id=st.session_state.user_id, limit=50)

    st.markdown(t("lbl_db_location", lang, path=audit_logger.db_path))
    st.markdown(t("lbl_recent_events", lang, count=len(events)))

    if not events:
        st.info(t("info_no_events", lang))
    else:
        display_data = []
        for e in events:
            display_data.append({
                t("col_timestamp", lang): e["timestamp"],
                t("col_tool", lang): e["tool_name"],
                t("col_action", lang): e["action_type"],
                t("col_decision", lang): e["decision"],
                t("col_outcome", lang): e["authorization_outcome"],
                t("col_reason", lang): e["reason_code"],
                t("col_transport", lang): e["transport"],
                t("col_task_id", lang): e["task_id"],
            })
        st.dataframe(pd.DataFrame(display_data), use_container_width=True)

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
import hmac
import io
import os
import re
import sys
import textwrap
import uuid
from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional

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
from src.retailmind.data.loader import (
    DatasetManager,
    ProcessedDataset,
    RowLimitExceededError,
    is_local_interface_bound,
)
from src.retailmind.mcp.client import RetailMindMCPClient
from src.retailmind.memory.manager import SQLiteMemoryManager
from src.retailmind.tools.implementations import count_distinct_orders
from src.retailmind.ui.i18n import get_layout_css, t
from src.retailmind.ui.icons import get_svg_icon

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
if "lang" in st.query_params and st.query_params["lang"] in ["ar", "en"]:
    st.session_state.language = st.query_params["lang"]
elif "language" not in st.session_state:
    st.session_state.language = "ar"

MERCHANT_VIEWS = ["overview", "agent", "dataset", "memory"]
DEVELOPER_VIEWS = ["audit"]
ALL_VIEWS = MERCHANT_VIEWS + DEVELOPER_VIEWS

if "current_view_key" not in st.session_state:
    if "view" in st.query_params and st.query_params["view"] in ALL_VIEWS:
        st.session_state.current_view_key = st.query_params["view"]
    else:
        st.session_state.current_view_key = "overview"

if "session_id" not in st.session_state:
    st.session_state.session_id = f"sess_{uuid.uuid4().hex[:8]}"

if "user_id" not in st.session_state:
    st.session_state.user_id = f"user_{uuid.uuid4().hex[:12]}"

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "pending_approval" not in st.session_state:
    st.session_state.pending_approval = None

if "local_dev_token" not in st.session_state:
    st.session_state.local_dev_token = None

# Level 2 Security: Strip unauthorized or sensitive query parameters immediately (strict whitelist)
ALLOWED_QUERY_PARAMS = {"lang", "view", "load_sample", "revoke_dev"}
for param_key in list(st.query_params.keys()):
    if param_key not in ALLOWED_QUERY_PARAMS:
        try:
            del st.query_params[param_key]
        except Exception:
            pass

if is_local_interface_bound():
    if st.query_params.get("revoke_dev") == "1":
        st.session_state.local_dev_token = None
        try:
            del st.query_params["revoke_dev"]
        except Exception:
            pass


def check_developer_authorization() -> bool:
    """Secure server-side check for developer authorization.
    
    Level 2 Isolation Rules:
    1. Loopback binding only (fails closed on public interfaces).
    2. Compares session-bound local_dev_token against RETAILMIND_LOCAL_DEV_SECRET using hmac.compare_digest.
    3. Global server environment tokens do not grant ambient developer privileges to UI sessions.
    4. URL tokens are strictly rejected and stripped to prevent credential leaks.
    """
    if not is_local_interface_bound():
        return False
    configured_secret = os.getenv("RETAILMIND_LOCAL_DEV_SECRET")
    if not configured_secret:
        return False
    current_token = st.session_state.get("local_dev_token")
    if not current_token or not isinstance(current_token, str):
        return False
    return hmac.compare_digest(current_token, configured_secret)

if "dataset_loaded" not in st.session_state:
    st.session_state.dataset_loaded = False
    st.session_state.active_csv_path = None
    st.session_state.active_filename = "None"
    st.session_state.dataset_fingerprint = ""

if "last_generated_report" not in st.session_state:
    st.session_state.last_generated_report = None

lang = st.session_state.language


def render_trusted_html(html_str: str) -> None:
    """Render trusted, application-authored HTML safely without CommonMark indentation bugs."""
    # Strip any leading whitespace from every line so CommonMark never treats 4+ spaces as indented code blocks!
    clean_html = re.sub(r"^[ \t]+", "", textwrap.dedent(html_str).strip(), flags=re.MULTILINE)
    st.markdown(clean_html, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Inject Scoped Bilingual RTL/LTR SaaS Styling (Single Source of Truth)
# -----------------------------------------------------------------------------
render_trusted_html(get_layout_css(lang))

CATEGORY_MAP_AR = {
    "Electronics": "الإلكترونيات",
    "Accessories": "الإكسسوارات",
    "Fashion": "الأزياء",
    "Clothing": "الأزياء",
    "Home & Kitchen": "المنزل والمطبخ",
    "Beauty & Personal Care": "الجمال والعناية",
    "Sports & Outdoors": "الرياضة والأنشطة",
}


def format_dataset_date_span(df: pd.DataFrame, lang: str) -> str:
    """Formats the active date span cleanly based on actual dataframe timestamps."""
    if "date" not in df.columns:
        return t("ref_date_range_label", lang)
    try:
        dts = pd.to_datetime(df["date"], errors="coerce").dropna()
        if dts.empty:
            return t("ref_date_range_label", lang)
        min_d = dts.min()
        max_d = dts.max()
        if lang == "ar":
            arabic_months = [
                "", "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
                "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"
            ]
            if min_d.year == max_d.year:
                if min_d.month == max_d.month:
                    return f"{min_d.day} - {max_d.day} {arabic_months[min_d.month]} {min_d.year}"
                return f"{min_d.day} {arabic_months[min_d.month]} - {max_d.day} {arabic_months[max_d.month]} {min_d.year}"
            return f"{min_d.day} {arabic_months[min_d.month]} {min_d.year} - {max_d.day} {arabic_months[max_d.month]} {max_d.year}"
        else:
            if min_d.year == max_d.year:
                if min_d.month == max_d.month:
                    return f"{min_d.strftime('%b %d')} - {max_d.strftime('%d, %Y')}"
                return f"{min_d.strftime('%b %d')} - {max_d.strftime('%b %d, %Y')}"
            return f"{min_d.strftime('%b %d, %Y')} - {max_d.strftime('%b %d, %Y')}"
    except Exception:
        return t("ref_date_range_label", lang)


def format_current_date(lang: str) -> str:
    """Formats today's date dynamically in Arabic or English."""
    today = date.today()
    if lang == "ar":
        arabic_days = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
        arabic_months = [
            "", "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
            "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"
        ]
        day_name = arabic_days[today.weekday()]
        month_name = arabic_months[today.month]
        return f"{day_name}، {today.day} {month_name} {today.year}"
    else:
        return today.strftime("%A, %d %B %Y")


def compute_period_metrics(df: pd.DataFrame, has_cost: bool) -> dict:
    """Computes exact mathematical ground-truth KPIs and period-over-period deltas."""
    net_revenue = float(df["line_revenue"].sum()) if "line_revenue" in df.columns else 0.0
    total_units = int(df["quantity"].sum()) if "quantity" in df.columns else 0
    total_orders = count_distinct_orders(df)

    net_profit = float(df["line_profit"].sum()) if (has_cost and "line_profit" in df.columns) else None
    margin_pct = (net_profit / net_revenue * 100.0) if (net_profit is not None and net_revenue > 0) else None
    total_cost = float((df["quantity"] * df["unit_cost"]).sum()) if (has_cost and "unit_cost" in df.columns and "quantity" in df.columns) else None

    deltas = {
        "revenue_pct": None,
        "profit_pct": None,
        "margin_diff": None,
        "orders_pct": None,
        "units_pct": None,
        "has_comparison": False,
        "periods": [],
    }

    if "date" in df.columns:
        try:
            temp_df = df.copy()
            temp_df["_dt"] = pd.to_datetime(temp_df["date"], errors="coerce")
            temp_df = temp_df.dropna(subset=["_dt"])
            temp_df["_period"] = temp_df["_dt"].dt.to_period("M")
            periods = sorted(temp_df["_period"].unique())
            deltas["periods"] = [str(p) for p in periods]

            if len(periods) >= 2:
                p_prev = periods[-2]
                p_curr = periods[-1]
                df_prev = temp_df[temp_df["_period"] == p_prev]
                df_curr = temp_df[temp_df["_period"] == p_curr]

                rev_prev = float(df_prev["line_revenue"].sum())
                rev_curr = float(df_curr["line_revenue"].sum())
                if rev_prev > 0:
                    deltas["revenue_pct"] = ((rev_curr - rev_prev) / rev_prev) * 100.0

                if has_cost and "line_profit" in df.columns:
                    prof_prev = float(df_prev["line_profit"].sum())
                    prof_curr = float(df_curr["line_profit"].sum())
                    if prof_prev > 0:
                        deltas["profit_pct"] = ((prof_curr - prof_prev) / prof_prev) * 100.0

                    if rev_prev > 0 and rev_curr > 0:
                        marg_prev = (prof_prev / rev_prev) * 100.0
                        marg_curr = (prof_curr / rev_curr) * 100.0
                        deltas["margin_diff"] = marg_curr - marg_prev

                orders_prev = count_distinct_orders(df_prev)
                orders_curr = count_distinct_orders(df_curr)
                if orders_prev > 0:
                    deltas["orders_pct"] = ((orders_curr - orders_prev) / orders_prev) * 100.0

                units_prev = float(df_prev["quantity"].sum())
                units_curr = float(df_curr["quantity"].sum())
                if units_prev > 0:
                    deltas["units_pct"] = ((units_curr - units_prev) / units_prev) * 100.0

                deltas["has_comparison"] = True
        except Exception:
            pass

    return {
        "net_revenue": net_revenue,
        "total_units": total_units,
        "total_orders": total_orders,
        "net_profit": net_profit,
        "margin_pct": margin_pct,
        "total_cost": total_cost,
        "deltas": deltas,
    }


def render_dynamic_execution_stepper(t_data: dict, lang: str) -> str:
    """Builds a genuine execution stepper based strictly on real tool calls that executed.
    
    If no tool calls occurred, returns empty string.
    """
    history = t_data.get("tool_calls_history", [])
    if not history:
        return ""

    tool_label_map = {
        "summarize_sales": {
            "title": {"en": "Sales Analysis", "ar": "تحليل المبيعات"},
            "sub": {"en": "Sales metrics computed", "ar": "تم تحليل أداء المبيعات حسب المعايير"},
        },
        "rank_products": {
            "title": {"en": "Product Ranking", "ar": "تصنيف المنتجات"},
            "sub": {"en": "Top products evaluated", "ar": "تم ترتيب المنتجات الأعلى أداءً"},
        },
        "compare_periods": {
            "title": {"en": "Cost & Period Comparison", "ar": "مقارنة التكاليف"},
            "sub": {"en": "Costs compared to previous period", "ar": "تمت مقارنة التكاليف مع الفترات السابقة"},
        },
        "detect_anomalies": {
            "title": {"en": "Anomaly Detection", "ar": "كشف الشذوذ"},
            "sub": {"en": "Statistical outliers checked", "ar": "تم فحص المعاملات الشاذة إحصائياً"},
        },
        "segment_sales": {
            "title": {"en": "Sales Segmentation", "ar": "تجزئة المبيعات"},
            "sub": {"en": "Dimensional breakdown evaluated", "ar": "تم تفكيك المبيعات حسب الأبعاد"},
        },
        "inspect_dataset": {
            "title": {"en": "Dataset Inspection", "ar": "فحص البيانات"},
            "sub": {"en": "Schema and columns verified", "ar": "تم التحقق من أعمدة وهيكل البيانات"},
        },
        "validate_dataset": {
            "title": {"en": "Dataset Validation", "ar": "تدقيق البيانات"},
            "sub": {"en": "Quality integrity passed", "ar": "تم تدقيق الجودة والأرقام"},
        },
        "generate_report": {
            "title": {"en": "Report Generation", "ar": "إنشاء التقرير"},
            "sub": {"en": "Executive report drafted", "ar": "تمت صياغة التقرير التنفيذي"},
        },
    }

    seen_tools = []
    for call in history:
        t_name = call.get("tool")
        if t_name and t_name not in seen_tools:
            seen_tools.append(t_name)

    if not seen_tools:
        return ""

    steps_html = []
    arrow = "←" if lang == "ar" else "➔"
    lang_key = "ar" if lang == "ar" else "en"

    for idx, t_name in enumerate(seen_tools):
        info = tool_label_map.get(t_name, {
            "title": {"en": t_name, "ar": t_name},
            "sub": {"en": "Tool executed successfully", "ar": "تم تنفيذ الأداة بنجاح"},
        })
        step_title = info["title"][lang_key]
        step_sub = info["sub"][lang_key]

        if idx > 0:
            steps_html.append(f'<div class="step-arrow">{arrow}</div>')

        steps_html.append(f"""
        <div class="step-box">
            <div style="color: #059669; display: flex; align-items: center;">{get_svg_icon('check_circle', size=17, color='#059669')}</div>
            <div>
                <div style="font-weight: 700; font-size: 0.82rem; color: #065f46;">{step_title}</div>
                <div style="font-size: 0.70rem; color: #64748b; line-height: 1.3;">{step_sub}</div>
            </div>
        </div>
        """)

    # If executed via MCP, append the MCP verification badge step
    if t_data.get("execution_transport") == "mcp" and steps_html:
        mcp_title = t("ref_stepper_verified_mcp", lang)
        mcp_sub = t("ref_stepper_verified_mcp_sub", lang)
        steps_html.append(f'<div class="step-arrow">{arrow}</div>')
        steps_html.append(f"""
        <div class="step-box">
            <div style="color: #059669; display: flex; align-items: center;">{get_svg_icon('check_circle', size=17, color='#059669')}</div>
            <div>
                <div style="font-weight: 700; font-size: 0.82rem; color: #065f46;">{mcp_title}</div>
                <div style="font-size: 0.70rem; color: #64748b; line-height: 1.3;">{mcp_sub}</div>
            </div>
        </div>
        """)

    return f'<div class="execution-stepper">{"".join(steps_html)}</div>'


def render_user_execution_steps_html(t_data: dict, lang: str) -> str:
    """Renders user-friendly business execution steps with authentic execution status badges.
    
    Hides all technical tokens, MCP/stdio internals, and raw programming identifiers from end users.
    """
    history = t_data.get("tool_calls_history", [])
    if not history:
        return ""

    tool_info_map = {
        "inspect_dataset": {
            "title": {"ar": "فحص بنية وجودة البيانات", "en": "Dataset Structure Inspection"},
            "desc": {"ar": "التحقق من توفر الأعمدة ومطابقة الحقول الأساسية", "en": "Verified required schema and columns"},
        },
        "validate_dataset": {
            "title": {"ar": "تدقيق ومطابقة أرقام المبيعات", "en": "Sales Figures Validation"},
            "desc": {"ar": "مراجعة نطاقات الأسعار والكميات وسلامة السجلات", "en": "Validated numeric ranges and data integrity"},
        },
        "summarize_sales": {
            "title": {"ar": "تحليل وتلخيص المبيعات الإجمالية", "en": "Sales & Revenue Summary"},
            "desc": {"ar": "احتساب إجمالي الإيرادات والأرباح وهامش الربح بدقة", "en": "Calculated net revenue, profit, and margins"},
        },
        "rank_products": {
            "title": {"ar": "ترتيب وتصنيف أداء المنتجات", "en": "Product Performance Ranking"},
            "desc": {"ar": "تحديد المنتجات الأعلى مبيعاً والأكثر مساهمة في الأرباح", "en": "Ranked top-performing products by sales"},
        },
        "compare_periods": {
            "title": {"ar": "مقارنة الفترات وتحليل التكاليف", "en": "Period & Cost Comparison"},
            "desc": {"ar": "مقارنة الأداء بالفترات السابقة ورصد تباين التكاليف", "en": "Compared performance against prior period"},
        },
        "detect_anomalies": {
            "title": {"ar": "كشف الأنماط والقيم الشاذة", "en": "Anomaly & Pattern Detection"},
            "desc": {"ar": "رصد المعاملات غير المعتادة وفروقات الأسعار الإحصائية", "en": "Scanned for statistical outliers and unusual trends"},
        },
        "segment_sales": {
            "title": {"ar": "تجزئة المبيعات حسب الفئات", "en": "Sales Segmentation by Category"},
            "desc": {"ar": "تحليل توزيع المبيعات عبر الفئات ومجموعات المنتجات", "en": "Analyzed revenue distribution across categories"},
        },
        "generate_report": {
            "title": {"ar": "إعداد التقرير المالي التنفيذي", "en": "Executive Financial Report Drafting"},
            "desc": {"ar": "صياغة التقرير الإداري الشامل وتجهيزه للاعتماد", "en": "Drafted executive report and prepared for approval"},
        },
    }

    status_badge_map = {
        "success": {
            "ar": '<span style="display:inline-flex;align-items:center;gap:4px;background:#ecfdf5;color:#065f46;border:1px solid #a7f3d0;padding:3px 10px;border-radius:20px;font-weight:700;font-size:0.75rem;">✓ مكتمل</span>',
            "en": '<span style="display:inline-flex;align-items:center;gap:4px;background:#ecfdf5;color:#065f46;border:1px solid #a7f3d0;padding:3px 10px;border-radius:20px;font-weight:700;font-size:0.75rem;">✓ Completed</span>',
        },
        "approval_required": {
            "ar": '<span style="display:inline-flex;align-items:center;gap:4px;background:#fefce8;color:#854d0e;border:1px solid #fef08a;padding:3px 10px;border-radius:20px;font-weight:700;font-size:0.75rem;">⏳ بانتظار الموافقة</span>',
            "en": '<span style="display:inline-flex;align-items:center;gap:4px;background:#fefce8;color:#854d0e;border:1px solid #fef08a;padding:3px 10px;border-radius:20px;font-weight:700;font-size:0.75rem;">⏳ Awaiting Approval</span>',
        },
        "denied": {
            "ar": '<span style="display:inline-flex;align-items:center;gap:4px;background:#f1f5f9;color:#475569;border:1px solid #cbd5e1;padding:3px 10px;border-radius:20px;font-weight:700;font-size:0.75rem;">✕ تم الرفض</span>',
            "en": '<span style="display:inline-flex;align-items:center;gap:4px;background:#f1f5f9;color:#475569;border:1px solid #cbd5e1;padding:3px 10px;border-radius:20px;font-weight:700;font-size:0.75rem;">✕ Denied</span>',
        },
        "error": {
            "ar": '<span style="display:inline-flex;align-items:center;gap:4px;background:#fef2f2;color:#991b1b;border:1px solid #fecaca;padding:3px 10px;border-radius:20px;font-weight:700;font-size:0.75rem;">✕ تعذر التنفيذ</span>',
            "en": '<span style="display:inline-flex;align-items:center;gap:4px;background:#fef2f2;color:#991b1b;border:1px solid #fecaca;padding:3px 10px;border-radius:20px;font-weight:700;font-size:0.75rem;">✕ Failed</span>',
        },
        "failure": {
            "ar": '<span style="display:inline-flex;align-items:center;gap:4px;background:#fef2f2;color:#991b1b;border:1px solid #fecaca;padding:3px 10px;border-radius:20px;font-weight:700;font-size:0.75rem;">✕ تعذر التنفيذ</span>',
            "en": '<span style="display:inline-flex;align-items:center;gap:4px;background:#fef2f2;color:#991b1b;border:1px solid #fecaca;padding:3px 10px;border-radius:20px;font-weight:700;font-size:0.75rem;">✕ Failed</span>',
        },
    }

    lang_k = "ar" if lang == "ar" else "en"
    rows_html = []

    for item in history:
        turn = item.get("turn", 1)
        tool_raw = item.get("tool", "")
        status_raw = item.get("status", "success")

        info = tool_info_map.get(tool_raw, {
            "title": {"ar": f"إجراء تحليلي ({turn})", "en": f"Analytical Action ({turn})"},
            "desc": {"ar": "تم تنفيذ التحقق المعتمد", "en": "Verified analytical check executed"},
        })
        title = info["title"][lang_k]
        desc = info["desc"][lang_k]

        badge = status_badge_map.get(status_raw, status_badge_map["success"])[lang_k]

        rows_html.append(f"""
        <div style="background: #ffffff; border: 1px solid #e8e5df; border-radius: 10px; padding: 10px 14px; margin-bottom: 7px; display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="background: #ecfdf5; border: 1px solid #a7f3d0; width: 26px; height: 26px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.78rem; color: #065f46;">
                    {turn}
                </div>
                <div>
                    <div style="font-weight: 700; font-size: 0.85rem; color: #0f172a;">{title}</div>
                    <div style="font-size: 0.74rem; color: #64748b; margin-top: 1px;">{desc}</div>
                </div>
            </div>
            <div>
                {badge}
            </div>
        </div>
        """)

    return f'<div style="margin-top: 4px; margin-bottom: 4px;">{"".join(rows_html)}</div>'


# -----------------------------------------------------------------------------
# Top Header Bar & Language Switcher
# -----------------------------------------------------------------------------
cur_view = st.session_state.get("current_view_key", "overview")

if cur_view == "overview":
    # Reference Image 3 Top Header: Title on Right (RTL), Live Update & Date & Language on Left
    active_date_span = t("ref_date_range_label", lang)
    active_ds_badge = ""
    if st.session_state.get("dataset_loaded", False):
        try:
            _ds = DatasetManager.get_dataset(st.session_state.session_id)
            if len(_ds.valid_df) > 0:
                active_date_span = format_dataset_date_span(_ds.valid_df, lang)
                fn = st.session_state.get("active_filename", "dataset.csv")
                rows_cnt = len(_ds.valid_df)
                active_ds_badge = f"""
                <span style="display: inline-flex; align-items: center; gap: 5px; font-size: 0.76rem; color: #047857; background: #ecfdf5; border: 1px solid #a7f3d0; padding: 2px 8px; border-radius: 12px; font-weight: 600; margin-inline-start: 8px;">
                    <span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#10b981;"></span>
                    <span>{fn} ({rows_cnt} {t('metric_valid_rows', lang)})</span>
                </span>
                """
        except Exception:
            pass

    header_col1, header_col2 = st.columns([5.0, 4.0])
    with header_col1:
        render_trusted_html(
            f"""
            <div style="padding: 2px 0 6px 0;">
                <div style="display: flex; align-items: center; flex-wrap: wrap; gap: 4px;">
                    <h1 style="margin: 0; font-size: 1.70rem; font-weight: 800; color: #0f172a; letter-spacing: -0.02em; line-height: 1.2;">
                        {t('ref_performance_title', lang)}
                    </h1>
                    {active_ds_badge}
                </div>
                <div style="color: #64748b; font-size: 0.88rem; margin-top: 3px; font-weight: 500;">
                    {t('ref_performance_subtitle', lang)}
                </div>
            </div>
            """
        )
    with header_col2:
        top_sub_c1, top_sub_c2 = st.columns([2.3, 1.7])
        with top_sub_c1:
            render_trusted_html(
                f"""
                <div style="display: flex; align-items: center; justify-content: flex-end; gap: 8px; margin-top: 6px; flex-wrap: wrap;">
                    <div style="display: inline-flex; align-items: center; gap: 5px; font-size: 0.78rem; color: #475569; font-weight: 500;">
                        <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#10b981;"></span>
                        <span>{t('ref_last_updated_today', lang)}</span>
                    </div>
                    <div class="header-date-pill" style="cursor: default;" title="{t('ref_date_span_prefix', lang)} {active_date_span}">
                        {get_svg_icon('calendar', size=13, color='#64748b')}
                        <span>{active_date_span}</span>
                    </div>
                </div>
                """
            )
        with top_sub_c2:
            def on_language_toggle():
                chosen = st.session_state.get("lang_selector_choice")
                new_lang = "ar" if chosen == "العربية" else "en"
                if new_lang != st.session_state.language:
                    st.session_state.language = new_lang

            cur_choice = "English" if lang == "en" else "العربية"
            if hasattr(st, "segmented_control"):
                st.segmented_control(
                    label=t("lang_toggle_label", lang),
                    options=["English", "العربية"],
                    default=cur_choice,
                    key="lang_selector_choice",
                    on_change=on_language_toggle,
                    label_visibility="collapsed",
                )
            else:
                st.radio(
                    label=t("lang_toggle_label", lang),
                    options=["English", "العربية"],
                    index=0 if lang == "en" else 1,
                    horizontal=True,
                    key="lang_selector_choice",
                    on_change=on_language_toggle,
                    label_visibility="collapsed",
                )
elif cur_view == "agent":
    # Reference Image 2 Top Header
    header_col1, header_col2 = st.columns([5.0, 4.0])
    with header_col1:
        render_trusted_html(
            f"""
            <div style="display: flex; align-items: center; gap: 12px; padding: 2px 0 6px 0;">
                <div class="brand-logo-wrap" style="width: 40px; height: 40px; background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 12px; display: flex; align-items: center; justify-content: center;">
                    {get_svg_icon('bar_chart', size=20, color='#059669')}
                </div>
                <div>
                    <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                        <h1 style="margin: 0; font-size: 1.55rem; font-weight: 800; color: #0f172a; line-height: 1.2;">
                            {t('ref_analyst_title', lang)}
                        </h1>
                        <span class="status-badge badge-success">
                            <span style="display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: #10b981;"></span>
                            <span>{t('ref_store_status', lang)}</span>
                        </span>
                    </div>
                    <div style="color: #64748b; font-size: 0.82rem; margin-top: 2px;">
                        {t('ref_analyst_subtitle', lang)}
                    </div>
                </div>
            </div>
            """
        )
    with header_col2:
        top_sub_c1, top_sub_c2 = st.columns([2.0, 2.0])
        with top_sub_c1:
            render_trusted_html(
                f"""
                <div style="display: flex; align-items: center; justify-content: flex-end; gap: 6px; margin-top: 8px;">
                    <span style="font-size: 0.90rem; font-weight: 800; color: #0f172a;">RetailMind AI</span>
                    <span style="color: #cbd5e1;">|</span>
                    <span style="font-size: 0.76rem; color: #64748b; font-weight: 500;">{t('ref_brand_tagline', lang)}</span>
                </div>
                """
            )
        with top_sub_c2:
            def on_language_toggle_agent():
                chosen = st.session_state.get("lang_selector_choice")
                new_lang = "ar" if chosen == "العربية" else "en"
                if new_lang != st.session_state.language:
                    st.session_state.language = new_lang

            cur_choice = "English" if lang == "en" else "العربية"
            if hasattr(st, "segmented_control"):
                st.segmented_control(
                    label=t("lang_toggle_label", lang),
                    options=["English", "العربية"],
                    default=cur_choice,
                    key="lang_selector_choice",
                    on_change=on_language_toggle_agent,
                    label_visibility="collapsed",
                )
            else:
                st.radio(
                    label=t("lang_toggle_label", lang),
                    options=["English", "العربية"],
                    index=0 if lang == "en" else 1,
                    horizontal=True,
                    key="lang_selector_choice",
                    on_change=on_language_toggle_agent,
                    label_visibility="collapsed",
                )
elif cur_view == "dataset":
    # Reference Image 1 Top Header: Title on Right (RTL), User Greeting & Language Switcher on Left
    header_col1, header_col2 = st.columns([5.0, 4.0])
    with header_col1:
        render_trusted_html(
            f"""
            <div style="padding: 2px 0 6px 0;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <h1 style="margin: 0; font-size: 1.65rem; font-weight: 800; color: #0f172a; line-height: 1.2;">
                        {t('ref_governance_title', lang)}
                    </h1>
                </div>
                <div style="color: #64748b; font-size: 0.82rem; margin-top: 3px;">
                    {t('ref_governance_subtitle', lang)}
                </div>
            </div>
            """
        )
    with header_col2:
        top_sub_c1, top_sub_c2 = st.columns([2.3, 1.7])
        with top_sub_c1:
            render_trusted_html(
                f"""
                <div style="display: flex; align-items: center; justify-content: flex-end; gap: 10px; margin-top: 6px;">
                    <div style="text-align: {'left' if lang == 'en' else 'right'};">
                        <div style="font-size: 0.90rem; font-weight: 800; color: #0f172a;">{t('ref_user_greeting', lang)}</div>
                        <div style="font-size: 0.72rem; color: #64748b;">{t('ref_user_subtitle', lang)}</div>
                    </div>
                    <div style="width: 36px; height: 36px; border-radius: 50%; background: #f8fafc; border: 1px solid #e2e8f0; display: flex; align-items: center; justify-content: center; color: #64748b;">
                        {get_svg_icon('user', size=18, color='#64748b')}
                    </div>
                </div>
                """
            )
        with top_sub_c2:
            def on_language_toggle_dataset():
                chosen = st.session_state.get("lang_selector_choice")
                new_lang = "ar" if chosen == "العربية" else "en"
                if new_lang != st.session_state.language:
                    st.session_state.language = new_lang

            cur_choice = "English" if lang == "en" else "العربية"
            if hasattr(st, "segmented_control"):
                st.segmented_control(
                    label=t("lang_toggle_label", lang),
                    options=["English", "العربية"],
                    default=cur_choice,
                    key="lang_selector_choice",
                    on_change=on_language_toggle_dataset,
                    label_visibility="collapsed",
                )
            else:
                st.radio(
                    label=t("lang_toggle_label", lang),
                    options=["English", "العربية"],
                    index=0 if lang == "en" else 1,
                    horizontal=True,
                    key="lang_selector_choice",
                    on_change=on_language_toggle_dataset,
                    label_visibility="collapsed",
                )
else:
    header_col1, header_col2 = st.columns([4.5, 3.5])
    with header_col1:
        render_trusted_html(
            f"""
            <div class="brand-badge" style="padding: 2px 0 8px 0;">
                <div class="brand-logo-wrap">
                    {get_svg_icon('brand_sprout', size=24, color='#059669')}
                </div>
                <div>
                    <div style="font-size: 1.25rem; font-weight: 800; color: #0f172a; line-height: 1.2;">RetailMind AI</div>
                    <div style="color: #64748b; font-size: 0.78rem;">{t('ref_brand_tagline', lang)}</div>
                </div>
            </div>
            """
        )
    with header_col2:
        top_sub_c1, top_sub_c2 = st.columns([1.5, 1.5])
        with top_sub_c1:
            render_trusted_html(
                f"""
                <div class="status-badge badge-success" style="margin-top: 6px;">
                    <span style="display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: #10b981;"></span>
                    <span>{t('ref_store_status', lang)}</span>
                </div>
                """
            )
        with top_sub_c2:
            def on_language_toggle_other():
                chosen = st.session_state.get("lang_selector_choice")
                new_lang = "ar" if chosen == "العربية" else "en"
                if new_lang != st.session_state.language:
                    st.session_state.language = new_lang

            cur_choice = "English" if lang == "en" else "العربية"
            if hasattr(st, "segmented_control"):
                st.segmented_control(
                    label=t("lang_toggle_label", lang),
                    options=["English", "العربية"],
                    default=cur_choice,
                    key="lang_selector_choice",
                    on_change=on_language_toggle_other,
                    label_visibility="collapsed",
                )
            else:
                st.radio(
                    label=t("lang_toggle_label", lang),
                    options=["English", "العربية"],
                    index=0 if lang == "en" else 1,
                    horizontal=True,
                    key="lang_selector_choice",
                    on_change=on_language_toggle_other,
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


def load_dataset_from_bytes(file_bytes: bytes, filename: str, auth_token: Optional[str] = None) -> ProcessedDataset:
    try:
        df = pd.read_csv(io.BytesIO(file_bytes), encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(io.BytesIO(file_bytes), encoding="latin-1")
    effective_token = auth_token or st.session_state.get("local_dev_token") or os.getenv("RETAILMIND_AUTH_TOKEN")
    processed = DatasetManager.register_dataset(
        st.session_state.session_id, df, user_id=st.session_state.user_id, auth_token=effective_token
    )
    st.session_state.dataset_loaded = True
    st.session_state.active_csv_path = processed.snapshot_path
    st.session_state.active_filename = filename
    st.session_state.dataset_fingerprint = processed.fingerprint
    return processed


if st.query_params.get("load_sample") == "1" and not st.session_state.dataset_loaded:
    sample_csv = WORKSPACE_ROOT / "sample_data" / "synthetic_sales.csv"
    if sample_csv.exists():
        try:
            load_dataset_from_path(sample_csv, "synthetic_sales.csv")
        except Exception:
            pass


# -----------------------------------------------------------------------------
# Sidebar Navigation & System Controls
# -----------------------------------------------------------------------------
is_dev = check_developer_authorization()
view_keys = MERCHANT_VIEWS + DEVELOPER_VIEWS if is_dev else MERCHANT_VIEWS

with st.sidebar:
    render_trusted_html(
        f"""
        <div style="display: flex; align-items: center; gap: 10px; padding: 4px 0 14px 0; border-bottom: 1px solid #f1f0ec; margin-bottom: 12px;">
            <div style="background: #fefce8; border: 1px solid #fef08a; padding: 7px; border-radius: 10px; color: #d97706; display: inline-flex; align-items: center; justify-content: center; box-shadow: 0 2px 6px rgba(217, 119, 6, 0.1);">
                {get_svg_icon('brand_leaf', size=22, color='#d97706')}
            </div>
            <div>
                <div style="font-size: 1.18rem; font-weight: 800; color: #0f172a; letter-spacing: -0.01em; line-height: 1.2;">RetailMind AI</div>
                <div style="color: #78716c; font-size: 0.72rem; font-weight: 500;">{t('ref_brand_tagline', lang)}</div>
            </div>
        </div>
        """
    )

    # NAV-01: Clean business status in header
    render_trusted_html(
        f"""
        <div style='margin-bottom: 12px; display: flex; align-items: center; gap: 8px;'>
            <span class='status-badge badge-success' style='font-size: 0.78rem; font-weight: 600; padding: 4px 10px;'>{t('ref_sidebar_ai_status', lang)}</span>
        </div>
        """
    )

    # NAV-05: Visual partition into Merchant Operations & Developer Console
    nav_labels = {
        "en": {
            "overview": "Overview Dashboard",
            "agent": "AI Sales Agent",
            "dataset": "Data & Governance",
            "memory": "Saved Insights",
            "audit": "🛡️ Security & Audit Trail",
        },
        "ar": {
            "overview": "الرئيسية",
            "agent": "المحلل الذكي",
            "dataset": "البيانات والحوكمة",
            "memory": "الرؤى المحفوظة",
            "audit": "🛡️ سجل التدقيق والأمان",
        },
    }

    cur_view = st.session_state.get("current_view_key", "overview")
    default_idx = view_keys.index(cur_view) if cur_view in view_keys else 0

    def on_nav_change():
        st.session_state.current_view_key = st.session_state.nav_radio_widget
        try:
            st.query_params["view"] = st.session_state.nav_radio_widget
        except Exception:
            pass

    render_trusted_html(
        f"<div style='font-size: 0.72rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin: 4px 0 6px 4px;'>{t('ref_nav_ops', lang)}</div>"
    )

    selected_view = st.radio(
        t("nav_menu", lang),
        view_keys,
        index=default_idx,
        format_func=lambda k: nav_labels[lang].get(k, k),
        label_visibility="collapsed",
        key="nav_radio_widget",
        on_change=on_nav_change,
    )

    if cur_view in DEVELOPER_VIEWS and not is_dev:
        active_view = cur_view
    else:
        active_view = selected_view
        st.session_state.current_view_key = active_view

    if is_dev:
        render_trusted_html(
            f"""
            <div style='margin-top: 6px; padding: 6px 10px; background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 8px; font-size: 0.74rem; color: #065f46; font-weight: 700; display: flex; align-items: center; gap: 6px;'>
                <span>🛠️</span>
                <span>{t('dev_section_title', lang)}</span>
            </div>
            """
        )

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # NAV-02: Simplified Session Dataset Expander
    with st.expander(f"📁 {t('sidebar_session_dataset', lang)}", expanded=False):
        if st.session_state.dataset_loaded:
            st.success(t("dataset_loaded_label", lang, filename=st.session_state.active_filename))
            if st.query_params.get("dev_mode") == "1":
                st.caption(t("fingerprint_label", lang, fp=st.session_state.dataset_fingerprint[:12]))
            try:
                active_ds = DatasetManager.get_dataset(st.session_state.session_id)
                if active_ds.is_synthetic:
                    st.caption(f"🛡️ {t('badge_dataset_synthetic', lang)}")
                else:
                    st.caption(f"🔒 {t('badge_dataset_custom', lang)}")
            except Exception:
                pass
        else:
            st.info(t("no_dataset_loaded", lang))
            sample_csv_path = WORKSPACE_ROOT / "sample_data" / "synthetic_sales.csv"
            if sample_csv_path.exists():
                if st.button(t("btn_load_sample", lang), use_container_width=True, key="btn_sample_1"):
                    with st.spinner(t("spinner_load_sample", lang)):
                        load_dataset_from_path(sample_csv_path, "synthetic_sales.csv")
                        st.rerun()

    # NAV-03: Consolidated Advanced Diagnostics Drawer
    with st.expander(f"⚙️ {t('ref_advanced_diagnostics', lang)}", expanded=False):
        render_trusted_html(
            f"""
            <div style='margin-bottom: 12px; display: flex; flex-wrap: wrap; gap: 5px;'>
                <span class='status-badge badge-success'>{t('status_model', lang)}</span>
                <span class='status-badge badge-info'>{t('status_mcp', lang)}</span>
                <span class='status-badge badge-warning'>{t('status_policy', lang)}</span>
            </div>
            """
        )
        st.markdown(f"**{t('guardrails_header', lang)}**")
        st.caption(t("lbl_session", lang, session=st.session_state.session_id))
        st.caption(t("lbl_user", lang, user=st.session_state.user_id))
        st.caption(t("lbl_budget_cap", lang, cap=settings.budget_per_task_usd))
        st.caption(t("lbl_max_turns", lang, turns=settings.max_turns))

        if st.button(t("btn_reset_chat", lang), use_container_width=True, key="btn_reset_chat_sidebar"):
            st.session_state.chat_history = []
            st.session_state.pending_approval = None
            st.session_state.last_generated_report = None
            st.rerun()

        st.markdown("---")
        st.markdown(f"**{t('dev_mode_title', lang)}**")
        local_bound = is_local_interface_bound()
        configured_secret = os.getenv("RETAILMIND_LOCAL_DEV_SECRET")

        if not local_bound:
            st.caption(t("dev_mode_err_public_binding", lang))
        else:
            is_dev_authorized = check_developer_authorization()

            if is_dev_authorized:
                st.success(t("dev_badge_active", lang))
                if st.button(t("dev_btn_lock", lang), use_container_width=True, key="btn_revoke_dev_sidebar"):
                    st.session_state.local_dev_token = None
                    st.session_state.current_view_key = "overview"
                    try:
                        st.query_params["view"] = "overview"
                    except Exception:
                        pass
                    st.rerun()
            else:
                st.info(t("dev_mode_badge_unauthorized", lang))
                if configured_secret:
                    entered_secret = st.text_input(
                        t("dev_mode_secret_input", lang),
                        type="password",
                        placeholder=t("dev_mode_secret_placeholder", lang),
                        key="sidebar_dev_secret_input",
                    )
                    if st.button(t("forbidden_login_btn", lang), use_container_width=True, key="btn_auth_dev_sidebar"):
                        if entered_secret and hmac.compare_digest(entered_secret, configured_secret):
                            st.session_state.local_dev_token = entered_secret
                            st.success(t("dev_mode_success_auth", lang))
                            st.rerun()
                        else:
                            st.error(t("dev_mode_err_invalid", lang))
                else:
                    st.caption(t("dev_mode_err_no_secret_env", lang))

    render_trusted_html(
        f"""
        <div style="margin-top: 18px; padding-top: 14px; border-top: 1px solid #f1f0ec; display: flex; flex-direction: column; gap: 7px;">
            <div style="display: flex; align-items: center; gap: 8px; font-size: 0.78rem; color: #065f46; background: #ecfdf5; padding: 6px 12px; border-radius: 20px; border: 1px solid #a7f3d0;">
                <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #10b981;"></span>
                <span style="font-weight: 600;">{t('ref_memory_status', lang)}</span>
            </div>
            <div style="display: flex; align-items: center; gap: 8px; font-size: 0.78rem; color: #475569; background: #f8fafc; padding: 6px 12px; border-radius: 20px; border: 1px solid #e2e8f0;">
                {get_svg_icon('shield_check', size=14, color='#64748b')}
                <span>{t('ref_permission_status', lang)}</span>
            </div>
        </div>
        <div style="margin-top: 20px; text-align: center; padding: 4px 0;">
            <svg width="100%" height="34" viewBox="0 0 200 34" fill="none" xmlns="http://www.w3.org/2000/svg" style="opacity: 0.85;">
                <path d="M0 34C60 34 80 6 200 0V34H0Z" fill="url(#wave_gold)" opacity="0.35"/>
                <path d="M0 34C50 34 90 14 200 6V34H0Z" fill="url(#wave_emerald)" opacity="0.45"/>
                <defs>
                    <linearGradient id="wave_gold" x1="0" y1="0" x2="200" y2="34" gradientUnits="userSpaceOnUse">
                        <stop stop-color="#f59e0b"/>
                        <stop offset="1" stop-color="#d97706"/>
                    </linearGradient>
                    <linearGradient id="wave_emerald" x1="0" y1="0" x2="200" y2="34" gradientUnits="userSpaceOnUse">
                        <stop stop-color="#10b981"/>
                        <stop offset="1" stop-color="#059669"/>
                    </linearGradient>
                </defs>
            </svg>
            <div style="color: #94a3b8; font-size: 0.74rem; font-weight: 600; margin-top: 4px;">{t('ref_brand_bottom_tagline', lang)}</div>
        </div>
        """
    )


# -----------------------------------------------------------------------------
# Date Context Bar (Rendered for non-overview/non-agent views)
# -----------------------------------------------------------------------------
if active_view not in ["overview", "agent"] and (active_view not in DEVELOPER_VIEWS or check_developer_authorization()):
    render_trusted_html(
        f"""
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; flex-wrap: wrap; gap: 8px;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <div style="display: inline-flex; align-items: center; gap: 6px; background: #f8fafc; border: 1px solid #e2e8f0; padding: 5px 12px; border-radius: 20px; font-size: 0.78rem; color: #64748b;">
                    {get_svg_icon('calendar', size=14, color='#64748b')}
                    <span>{format_current_date(lang)}</span>
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="display: inline-flex; align-items: center; gap: 5px; font-size: 0.75rem; color: #64748b;">
                    <span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:#10b981;"></span>
                    <span>{t('ref_last_updated_today', lang)}</span>
                </div>
                <div class="header-date-pill">
                    {get_svg_icon('clock', size=13, color='#64748b')}
                    <span style="font-size:0.75rem;">{t('ref_date_range_label', lang)}</span>
                </div>
            </div>
        </div>
        """
    )


# -----------------------------------------------------------------------------
# View 1: 📊 Overview Dashboard (1:1 with Reference Image 3)
# -----------------------------------------------------------------------------
if active_view == "overview":
    if not st.session_state.dataset_loaded:
        render_trusted_html(
            f"""
            <div class="onboarding-card">
                <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 14px;">
                    <div style="background: #ecfdf5; border: 1px solid #a7f3d0; color: #059669; padding: 10px; border-radius: 12px; display: inline-flex; align-items: center; justify-content: center;">
                        {get_svg_icon('brand_sprout', size=26, color='#059669')}
                    </div>
                    <div>
                        <h2 style="margin: 0; font-size: 1.35rem; font-weight: 800; color: #0f172a;">{t('onboarding_welcome_title', lang)}</h2>
                        <div style="color: #64748b; font-size: 0.85rem; margin-top: 4px; line-height: 1.4;">{t('onboarding_welcome_subtitle', lang)}</div>
                    </div>
                </div>
                <div class="onboarding-grid">
                    <div class="onboarding-step">
                        <div class="onboarding-step-icon">
                            {get_svg_icon('file_up', size=20, color='#059669')}
                        </div>
                        <div style="font-weight: 700; font-size: 0.95rem; color: #0f172a; margin-bottom: 6px;">{t('onboarding_step1_title', lang)}</div>
                        <div style="font-size: 0.82rem; color: #64748b; line-height: 1.4;">{t('onboarding_step1_desc', lang)}</div>
                    </div>
                    <div class="onboarding-step">
                        <div class="onboarding-step-icon">
                            {get_svg_icon('dashboard', size=20, color='#059669')}
                        </div>
                        <div style="font-weight: 700; font-size: 0.95rem; color: #0f172a; margin-bottom: 6px;">{t('onboarding_step2_title', lang)}</div>
                        <div style="font-size: 0.82rem; color: #64748b; line-height: 1.4;">{t('onboarding_step2_desc', lang)}</div>
                    </div>
                    <div class="onboarding-step">
                        <div class="onboarding-step-icon">
                            {get_svg_icon('bot', size=20, color='#059669')}
                        </div>
                        <div style="font-weight: 700; font-size: 0.95rem; color: #0f172a; margin-bottom: 6px;">{t('onboarding_step3_title', lang)}</div>
                        <div style="font-size: 0.82rem; color: #64748b; line-height: 1.4;">{t('onboarding_step3_desc', lang)}</div>
                    </div>
                </div>
            </div>
            """
        )

        ob_col1, ob_col2 = st.columns([1, 1])
        sample_csv_path = WORKSPACE_ROOT / "sample_data" / "synthetic_sales.csv"
        with ob_col1:
            if sample_csv_path.exists():
                if st.button(t("btn_onboarding_load_sample", lang), use_container_width=True, key="btn_ob_sample"):
                    with st.spinner(t("spinner_load_sample", lang)):
                        load_dataset_from_path(sample_csv_path, "synthetic_sales.csv")
                        st.rerun()
        with ob_col2:
            if st.button(t("btn_onboarding_goto_upload", lang), use_container_width=True, key="btn_ob_upload"):
                st.session_state.current_view_key = "dataset"
                st.rerun()

        st.caption(f"ℹ️ {t('catalog_pricing_notice', lang)}")
    else:
        dataset = DatasetManager.get_dataset(st.session_state.session_id)
        df = dataset.valid_df

        if len(df) == 0:
            st.error(t("err_zero_rows", lang))
        else:
            # 1. 4 Responsive KPI Cards (Ref. Image 3)
            metrics = compute_period_metrics(df, dataset.has_cost_data)
            net_revenue = metrics["net_revenue"]
            total_units = metrics["total_units"]
            total_orders = metrics["total_orders"]
            net_profit = metrics["net_profit"]
            margin_pct = metrics["margin_pct"]
            total_cost = metrics["total_cost"]
            deltas = metrics["deltas"]

            card_rev_val = f"${net_revenue:,.2f}"
            card_orders_val = f"{total_orders:,}"
            card_profit_val = f"${net_profit:,.2f}" if net_profit is not None else t("kpi_profit_unavail", lang)
            card_margin_val = f"{margin_pct:.1f}%" if margin_pct is not None else t("kpi_margin_na", lang)

            # Footer deltas: exact ground-truth calculation
            if deltas["has_comparison"] and deltas["margin_diff"] is not None:
                diff = deltas["margin_diff"]
                sign = "+" if diff >= 0 else ""
                cls = "kpi-delta-pos" if diff >= 0 else "kpi-delta-neg"
                arr = "▲" if diff >= 0 else "▼"
                margin_footer = f'<span class="{cls}">{arr} {sign}{diff:.1f}% {t("ref_compared_prev_period", lang)}</span>'
            else:
                margin_footer = f'<span class="kpi-delta-neutral">{t("ref_margin_ground_truth", lang)}</span>'

            if deltas["has_comparison"] and deltas["revenue_pct"] is not None:
                pct = deltas["revenue_pct"]
                sign = "+" if pct >= 0 else ""
                cls = "kpi-delta-pos" if pct >= 0 else "kpi-delta-neg"
                arr = "▲" if pct >= 0 else "▼"
                revenue_footer = f'<span class="{cls}">{arr} {sign}{pct:.1f}% {t("ref_compared_prev_period", lang)}</span>'
            else:
                revenue_footer = f'<span class="kpi-delta-pos">{t("ref_completed_sales", lang, count=total_orders)}</span>'

            if deltas["has_comparison"] and deltas["profit_pct"] is not None:
                pct = deltas["profit_pct"]
                sign = "+" if pct >= 0 else ""
                arr = "▲" if pct >= 0 else "▼"
                profit_footer = f'<span class="kpi-delta-pos" style="color:#a7f3d0 !important;">{arr} {sign}{pct:.1f}% {t("ref_compared_prev_period", lang)}</span>'
            elif total_cost is not None:
                profit_footer = f'<span class="kpi-delta-pos" style="color:#a7f3d0 !important;">{t("ref_total_cost_sub", lang, cost=f"${total_cost:,.2f}")}</span>'
            else:
                profit_footer = f'<span class="kpi-delta-neutral" style="color:#e2e8f0 !important;">{t("kpi_profit_delta_unavail", lang)}</span>'

            if deltas["has_comparison"] and deltas["units_pct"] is not None:
                pct = deltas["units_pct"]
                sign = "+" if pct >= 0 else ""
                cls = "kpi-delta-pos" if pct >= 0 else "kpi-delta-neg"
                arr = "▲" if pct >= 0 else "▼"
                orders_footer = f'<span class="{cls}">{arr} {sign}{pct:.1f}% {t("ref_compared_prev_period", lang)}</span>'
            else:
                orders_footer = f'<span class="kpi-delta-neutral">{t("ref_units_sold_count", lang, count=total_units)}</span>'

            # 4 Cards in RTL order matching Reference Image 3:
            # 1. Margin (هامش الربح) — Rightmost in RTL
            # 2. Revenue (الإيرادات)
            # 3. Net Profit (صافي الربح) — Hero Deep Emerald Card
            # 4. Orders (الطلبات) — Leftmost in RTL
            kpi_grid_html = textwrap.dedent(f"""
            <div class="kpi-grid">
                <div class="kpi-card">
                    <div class="kpi-header">
                        <span class="kpi-title">{t('ref_margin_title', lang)}</span>
                        <span class="kpi-icon-wrap" style="background:#fef3c7; color:#d97706;">
                            {get_svg_icon('percent', size=16, color='#d97706')}
                        </span>
                    </div>
                    <div class="kpi-value">{card_margin_val}</div>
                    <div class="kpi-footer">
                        {margin_footer}
                    </div>
                </div>

                <div class="kpi-card">
                    <div class="kpi-header">
                        <span class="kpi-title">{t('ref_revenue_title', lang)}</span>
                        <span class="kpi-icon-wrap" style="background:#ecfdf5; color:#059669;">
                            {get_svg_icon('bar_chart', size=16, color='#059669')}
                        </span>
                    </div>
                    <div class="kpi-value">{card_rev_val}</div>
                    <div class="kpi-footer">
                        {revenue_footer}
                    </div>
                </div>

                <div class="kpi-card-hero">
                    <div class="kpi-header">
                        <span class="kpi-title" style="color:#d1fae5 !important;">{t('ref_profit_title', lang)}</span>
                        <span class="kpi-icon-wrap" style="background:rgba(255,255,255,0.2) !important; color:#ffffff !important;">
                            {get_svg_icon('coins', size=16, color='#ffffff')}
                        </span>
                    </div>
                    <div class="kpi-value" style="color:#ffffff !important;">{card_profit_val}</div>
                    <div class="kpi-footer">
                        {profit_footer}
                    </div>
                </div>

                <div class="kpi-card">
                    <div class="kpi-header">
                        <span class="kpi-title">{t('ref_orders_title', lang)}</span>
                        <span class="kpi-icon-wrap" style="background:#ecfdf5; color:#059669;">
                            {get_svg_icon('shopping_cart', size=16, color='#059669')}
                        </span>
                    </div>
                    <div class="kpi-value">{card_orders_val}</div>
                    <div class="kpi-footer">
                        {orders_footer}
                    </div>
                </div>
            </div>
            """).strip()

            render_trusted_html(kpi_grid_html)

            # 2. Analytics Charts Row (Ref. Image 3: Two Columns)
            import altair as alt
            chart_col1, chart_col2 = st.columns(2)

            with chart_col1:
                with st.container(border=True):
                    render_trusted_html(f"""
                    <div class="analytics-card-header">
                        <span class="analytics-card-title">{t('chart_category_perf', lang)}</span>
                        <span class="analytics-legend">
                            <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#d97706;"></span>
                            <span>{t('ref_col_sales_revenue', lang)}</span>
                        </span>
                    </div>
                    """)
                    if "category" in df.columns:
                        cat_df = df.groupby("category")["line_revenue"].sum().reset_index()
                        cat_df = cat_df.sort_values("line_revenue", ascending=False)
                        if lang == "ar":
                            cat_df["category_label"] = cat_df["category"].map(lambda c: CATEGORY_MAP_AR.get(c, c))
                        else:
                            cat_df["category_label"] = cat_df["category"]
                        bars = (
                            alt.Chart(cat_df)
                            .mark_bar(color="#047857", cornerRadiusEnd=4)
                            .encode(
                                x=alt.X("category_label:N", title=None, sort="-y", axis=alt.Axis(labelAngle=0, labelColor="#475569", labelFontSize=11)),
                                y=alt.Y("line_revenue:Q", title=None, axis=alt.Axis(format="$,.0f", labelColor="#64748b", gridColor="#f1f5f9")),
                                tooltip=[
                                    alt.Tooltip("category_label:N", title=t("axis_category", lang)),
                                    alt.Tooltip("line_revenue:Q", title=t("axis_revenue", lang), format="$,.2f"),
                                ],
                            )
                        )
                        text = bars.mark_text(
                            align="center",
                            baseline="bottom",
                            dy=-6,
                            color="#475569",
                            fontSize=11,
                            fontWeight=600,
                        ).encode(
                            text=alt.Text("line_revenue:Q", format="$,.0f")
                        )
                        cat_chart = (bars + text).properties(height=240)
                        st.altair_chart(cat_chart, use_container_width=True)
                    else:
                        st.info(t("info_no_category", lang))

            with chart_col2:
                with st.container(border=True):
                    render_trusted_html(f"""
                    <div class="analytics-card-header">
                        <span class="analytics-card-title">{t('chart_revenue_trend', lang)}</span>
                        <span class="analytics-legend">
                            <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#059669;"></span>
                            <span>{t('kpi_net_revenue', lang)}</span>
                        </span>
                    </div>
                    """)
                    if "date" in df.columns:
                        date_df = df.groupby("date")["line_revenue"].sum().reset_index().sort_values("date")
                        trend_chart = (
                            alt.Chart(date_df)
                            .mark_area(
                                line={"color": "#059669", "strokeWidth": 2.5},
                                color=alt.Gradient(
                                    gradient="linear",
                                    stops=[
                                        alt.GradientStop(color="rgba(5, 150, 105, 0.25)", offset=0),
                                        alt.GradientStop(color="rgba(5, 150, 105, 0.01)", offset=1),
                                    ],
                                    x1=1, x2=1, y1=1, y2=0,
                                ),
                                point={"color": "#047857", "size": 36, "filled": True},
                                interpolate="monotone",
                            )
                            .encode(
                                x=alt.X("date:T", title=None, axis=alt.Axis(format="%d %b", labelAngle=0, labelColor="#475569", labelFontSize=11, gridColor="#f1f5f9")),
                                y=alt.Y("line_revenue:Q", title=None, axis=alt.Axis(format="$,.0f", labelColor="#64748b", gridColor="#f1f5f9")),
                                tooltip=[
                                    alt.Tooltip("date:T", title=t("axis_date", lang), format="%Y-%m-%d"),
                                    alt.Tooltip("line_revenue:Q", title=t("axis_revenue", lang), format="$,.2f"),
                                ],
                            )
                            .properties(height=240)
                        )
                        st.altair_chart(trend_chart, use_container_width=True)

            # 3. Top Products Summary Table (Ref. Image 3 Bottom Card)
            if "product" in df.columns:
                agg_dict = {"line_revenue": "sum", "quantity": "sum"}
                group_cols = ["product"]
                if "category" in df.columns:
                    group_cols.append("category")
                prod_summary = df.groupby(group_cols).agg(agg_dict).reset_index()
                prod_summary = prod_summary.sort_values("line_revenue", ascending=False).head(5)
                prod_summary["#"] = list(range(1, len(prod_summary) + 1))

                table_rows = []
                for _, row in prod_summary.iterrows():
                    raw_cat = row.get("category", "-")
                    cat_display = CATEGORY_MAP_AR.get(raw_cat, raw_cat) if lang == "ar" else raw_cat
                    table_rows.append(f"""
                    <tr>
                        <td style="width: 45px; color: #64748b; font-weight: 600;">{row['#']}</td>
                        <td style="font-weight: 600; color: #0f172a;">
                            <span style="display: inline-flex; align-items: center; gap: 8px;">
                                <span style="display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; border-radius: 6px; background: #f1f5f9; color: #64748b;">
                                    {get_svg_icon('package', size=15, color='#64748b')}
                                </span>
                                <span>{row['product']}</span>
                            </span>
                        </td>
                        <td style="color: #475569;">{cat_display}</td>
                        <td style="font-weight: 600; color: #0f172a;">{int(row['quantity']):,}</td>
                        <td style="font-weight: 700; color: #047857; direction: ltr; text-align: left;">${row['line_revenue']:,.2f}</td>
                    </tr>
                    """)

                render_trusted_html(f"""
                <div class="top-products-card">
                    <div style="font-size: 1.15rem; font-weight: 700; color: #0f172a; margin-bottom: 4px;">
                        {t('ref_top_products_card_title', lang)}
                    </div>
                    <div class="ref-table-wrap">
                        <table class="ref-table">
                            <thead>
                                <tr>
                                    <th style="width: 45px;">#</th>
                                    <th>{t('ref_col_product_name', lang)}</th>
                                    <th>{t('ref_col_category_name', lang)}</th>
                                    <th>{t('ref_col_sales_volume', lang)}</th>
                                    <th>{t('ref_col_sales_revenue', lang)}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {''.join(table_rows)}
                            </tbody>
                        </table>
                    </div>
                </div>
                """)

            # 4. Detailed Visualizations Expander (Top Products Horizontal Bar & Regional Distribution)
            with st.expander(f"📊 {t('chart_top_products', lang)} & {t('chart_revenue_by_region', lang)}", expanded=False):
                exp_c1, exp_c2 = st.columns(2)
                with exp_c1:
                    st.subheader(t("chart_top_products", lang))
                    if "product" in df.columns:
                        prod_df = df.groupby("product")["line_revenue"].sum().reset_index()
                        prod_df = prod_df.sort_values("line_revenue", ascending=False).head(5)
                        top_prod_chart = (
                            alt.Chart(prod_df)
                            .mark_bar(color="#059669", cornerRadiusEnd=3)
                            .encode(
                                x=alt.X("line_revenue:Q", title=t("axis_revenue", lang)),
                                y=alt.Y(
                                    "product:N",
                                    title=t("axis_product", lang),
                                    sort=alt.EncodingSortField(field="line_revenue", order="descending"),
                                    axis=alt.Axis(labelLimit=350),
                                ),
                                tooltip=[
                                    alt.Tooltip("product:N", title=t("axis_product", lang)),
                                    alt.Tooltip("line_revenue:Q", title=t("axis_revenue", lang), format="$,.2f"),
                                ],
                            )
                            .properties(height=280)
                        )
                        st.altair_chart(top_prod_chart, use_container_width=True)

                with exp_c2:
                    st.subheader(t("chart_revenue_by_region", lang))
                    if "region" in df.columns:
                        reg_df = df.groupby("region")["line_revenue"].sum().reset_index()
                        reg_df = reg_df.sort_values("line_revenue", ascending=False)
                        reg_chart = (
                            alt.Chart(reg_df)
                            .mark_bar(color="#059669", cornerRadiusEnd=3)
                            .encode(
                                x=alt.X("region:N", title=t("axis_region", lang), sort="-y"),
                                y=alt.Y("line_revenue:Q", title=t("axis_revenue", lang)),
                                tooltip=[
                                    alt.Tooltip("region:N", title=t("axis_region", lang)),
                                    alt.Tooltip("line_revenue:Q", title=t("axis_revenue", lang), format="$,.2f"),
                                ],
                            )
                            .properties(height=280)
                        )
                        st.altair_chart(reg_chart, use_container_width=True)
                    else:
                        st.info(t("info_no_region", lang))


# -----------------------------------------------------------------------------
# View 2: 💬 AI Sales Agent (Gemini + MCP)
# -----------------------------------------------------------------------------
elif active_view == "agent":
    if not st.session_state.dataset_loaded:
        st.warning(t("warn_agent_no_dataset", lang))
        sample_csv_path = WORKSPACE_ROOT / "sample_data" / "synthetic_sales.csv"
        if sample_csv_path.exists():
            if st.button(t("btn_load_sample", lang), use_container_width=True, key="btn_agent_empty_load"):
                with st.spinner(t("spinner_load_sample", lang)):
                    load_dataset_from_path(sample_csv_path, "synthetic_sales.csv")
                    st.rerun()

    # Reference Image 2: Two Columns
    # In Arabic RTL: Panel is on RIGHT, Chat is on LEFT.
    # In English LTR: Chat is on LEFT, Panel is on RIGHT.
    if lang == "ar":
        panel_col, chat_col = st.columns([3.2, 6.8])
    else:
        chat_col, panel_col = st.columns([6.8, 3.2])

    with panel_col:
        # Format active period for context card
        active_period_str = t("ref_context_period", lang)
        if st.session_state.dataset_loaded:
            try:
                _active_ds = DatasetManager.get_dataset(st.session_state.session_id)
                if len(_active_ds.valid_df) > 0:
                    active_period_str = format_dataset_date_span(_active_ds.valid_df, lang)
            except Exception:
                pass

        render_trusted_html(
            f"""
            <div style="background: #ffffff; border: 1px solid #e8e5df; border-radius: 14px; padding: 18px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
                <div style="font-weight: 700; font-size: 0.95rem; color: #0f172a; margin-bottom: 14px; display: flex; align-items: center; gap: 8px;">
                    {get_svg_icon('package', size=18, color='#059669')}
                    <span>{t('ref_tools_employed', lang)}</span>
                </div>
                <div style="display: flex; flex-direction: column; gap: 12px; font-size: 0.82rem;">
                    <div style="display: flex; align-items: flex-start; gap: 10px;">
                        <span style="color: #059669; margin-top: 2px;">{get_svg_icon('bar_chart', size=16, color='#059669')}</span>
                        <div>
                            <div style="font-weight: 700; color: #0f172a;">{t('ref_tool_revenue_title', lang)}</div>
                            <div style="color: #64748b; font-size: 0.74rem;">{t('ref_tool_revenue_desc', lang)}</div>
                        </div>
                    </div>
                    <div style="display: flex; align-items: flex-start; gap: 10px;">
                        <span style="color: #059669; margin-top: 2px;">{get_svg_icon('database', size=16, color='#059669')}</span>
                        <div>
                            <div style="font-weight: 700; color: #0f172a;">{t('ref_tool_costs_title', lang)}</div>
                            <div style="color: #64748b; font-size: 0.74rem;">{t('ref_tool_costs_desc', lang)}</div>
                        </div>
                    </div>
                    <div style="display: flex; align-items: flex-start; gap: 10px;">
                        <span style="color: #d97706; margin-top: 2px;">{get_svg_icon('alert_triangle', size=16, color='#d97706')}</span>
                        <div>
                            <div style="font-weight: 700; color: #0f172a;">{t('ref_tool_anomalies_title', lang)}</div>
                            <div style="color: #64748b; font-size: 0.74rem;">{t('ref_tool_anomalies_desc', lang)}</div>
                        </div>
                    </div>
                </div>
            </div>

            <div style="background: #fffbeb; border: 1px solid #fde68a; border-radius: 14px; padding: 16px; margin-bottom: 16px;">
                <div style="font-weight: 700; font-size: 0.88rem; color: #92400e; margin-bottom: 6px; display: flex; align-items: center; justify-content: space-between;">
                    <span style="display: flex; align-items: center; gap: 6px;">
                        {get_svg_icon('shield_check', size=16, color='#d97706')}
                        <span>{t('ref_human_approval_required', lang)}</span>
                    </span>
                    <span style="font-size: 0.80rem; color: #b45309;">›</span>
                </div>
                <div style="font-size: 0.78rem; color: #b45309; line-height: 1.45;">
                    {t('ref_human_approval_desc', lang)}
                </div>
            </div>

            <div style="background: #ffffff; border: 1px solid #e8e5df; border-radius: 14px; padding: 18px; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
                <div style="font-weight: 700; font-size: 0.95rem; color: #0f172a; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                    {get_svg_icon('info', size=17, color='#059669')}
                    <span>{t('ref_context_info', lang)}</span>
                </div>
                <div style="display: flex; flex-direction: column; gap: 10px; font-size: 0.80rem; color: #475569;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        {get_svg_icon('calendar', size=15, color='#64748b')}
                        <span>{active_period_str}</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        {get_svg_icon('store', size=15, color='#64748b')}
                        <span>{t('ref_context_store', lang)}</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        {get_svg_icon('database', size=15, color='#64748b')}
                        <span>{t('ref_context_sources', lang)}</span>
                    </div>
                </div>
                <div style="margin-top: 14px; padding-top: 10px; border-top: 1px solid #f1f5f9; font-size: 0.75rem; color: #059669; font-weight: 600; text-align: center;">
                    {t('ref_tagline_badge', lang)}
                </div>
            </div>
            """
        )

    with chat_col:
        # If no messages yet, show welcoming state
        if not st.session_state.chat_history:
            render_trusted_html(
                f"""
                <div style="background: #ffffff; border: 1px solid #e8e5df; border-radius: 14px; padding: 22px 24px; margin-bottom: 18px; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 10px;">
                        <div style="background: #ecfdf5; border: 1px solid #a7f3d0; padding: 8px; border-radius: 10px; color: #059669;">
                            {get_svg_icon('brand_sprout', size=24, color='#059669')}
                        </div>
                        <div>
                            <div style="font-weight: 800; font-size: 1.10rem; color: #0f172a;">{t('agent_welcome_box_title', lang)}</div>
                            <div style="font-size: 0.82rem; color: #64748b; margin-top: 2px;">{t('agent_welcome_box_sub', lang)}</div>
                        </div>
                    </div>
                </div>
                """
            )

        # Render chat messages
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if "transparency" in msg and msg["transparency"]:
                    t_data = msg["transparency"]
                    # Render genuine dynamic execution stepper ONLY if tools were executed
                    stepper_html = render_dynamic_execution_stepper(t_data, lang)
                    if stepper_html:
                        render_trusted_html(stepper_html)

                    # 1. User-Facing Business Steps (Free of MCP, stdio, tokens, costs, or code names)
                    tool_history = t_data.get("tool_calls_history", [])
                    if tool_history:
                        user_header = t("user_steps_header", lang, count=len(tool_history))
                        with st.expander(f"📋 {user_header}", expanded=True):
                            steps_html = render_user_execution_steps_html(t_data, lang)
                            render_trusted_html(steps_html)

                    # 2. Advanced Technical Diagnostics (Accessible to AUTHORIZED DEVELOPERS ONLY)
                    if check_developer_authorization():
                        dev_header = t("dev_diagnostics_header", lang)
                        with st.expander(f"🛠️ {dev_header}", expanded=False):
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

                            if tool_history:
                                st.markdown(t("tool_audit_title", lang))
                                for tc in tool_history:
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

        # Pending Approval Card (Human-in-the-Loop)
        if st.session_state.pending_approval:
            pending = st.session_state.pending_approval
            render_trusted_html(
                f"""
                <div class="approval-card">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <div style="background: #ecfdf5; border: 1px solid #a7f3d0; padding: 8px; border-radius: 10px; color: #059669;">
                                {get_svg_icon('file_spreadsheet', size=22, color='#059669')}
                            </div>
                            <div>
                                <div style="font-weight: 700; font-size: 1.05rem; color: #0f172a;">{t('ref_approval_card_title', lang)}</div>
                                <div style="font-size: 0.80rem; color: #64748b;">{t('ref_approval_card_sub', lang, title=pending.get("title", "Sales Report"))}</div>
                            </div>
                        </div>
                        <div class="status-badge badge-warning">
                            {get_svg_icon('clock', size=13, color='#d97706')}
                            <span>{t('ref_pending_review', lang)}</span>
                        </div>
                    </div>
                </div>
                """
            )

            col_app, col_deny = st.columns([1, 1])
            if col_app.button(t("btn_approve_report", lang), use_container_width=True, key="btn_app_rep"):
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

            if col_deny.button(t("btn_deny_report", lang), use_container_width=True, key="btn_deny_rep"):
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
            if not report_p.is_absolute():
                report_p = settings.workspace_root / report_p
            try:
                resolved_report = report_p.resolve()
                resolved_reports_dir = settings.reports_dir.resolve()
                if resolved_report.exists() and (
                    resolved_report.is_relative_to(resolved_reports_dir)
                    or str(resolved_report).startswith(str(resolved_reports_dir))
                ):
                    mime_type = "text/csv" if resolved_report.suffix.lower() == ".csv" else "text/markdown"
                    st.download_button(
                        label=t("btn_download_report", lang, filename=resolved_report.name),
                        data=resolved_report.read_text(encoding="utf-8"),
                        file_name=resolved_report.name,
                        mime=mime_type,
                    )
            except Exception:
                pass

        # Interactive Suggested Prompts (Pills immediately above input)
        st.markdown(
            f"<div style='font-size:0.82rem;font-weight:700;color:#64748b;margin:12px 0 6px 0;'>{t('ref_followup_suggestions', lang)}</div>",
            unsafe_allow_html=True,
        )
        pill_cols = st.columns(4)
        if pill_cols[0].button(t("ref_pill_revenue_summary", lang), use_container_width=True, key="pill_rev"):
            st.session_state.staged_prompt = t("query_revenue", lang)
        if pill_cols[1].button(t("ref_pill_top_products", lang), use_container_width=True, key="pill_prods"):
            st.session_state.staged_prompt = t("query_top_prods", lang)
        if pill_cols[2].button(t("ref_pill_profit_report", lang), use_container_width=True, key="pill_rep"):
            st.session_state.staged_prompt = t("query_report", lang)
        if pill_cols[3].button(t("ref_pill_anomalies", lang), use_container_width=True, key="pill_anom"):
            st.session_state.staged_prompt = t("query_compare", lang)

        # Staged prompt review bar (gives user full visibility and edit agency)
        staged_val = st.session_state.get("staged_prompt")
        user_input_from_staged = None
        if staged_val:
            st.markdown(
                f"""
                <div style="background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 10px; padding: 10px 14px; margin: 10px 0; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
                    <div style="font-size: 0.85rem; color: #065f46;">
                        <span style="font-weight: 700;">{t('ref_staged_query', lang)}</span>
                        <span>"{staged_val}"</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            col_s1, col_s2 = st.columns([3, 1])
            if col_s1.button(f"{t('ref_btn_send_staged', lang)}", use_container_width=True, key="btn_send_staged_exec"):
                user_input_from_staged = staged_val
                st.session_state.staged_prompt = None
            if col_s2.button(f"✕ {t('ref_btn_clear_staged', lang)}", use_container_width=True, key="btn_clear_staged_exec"):
                st.session_state.staged_prompt = None
                st.rerun()

        # Chat Input Box
        user_input = st.chat_input(t("chat_input_prompt", lang)) or user_input_from_staged
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

                    def ui_approval_callback(tool_name: str, args: Dict[str, Any]) -> bool:
                        if tool_name == "generate_report":
                            st.session_state.pending_approval = {
                                "title": args.get("title", "Executive Report"),
                                "args": args,
                            }
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
# View 3: 📁 Dataset Ingestion & Validation (Data & Governance)
# -----------------------------------------------------------------------------
elif active_view == "dataset":
    # -------------------------------------------------------------
    # Card 1: استيراد بيانات المبيعات (Sales Data Ingestion & Active File Card)
    # -------------------------------------------------------------
    dataset = None
    file_size_str = "0 KB"
    valid_rows_count = 0
    if st.session_state.dataset_loaded:
        try:
            dataset = DatasetManager.get_dataset(st.session_state.session_id)
            valid_rows_count = len(dataset.valid_df)
            if dataset.snapshot_path and Path(dataset.snapshot_path).exists():
                sz = Path(dataset.snapshot_path).stat().st_size
                if sz > 1024 * 1024:
                    file_size_str = f"{sz / (1024 * 1024):.1f} MB"
                else:
                    file_size_str = f"{sz / 1024:.1f} KB"
            else:
                file_size_str = f"{(len(dataset.raw_df) * 48 / 1024):.1f} KB"
        except Exception:
            pass

    has_date = bool(dataset and "date" in dataset.valid_df.columns)
    has_product = bool(dataset and "product" in dataset.valid_df.columns)
    has_revenue = bool(dataset and ("unit_price" in dataset.valid_df.columns or "line_revenue" in dataset.valid_df.columns))
    has_cost = bool(dataset and dataset.has_cost_data)
    has_quantity = bool(dataset and "quantity" in dataset.valid_df.columns)

    if dataset:
        active_box_html = f"""
        <div style="background: #fafaf9; border: 1.5px dashed #cbd5e1; border-radius: 12px; padding: 16px 20px; margin: 18px 0; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
            <div style="display: flex; align-items: center; gap: 14px;">
                <div style="background: #ffffff; border: 1px solid #a7f3d0; padding: 10px; border-radius: 10px; color: #059669; display: inline-flex; align-items: center; justify-content: center; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
                    {get_svg_icon('file_spreadsheet', size=26, color='#059669')}
                </div>
                <div>
                    <div style="font-weight: 800; font-size: 1.05rem; color: #0f172a;">{st.session_state.active_filename}</div>
                    <div style="color: #64748b; font-size: 0.80rem; margin-top: 2px;">{file_size_str} • {valid_rows_count:,} {t('lbl_valid_rows', lang)}</div>
                </div>
            </div>
            <div class="status-badge badge-success" style="padding: 6px 14px; font-size: 0.82rem; font-weight: 700;">
                {get_svg_icon('check_circle', size=16, color='#059669')}
                <span>{t('ref_badge_verified', lang)}</span>
            </div>
        </div>
        """
    else:
        active_box_html = f"""
        <div style="background: #fafaf9; border: 1.5px dashed #cbd5e1; border-radius: 12px; padding: 22px 20px; margin: 18px 0; text-align: center;">
            <div style="color: #64748b; font-size: 0.90rem; margin-bottom: 6px;">{t('no_dataset_loaded', lang)}</div>
            <div style="font-size: 0.78rem; color: #94a3b8;">{t('ref_upload_box_sub', lang)}</div>
        </div>
        """

    pills_html = f"""
    <div style="margin-top: 18px;">
        <div style="font-weight: 700; font-size: 0.92rem; color: #0f172a; margin-bottom: 12px;">
            {t('ref_col_matching_title', lang)}
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 12px;">
            <div class="col-match-pill {'matched' if has_date else ''}">
                <div style="display: flex; align-items: center; gap: 5px;">
                    <span style="font-weight: 700; font-size: 0.84rem; color: {'#065f46' if has_date else '#94a3b8'};">{t('lbl_col_date', lang)}</span>
                    <span style="color: {'#059669' if has_date else '#94a3b8'};">{get_svg_icon('check_circle', size=14, color='#059669') if has_date else '○'}</span>
                </div>
                <div style="font-size: 0.72rem; color: #64748b;">{t('ref_col_type_date', lang)}</div>
            </div>
            <div class="col-match-pill {'matched' if has_product else ''}">
                <div style="display: flex; align-items: center; gap: 5px;">
                    <span style="font-weight: 700; font-size: 0.84rem; color: {'#065f46' if has_product else '#94a3b8'};">{t('lbl_col_product', lang)}</span>
                    <span style="color: {'#059669' if has_product else '#94a3b8'};">{get_svg_icon('check_circle', size=14, color='#059669') if has_product else '○'}</span>
                </div>
                <div style="font-size: 0.72rem; color: #64748b;">{t('ref_col_type_product', lang)}</div>
            </div>
            <div class="col-match-pill {'matched' if has_revenue else ''}">
                <div style="display: flex; align-items: center; gap: 5px;">
                    <span style="font-weight: 700; font-size: 0.84rem; color: {'#065f46' if has_revenue else '#94a3b8'};">{t('lbl_col_price', lang)}</span>
                    <span style="color: {'#059669' if has_revenue else '#94a3b8'};">{get_svg_icon('check_circle', size=14, color='#059669') if has_revenue else '○'}</span>
                </div>
                <div style="font-size: 0.72rem; color: #64748b;">{t('ref_col_type_number', lang)}</div>
            </div>
            <div class="col-match-pill {'matched' if has_cost else ''}">
                <div style="display: flex; align-items: center; gap: 5px;">
                    <span style="font-weight: 700; font-size: 0.84rem; color: {'#065f46' if has_cost else '#94a3b8'};">{t('lbl_col_cost', lang)}</span>
                    <span style="color: {'#059669' if has_cost else '#94a3b8'};">{get_svg_icon('check_circle', size=14, color='#059669') if has_cost else '○'}</span>
                </div>
                <div style="font-size: 0.72rem; color: #64748b;">{t('ref_col_type_number', lang) if has_cost else t('ref_col_cost_unavailable', lang)}</div>
            </div>
            <div class="col-match-pill {'matched' if has_quantity else ''}">
                <div style="display: flex; align-items: center; gap: 5px;">
                    <span style="font-weight: 700; font-size: 0.84rem; color: {'#065f46' if has_quantity else '#94a3b8'};">{t('lbl_col_quantity', lang)}</span>
                    <span style="color: {'#059669' if has_quantity else '#94a3b8'};">{get_svg_icon('check_circle', size=14, color='#059669') if has_quantity else '○'}</span>
                </div>
                <div style="font-size: 0.72rem; color: #64748b;">{t('ref_col_type_number', lang)}</div>
            </div>
        </div>
    </div>
    """

    render_trusted_html(f"""
    <div style="background: #ffffff; border: 1px solid #e8e5df; border-radius: 14px; padding: 22px 24px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
            <div>
                <div style="font-weight: 800; font-size: 1.15rem; color: #0f172a;">{t('ref_upload_box_title', lang)}</div>
                <div style="font-size: 0.82rem; color: #64748b; margin-top: 2px;">{t('ref_upload_box_sub', lang)}</div>
            </div>
            <div style="color: #64748b; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 8px; display: flex; align-items: center; justify-content: center;">
                {get_svg_icon('cloud_upload', size=24, color='#64748b')}
            </div>
        </div>
        {active_box_html}
        {pills_html}
    </div>
    """)

    # Upload Actions & Controls Expander
    uploader_expanded = not st.session_state.dataset_loaded or st.session_state.get("uploader_has_error", False)
    with st.expander(f"📁 {t('uploader_label', lang)}", expanded=uploader_expanded):
        is_dev_authorized = check_developer_authorization()

        # Clear permissions notice before choosing file
        if is_dev_authorized:
            render_trusted_html(
                f"""
                <div style="background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 10px; padding: 10px 14px; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
                    <div style="display: flex; align-items: center; gap: 8px; color: #065f46; font-size: 0.84rem; font-weight: 600;">
                        <span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:#10b981;"></span>
                        <span>{t('auth_status_dev_active_banner', lang)}</span>
                    </div>
                </div>
                """
            )
            col_rev1, col_rev2 = st.columns([4, 1])
            with col_rev2:
                if st.button(t("dev_mode_btn_revoke", lang), key="btn_revoke_dev_uploader", use_container_width=True):
                    st.session_state.local_dev_token = None
                    st.rerun()
        else:
            render_trusted_html(
                f"""
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px 16px; margin-bottom: 12px;">
                    <div style="display: flex; align-items: center; gap: 8px; color: #1e293b; font-size: 0.85rem; font-weight: 700; margin-bottom: 4px;">
                        {get_svg_icon('shield_check', size=16, color='#64748b')}
                        <span>{t('auth_notice_demo_mode_title', lang)}</span>
                    </div>
                    <div style="color: #64748b; font-size: 0.78rem; line-height: 1.4; margin-bottom: 6px;">
                        {t('auth_notice_demo_mode_desc', lang)}
                    </div>
                </div>
                """
            )
            if not local_bound:
                st.caption(t("dev_mode_err_public_binding", lang))
            elif not configured_secret:
                st.caption(t("dev_mode_err_no_secret_env", lang))
            else:
                col_auth1, col_auth2 = st.columns([3, 1])
                with col_auth1:
                    v3_secret_input = st.text_input(
                        t("dev_mode_secret_input", lang),
                        type="password",
                        placeholder=t("dev_mode_secret_placeholder", lang),
                        key="v3_dev_secret_input_field",
                        label_visibility="collapsed",
                    )
                with col_auth2:
                    if st.button(t("dev_mode_btn_authorize", lang), key="btn_v3_auth_submit", use_container_width=True):
                        if v3_secret_input and configured_secret and hmac.compare_digest(v3_secret_input, configured_secret):
                            st.session_state.local_dev_token = v3_secret_input
                            st.success(t("dev_mode_success_auth", lang))
                            st.rerun()
                        else:
                            st.error(t("dev_mode_err_invalid", lang))

        uploaded_file = st.file_uploader(
            t("uploader_label", lang),
            type=["csv"],
            help=t("uploader_help", lang),
            key="v3_file_uploader",
        )
        if uploaded_file is not None:
            if uploaded_file.size > 10 * 1024 * 1024:
                st.error(t("err_file_size", lang))
            else:
                bytes_data = uploaded_file.getvalue()
                with st.spinner(t("spinner_validating_csv", lang)):
                    try:
                        load_dataset_from_bytes(bytes_data, uploaded_file.name)
                        st.session_state.uploader_has_error = False
                        st.success(t("msg_csv_success", lang, name=uploaded_file.name))
                        st.rerun()
                    except RowLimitExceededError as exc:
                        st.session_state.uploader_has_error = True
                        st.error(t("err_row_limit_title", lang))
                        st.markdown(t("err_row_limit_desc", lang, name=uploaded_file.name, rows=exc.row_count))
                    except ValueError as exc:
                        st.session_state.uploader_has_error = True
                        err_text = str(exc)
                        if "UNAUTHENTICATED_DEMO_RESTRICTION" in err_text:
                            st.error(t("err_unauthenticated_demo_title", lang))
                            st.markdown(t("err_unauthenticated_demo_desc", lang))
                        elif "LOCAL_TESTING_REJECTED_PUBLIC_BINDING" in err_text:
                            st.error(t("err_local_public_binding_title", lang))
                            st.markdown(t("err_local_public_binding_desc", lang))
                        elif "missing required columns" in err_text.lower():
                            st.error(t("err_csv_missing_columns_title", lang))
                            st.markdown(t("err_csv_missing_columns_desc", lang, columns=err_text))
                        else:
                            st.error(t("err_csv_parse", lang, error=err_text))
                    except Exception as exc:
                        st.session_state.uploader_has_error = True
                        st.error(t("err_csv_parse", lang, error=exc))

    # -------------------------------------------------------------
    # Card 2: موافقة على تقرير الأرباح (Human Approval Governance Card)
    # -------------------------------------------------------------
    pending = st.session_state.get("pending_approval")
    has_approval = bool(pending)

    if not has_approval:
        render_trusted_html(f"""
        <div style="background: #ffffff; border: 1px solid #e8e5df; border-radius: 14px; padding: 22px 24px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
                <div style="display: flex; align-items: center; gap: 14px;">
                    <div style="background: #ecfdf5; border: 1px solid #a7f3d0; padding: 10px; border-radius: 10px; color: #059669; display: inline-flex; align-items: center; justify-content: center;">
                        {get_svg_icon('shield_check', size=24, color='#059669')}
                    </div>
                    <div>
                        <div style="font-weight: 800; font-size: 1.05rem; color: #0f172a;">{t('ref_approval_idle_title', lang)}</div>
                        <div style="font-size: 0.82rem; color: #475569; margin-top: 2px;">{t('ref_approval_idle_desc', lang)}</div>
                        <div style="font-size: 0.74rem; color: #64748b; margin-top: 1px;">{t('ref_approval_report_desc', lang)}</div>
                    </div>
                </div>
                <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 4px;">
                    <div class="status-badge badge-success" style="padding: 6px 12px; font-weight: 700;">
                        {get_svg_icon('check_circle', size=14, color='#059669')}
                        <span>{t('ref_approval_status_idle', lang)}</span>
                    </div>
                    <div style="font-size: 0.72rem; color: #94a3b8;">{format_current_date(lang)}</div>
                </div>
            </div>
        </div>
        """)
    else:
        report_title = pending.get("title", t("lbl_report", lang))
        render_trusted_html(f"""
        <div style="background: #ffffff; border: 1px solid #e8e5df; border-radius: 14px; padding: 22px 24px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; margin-bottom: 8px;">
                <div style="display: flex; align-items: center; gap: 14px;">
                    <div style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 10px; border-radius: 10px; color: #0f172a; display: inline-flex; align-items: center; justify-content: center;">
                        {get_svg_icon('file_spreadsheet', size=24, color='#0f172a')}
                    </div>
                    <div>
                        <div style="font-weight: 800; font-size: 1.05rem; color: #0f172a;">{t('ref_approval_card_title', lang)}</div>
                        <div style="font-size: 0.82rem; color: #475569; margin-top: 2px;">{report_title}</div>
                        <div style="font-size: 0.74rem; color: #64748b; margin-top: 1px;">{t('ref_approval_report_desc', lang)}</div>
                    </div>
                </div>
                <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 4px;">
                    <div class="status-badge badge-warning" style="padding: 6px 12px; font-weight: 700;">
                        {get_svg_icon('clock', size=14, color='#d97706')}
                        <span>{t('ref_pending_review', lang)}</span>
                    </div>
                    <div style="font-size: 0.72rem; color: #94a3b8;">{t('ref_approval_created_date', lang)}</div>
                </div>
            </div>
        </div>
        """)

    if has_approval:
        col_app_v3, col_deny_v3 = st.columns([1, 1])
        if col_app_v3.button(t("btn_approve_report", lang), use_container_width=True, key="btn_app_rep_v3"):
            with st.spinner(t("spinner_authorizing_report", lang)):
                auth_service = AuthorizationService.get_default_service()
                ticket = auth_service.issue_ticket(
                    user_id=st.session_state.user_id,
                    session_id=st.session_state.session_id,
                    tool_name="generate_report",
                    params=pending["args"],
                )

                async def execute_approved_report_v3():
                    client = RetailMindMCPClient(caller_user_id=st.session_state.user_id)
                    async with client:
                        call_args = dict(pending["args"], auth_ticket=ticket)
                        return await client.call_tool("generate_report", call_args)

                result = asyncio.run(execute_approved_report_v3())
                st.session_state.pending_approval = None
                if result.get("status") == "success":
                    st.success(t("msg_report_success", lang, path=result.get("file_path"), size=result.get("file_size_bytes")))
                    st.session_state.last_generated_report = result.get("file_path")
                else:
                    st.error(t("msg_report_failed", lang, error=result.get("message")))
                st.rerun()

        if col_deny_v3.button(t("btn_deny_report", lang), use_container_width=True, key="btn_deny_rep_v3"):
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
            st.rerun()

    # -------------------------------------------------------------
    # Card 3: سجل التدقيق (Security & Audit Trail Summary Table)
    # -------------------------------------------------------------
    audit_logger = AuditLogger.get_default_logger()
    events = audit_logger.query_events(user_id=st.session_state.user_id, limit=5)

    rows_html = []
    merchant_user_label = t("ref_default_merchant", lang)

    if events:
        for ev in events[:5]:
            ts = ev.get("timestamp", "")
            time_part = ts.split("T")[1][:5] if "T" in ts else ts[-8:-3] if len(ts) >= 8 else ""
            tool = ev.get("tool_name", "")
            action = ev.get("action_type", "")
            decision = ev.get("decision", "ALLOWED")
            dot_color = "#10b981" if decision == "ALLOWED" else "#d97706"
            icon_svg = get_svg_icon('file_up', size=15, color='#059669') if action == "READ" else get_svg_icon('shield_check', size=15, color='#d97706')

            rows_html.append(f"""
            <tr style="border-bottom: 1px solid #f1f5f9;">
                <td style="padding: 12px 14px; font-size: 0.82rem; color: #64748b;">
                    <span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:{dot_color};margin-left:5px;margin-right:5px;"></span>
                    {time_part}
                </td>
                <td style="padding: 12px 14px; font-size: 0.82rem; color: #0f172a; display: flex; align-items: center; gap: 6px;">
                    {icon_svg}
                    <span>{tool}</span>
                </td>
                <td style="padding: 12px 14px; font-size: 0.82rem; color: #475569;">{ev.get('reason_code') or tool}</td>
                <td style="padding: 12px 14px; font-size: 0.82rem; color: #0f172a; font-weight: 600;">{merchant_user_label}</td>
            </tr>
            """)
    else:
        rows_html.append(f"""
        <tr>
            <td colspan="4" style="padding: 24px 14px; text-align: center; color: #64748b; font-size: 0.85rem;">
                {t('info_no_events', lang)}
            </td>
        </tr>
        """)

    render_trusted_html(f"""
    <div style="background: #ffffff; border: 1px solid #e8e5df; border-radius: 14px; padding: 22px 24px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 16px;">
            <div style="color: #059669; display: flex; align-items: center;">
                {get_svg_icon('list_ordered', size=22, color='#059669')}
            </div>
            <div style="font-weight: 800; font-size: 1.10rem; color: #0f172a;">{t('ref_audit_table_title', lang)}</div>
        </div>
        <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; text-align: inherit;">
                <thead>
                    <tr style="border-bottom: 1.5px solid #e2e8f0; color: #64748b; font-size: 0.80rem;">
                        <th style="padding: 10px 14px; text-align: inherit;">{t('ref_audit_col_time', lang)}</th>
                        <th style="padding: 10px 14px; text-align: inherit;">{t('ref_audit_col_event', lang)}</th>
                        <th style="padding: 10px 14px; text-align: inherit;">{t('ref_audit_col_details', lang)}</th>
                        <th style="padding: 10px 14px; text-align: inherit;">{t('ref_audit_col_user', lang)}</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(rows_html)}
                </tbody>
            </table>
        </div>
    </div>
    """)

    # Detailed Data Inspection Expander
    if dataset:
        with st.expander(f"🔍 {t('preview_valid_data', lang)} ({valid_rows_count:,} {t('lbl_valid_rows', lang)})", expanded=False):
            st.dataframe(dataset.valid_df.head(25), use_container_width=True)
            if len(dataset.quarantined_df) > 0:
                st.subheader(t("preview_quarantined_data", lang))
                st.dataframe(dataset.quarantined_df, use_container_width=True)


# -----------------------------------------------------------------------------
# View 4: 🧠 Persistent Memory Explorer
# -----------------------------------------------------------------------------
elif active_view == "memory":
    st.title(t("memory_title", lang))
    st.caption(t("memory_caption", lang))

    render_trusted_html(
        f"""
        <div style="margin-bottom: 16px;">
            <span class="status-badge badge-success">
                <span style="display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: #10b981;"></span>
                <span>{t('ref_memory_status', lang)}</span>
            </span>
        </div>
        """
    )

    mem_manager = SQLiteMemoryManager()
    if not st.session_state.dataset_fingerprint:
        st.info(t("info_memory_no_dataset", lang))
    else:
        records = mem_manager.retrieve_relevant_context(
            user_id=st.session_state.user_id,
            dataset_fingerprint=st.session_state.dataset_fingerprint,
            limit=10,
        )

        if st.query_params.get("dev_mode") == "1":
            st.markdown(t("lbl_active_user", lang, user_id=st.session_state.user_id))
            st.markdown(t("lbl_dataset_fingerprint", lang, fingerprint=st.session_state.dataset_fingerprint))
            st.markdown(t("lbl_memories_found", lang, count=len(records)))
        else:
            fn = st.session_state.active_filename or "Dataset"
            st.markdown(f"**{t('ref_default_merchant', lang)}** · {fn}")
            st.markdown(t("lbl_memories_found", lang, count=len(records)))

        if not records:
            st.info(t("info_no_memories", lang))
        else:
            for idx, r in enumerate(records, 1):
                rec_date = r.get("created_at") or r.get("timestamp") or ""
                header = t("memory_item_expander", lang, idx=idx, query=r.get("query"), date=rec_date)
                with st.expander(header, expanded=(idx == 1)):
                    if st.query_params.get("dev_mode") == "1":
                        st.markdown(t("lbl_task_id", lang, task_id=r.get("task_id") or "N/A"))
                    st.markdown(t("lbl_verified_summary", lang, summary=r.get("summary")))
                    if r.get("tool_calls"):
                        if st.query_params.get("dev_mode") == "1":
                            st.json(r.get("tool_calls"))
                        else:
                            tc = r.get("tool_calls")
                            if isinstance(tc, list):
                                st.markdown(f"**{t('ref_verified_operations_title', lang)}:**")
                                for call in tc:
                                    tool_nm = call.get("tool") if isinstance(call, dict) else str(call)
                                    st.markdown(f"- `{tool_nm}` ✓")
                            elif isinstance(tc, dict):
                                st.markdown(f"**{t('ref_verified_operations_title', lang)}:**")
                                for k, v in tc.items():
                                    st.markdown(f"- **{k}:** {v}")
                            else:
                                st.markdown(f"**{t('ref_verified_operations_title', lang)}:** `{tc}`")


# -----------------------------------------------------------------------------
# View 5: 🛡️ Security & Audit Trail
# -----------------------------------------------------------------------------
elif active_view == "audit":
    if not check_developer_authorization():
        # Level 2 Isolation: 403 Forbidden Screen for Unauthorized Users
        render_trusted_html(
            f"""
            <div style="background: #ffffff; border: 1px solid #fee2e2; border-radius: 14px; padding: 36px 24px; margin: 24px 0; box-shadow: 0 4px 16px rgba(239, 68, 68, 0.06); text-align: center;">
                <div style="background: #fef2f2; border: 1px solid #fecaca; width: 68px; height: 68px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 16px; color: #dc2626;">
                    {get_svg_icon('shield_check', size=34, color='#dc2626')}
                </div>
                <div style="font-size: 1.45rem; font-weight: 800; color: #0f172a; margin-bottom: 8px;">{t('forbidden_title', lang)}</div>
                <div style="color: #64748b; font-size: 0.92rem; max-width: 600px; margin: 0 auto 20px auto; line-height: 1.6;">
                    {t('forbidden_desc', lang)}
                </div>
            </div>
            """
        )

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if not is_local_interface_bound():
                st.caption(t("dev_mode_err_public_binding", lang))
                if st.button(t("forbidden_btn_return", lang), use_container_width=True, key="btn_return_overview"):
                    st.session_state.current_view_key = "overview"
                    try:
                        st.query_params["view"] = "overview"
                    except Exception:
                        pass
                    st.rerun()
            else:
                with st.container(border=True):
                    st.markdown(f"#### {t('forbidden_login_box_title', lang)}")
                    dev_pw = st.text_input(
                        t("dev_mode_secret_input", lang),
                        type="password",
                        placeholder=t("dev_mode_secret_placeholder", lang),
                        key="forbidden_page_secret_input",
                    )
                    btn_col1, btn_col2 = st.columns([1, 1])
                    with btn_col1:
                        if st.button(t("forbidden_login_btn", lang), use_container_width=True, type="primary", key="btn_unlock_dev"):
                            configured_secret = os.getenv("RETAILMIND_LOCAL_DEV_SECRET")
                            if dev_pw and configured_secret and hmac.compare_digest(dev_pw, configured_secret):
                                st.session_state.local_dev_token = dev_pw
                                st.session_state.current_view_key = "audit"
                                st.success(t("dev_mode_success_auth", lang))
                                st.rerun()
                            else:
                                st.error(t("dev_mode_err_invalid", lang))
                    with btn_col2:
                        if st.button(t("forbidden_btn_return", lang), use_container_width=True, key="btn_return_overview"):
                            st.session_state.current_view_key = "overview"
                            try:
                                st.query_params["view"] = "overview"
                            except Exception:
                                pass
                            st.rerun()
    else:
        st.title(t("audit_title", lang))
        st.caption(t("audit_caption", lang))

        audit_logger = AuditLogger.get_default_logger()
        events = audit_logger.query_events(user_id=st.session_state.user_id, limit=50)

        db_path_info = t("lbl_db_location", lang, path=audit_logger.db_path)
        render_trusted_html(
            f"""
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; margin-bottom: 16px;">
                <div style="color: #64748b; font-size: 0.82rem;">{db_path_info}</div>
                <div class="status-badge badge-info">{t("lbl_recent_events", lang, count=len(events))}</div>
            </div>
            """
        )

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

"""RetailMind AI — Centralized Internationalization (i18n) & Bilingual Support.

Provides:
1. Complete translation dictionary for all user-facing strings (English and Arabic).
2. Scoped RTL/LTR layout styles for Streamlit.
3. Translation helper functions with string formatting support.
"""

from typing import Any, Dict

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    # -------------------------------------------------------------------------
    # App Shell & Navigation
    # -------------------------------------------------------------------------
    "app_title": {
        "en": "RetailMind AI — Autonomous Retail Analytics",
        "ar": "RetailMind AI — تحليلات مبيعات التجزئة الذكية",
    },
    "app_caption": {
        "en": "Autonomous Retail Analytics Agent",
        "ar": "وكيل ذكي ومستقل لتحليل بيانات مبيعات التجزئة",
    },
    "status_model": {
        "en": "● Gemini 3.1 Flash-Lite",
        "ar": "● Gemini 3.1 Flash-Lite",
    },
    "status_mcp": {
        "en": "● MCP v2 (stdio)",
        "ar": "● بروتوكول MCP v2 (stdio)",
    },
    "status_policy": {
        "en": "● ask_on_write",
        "ar": "● سياسة ask_on_write",
    },
    "nav_overview": {
        "en": "📊 Overview Dashboard",
        "ar": "📊 لوحة المؤشرات العامة",
    },
    "nav_agent": {
        "en": "💬 AI Sales Agent (Gemini + MCP)",
        "ar": "💬 وكيل المبيعات الذكي (Gemini + MCP)",
    },
    "nav_dataset": {
        "en": "📁 Dataset Ingestion & Validation",
        "ar": "📁 استيراد وتدقيق البيانات",
    },
    "nav_memory": {
        "en": "🧠 Persistent Memory Explorer",
        "ar": "🧠 مستكشف الذاكرة الدائمة",
    },
    "nav_audit": {
        "en": "🛡️ Security & Audit Trail",
        "ar": "🛡️ سجل الأمان والتدقيق",
    },
    "nav_menu": {
        "en": "Navigation Menu",
        "ar": "قائمة التنقل",
    },
    "lang_toggle_label": {
        "en": "Language / اللغة",
        "ar": "اللغة / Language",
    },
    "lang_en": {
        "en": "English",
        "ar": "English",
    },
    "lang_ar": {
        "en": "العربية",
        "ar": "العربية",
    },

    # -------------------------------------------------------------------------
    # Sidebar
    # -------------------------------------------------------------------------
    "active_dataset_header": {
        "en": "📁 Active Dataset",
        "ar": "📁 مجموعة البيانات النشطة",
    },
    "dataset_loaded_label": {
        "en": "**Loaded:** `{filename}`",
        "ar": "**تم التحميل:** `{filename}`",
    },
    "fingerprint_label": {
        "en": "Fingerprint: `{fp}...`",
        "ar": "بصمة البيانات: `{fp}...`",
    },
    "no_dataset_loaded": {
        "en": "No dataset loaded yet.",
        "ar": "لم يتم تحميل أي بيانات بعد.",
    },
    "btn_load_sample": {
        "en": "⚡ Load Synthetic Sample Data",
        "ar": "⚡ تحميل بيانات مبيعات تجريبية",
    },
    "btn_load_sample_no_cost": {
        "en": "⚡ Load Sample Data (No Cost)",
        "ar": "⚡ تحميل بيانات تجريبية (بدون تكلفة)",
    },
    "spinner_load_sample": {
        "en": "Ingesting sample retail dataset...",
        "ar": "جارٍ استيراد بيانات المبيعات التجريبية...",
    },
    "spinner_load_sample_no_cost": {
        "en": "Ingesting missing-cost retail dataset...",
        "ar": "جارٍ استيراد بيانات المبيعات بدون تكلفة...",
    },
    "guardrails_header": {
        "en": "⚙️ Guardrails & Runtime",
        "ar": "⚙️ حواجز الأمان وبيئة التشغيل",
    },
    "lbl_session": {
        "en": "Session: {session}",
        "ar": "الجلسة: {session}",
    },
    "lbl_user": {
        "en": "User: {user}",
        "ar": "المستخدم: {user}",
    },
    "lbl_budget_cap": {
        "en": "Budget Cap: ${cap:.2f}/task",
        "ar": "سقف الميزانية: ${cap:.2f}/مهمة",
    },
    "lbl_max_turns": {
        "en": "Max Turns: {turns}",
        "ar": "الحد الأقصى للجولات: {turns}",
    },
    "btn_reset_chat": {
        "en": "🧹 Reset Conversation",
        "ar": "🧹 إعادة تعيين المحادثة",
    },

    # -------------------------------------------------------------------------
    # View 1: 📊 Overview Dashboard
    # -------------------------------------------------------------------------
    "overview_title": {
        "en": "📊 Executive Sales Overview",
        "ar": "📊 النظرة العامة التنفيذية للمبيعات",
    },
    "overview_caption": {
        "en": "Real-time deterministic KPIs and trend analysis computed directly from the active dataset.",
        "ar": "مؤشرات أداء حتمية وتحليلات اتجاهات فورية محسوبة مباشرة من البيانات النشطة.",
    },
    "warn_no_dataset": {
        "en": "⚠️ No dataset loaded. Please upload a CSV file or load the sample dataset in the sidebar.",
        "ar": "⚠️ لم يتم تحميل بيانات. يرجى رفع ملف CSV أو تحميل العينة التجريبية من القائمة الجانبية.",
    },
    "err_zero_rows": {
        "en": "Active dataset has 0 valid rows.",
        "ar": "مجموعة البيانات النشطة تحتوي على 0 أسطر صالحة.",
    },
    "kpi_net_revenue": {
        "en": "Net Revenue",
        "ar": "صافي المبيعات",
    },
    "kpi_revenue_delta": {
        "en": "Verified Ground Truth",
        "ar": "قيمة حسابية مؤكدة",
    },
    "kpi_units_sold": {
        "en": "Units Sold",
        "ar": "الوحدات المباعة",
    },
    "kpi_units_delta": {
        "en": "Total Volume",
        "ar": "إجمالي حجم المبيعات",
    },
    "kpi_total_orders": {
        "en": "Total Orders",
        "ar": "إجمالي الطلبات",
    },
    "kpi_orders_delta": {
        "en": "Completed Transactions",
        "ar": "العمليات المكتملة",
    },
    "kpi_gross_profit": {
        "en": "Gross Profit",
        "ar": "إجمالي الربح",
    },
    "kpi_profit_delta_avail": {
        "en": "Unit Cost Available",
        "ar": "تكلفة الوحدة متوفرة",
    },
    "kpi_profit_unavail": {
        "en": "UNAVAILABLE",
        "ar": "غير متوفر",
    },
    "kpi_profit_delta_unavail": {
        "en": "No unit_cost column",
        "ar": "عمود unit_cost غير موجود",
    },
    "kpi_gross_margin": {
        "en": "Gross Margin",
        "ar": "هامش الربح الإجمالي",
    },
    "kpi_margin_delta_avail": {
        "en": "Profitability Ratio",
        "ar": "نسبة الربحية",
    },
    "kpi_margin_na": {
        "en": "N/A",
        "ar": "غير متاح",
    },
    "kpi_margin_delta_na": {
        "en": "Requires cost data",
        "ar": "يتطلب بيانات التكلفة",
    },
    "chart_revenue_by_date": {
        "en": "📈 Revenue by Date",
        "ar": "📈 المبيعات بحسب التاريخ",
    },
    "chart_top_products": {
        "en": "🏆 Top 5 Products by Revenue",
        "ar": "🏆 أعلى 5 منتجات حسب الإيرادات",
    },
    "chart_revenue_by_category": {
        "en": "📦 Revenue by Category",
        "ar": "📦 المبيعات بحسب الفئة",
    },
    "info_no_category": {
        "en": "No category column present in dataset.",
        "ar": "عمود الفئة (category) غير متوفر في مجموعة البيانات.",
    },
    "chart_revenue_by_region": {
        "en": "🌍 Revenue by Region",
        "ar": "🌍 المبيعات بحسب المنطقة",
    },
    "info_no_region": {
        "en": "No region column present in dataset.",
        "ar": "عمود المنطقة (region) غير متوفر في مجموعة البيانات.",
    },

    # -------------------------------------------------------------------------
    # View 2: 💬 AI Sales Agent (Gemini + MCP)
    # -------------------------------------------------------------------------
    "agent_title": {
        "en": "💬 RetailMind AI Conversational Agent",
        "ar": "💬 وكيل المبيعات الذكي RetailMind",
    },
    "agent_caption": {
        "en": "Powered by Google Gemini 3.1 Flash-Lite, official Model Context Protocol (MCP v2), and SQLite memory.",
        "ar": "مدعوم بنموذج Google Gemini 3.1 Flash-Lite، وبروتوكول MCP v2 الرسمي، وذاكرة SQLite الدائمة.",
    },
    "warn_agent_no_dataset": {
        "en": "⚠️ Please load or upload a dataset before asking analytical questions.",
        "ar": "⚠️ يرجى تحميل أو رفع مجموعة بيانات قبل طرح الأسئلة التحليلية.",
    },
    "suggested_queries_label": {
        "en": "**Suggested Analytical Queries:**",
        "ar": "**استفسارات تحليلية مقترحة:**",
    },
    "btn_prompt_revenue": {
        "en": "📊 Net Revenue & Margin",
        "ar": "📊 صافي الإيرادات وهامش الربح",
    },
    "query_revenue": {
        "en": "What was our total net revenue, profit, and gross margin for the dataset?",
        "ar": "ما هو إجمالي صافي الإيرادات، والربح، وهامش الربح الإجمالي في مجموعة البيانات؟",
    },
    "btn_prompt_top_prods": {
        "en": "🏆 Top 3 Products",
        "ar": "🏆 أعلى 3 منتجات",
    },
    "query_top_prods": {
        "en": "Which are our top 3 products by revenue and what is their revenue share?",
        "ar": "ما هي أعلى 3 منتجات من حيث الإيرادات وما هي حصتها النسبية من الإجمالي؟",
    },
    "btn_prompt_compare": {
        "en": "📅 Jan vs Feb Comparison",
        "ar": "📅 مقارنة يناير مع فبراير",
    },
    "query_compare": {
        "en": "Compare sales performance between January 2026 and February 2026.",
        "ar": "قارن أداء المبيعات بين شهري يناير 2026 وفبراير 2026.",
    },
    "btn_prompt_report": {
        "en": "📑 Generate Executive Report",
        "ar": "📑 إنشاء تقرير تنفيذي",
    },
    "query_report": {
        "en": "Please generate an executive sales performance report.",
        "ar": "يرجى إنشاء تقرير تنفيذي شامل ومفصل لأداء المبيعات.",
    },
    "transparency_header": {
        "en": "🔍 Execution Transparency — {tools} tool(s) | {turns} turn(s) | ${cost:.6f} USD",
        "ar": "🔍 شفافية التنفيذ — {tools} أدوات | {turns} جولات | ${cost:.6f} دولار أمريكي",
    },
    "lbl_transport": {
        "en": "**Execution Transport:** `{transport}` (stdio subprocess)",
        "ar": "**وسيط التنفيذ:** `{transport}` (عملية فرعية عبر stdio)",
    },
    "lbl_stop_reason": {
        "en": "**Stop Reason:** `{reason}`",
        "ar": "**سبب انتهاء المهمة:** `{reason}`",
    },
    "lbl_tokens_cost": {
        "en": "**Total Tokens:** `{tokens}` (Paid-Tier Cost: `${cost:.6f}` USD)",
        "ar": "**إجمالي التوكنات:** `{tokens}` (تكلفة الفئة المدفوعة: `${cost:.6f}` دولار)",
    },
    "caption_budget_pct": {
        "en": "Budget consumed: {pct:.1f}% of ${cap:.2f} limit",
        "ar": "الميزانية المستهلكة: {pct:.1f}% من سقف ${cap:.2f}",
    },
    "tool_audit_title": {
        "en": "**Tool Calls Audit:**",
        "ar": "**سجل استدعاء الأدوات الفعلي:**",
    },
    "tool_audit_line": {
        "en": "- Turn {turn}: `{tool}` via transport `{transport}` → **{status}**",
        "ar": "- الجولة {turn}: أداة `{tool}` عبر `{transport}` ← **{status}**",
    },
    "approval_req_title": {
        "en": "⚠️ **Human Authorization Required (ask_on_write Policy)**",
        "ar": "⚠️ **مطلوب تفويض بشري صريح (سياسة ask_on_write)**",
    },
    "approval_req_desc": {
        "en": "The agent requested to write an executive report titled: **{title}**",
        "ar": "طلب الوكيل كتابة وتصدير تقرير تنفيذي بعنوان: **{title}**",
    },
    "approval_req_info": {
        "en": "No report file has been written to disk. Please explicitly approve or deny this write operation:",
        "ar": "لم يتم إنشاء أو تعديل أي ملف على القرص بعد. يرجى الموافقة الصريحة أو رفض عملية الكتابة:",
    },
    "btn_approve_report": {
        "en": "✅ Approve & Export Report",
        "ar": "✅ موافقة وتصدير التقرير",
    },
    "btn_deny_report": {
        "en": "❌ Deny Write Action",
        "ar": "❌ رفض عملية الكتابة",
    },
    "spinner_authorizing_report": {
        "en": "Authorizing and exporting report through MCP server...",
        "ar": "جارٍ التحقق وتصدير التقرير عبر خادم MCP...",
    },
    "msg_report_success": {
        "en": "Report exported successfully: `{path}` ({size} bytes)",
        "ar": "تم تصدير التقرير بنجاح: `{path}` ({size} بايت)",
    },
    "chat_report_approved_content": {
        "en": "✅ **Report Exported:** `{path}`\n\nThe executive sales report has been verified and saved to disk with explicit user approval.",
        "ar": "✅ **تم تصدير التقرير:** `{path}`\n\nتم التحقق من التقرير التنفيذي وحفظه على القرص بموافقة المستخدم الصريحة.",
    },
    "msg_report_failed": {
        "en": "Report generation failed: {error}",
        "ar": "فشلت عملية إنشاء التقرير: {error}",
    },
    "chat_report_denied_content": {
        "en": "❌ **Action Denied:** The write operation `generate_report` was rejected by the user. No file was created.",
        "ar": "❌ **تم رفض العملية:** تم رفض عملية الكتابة `generate_report` من قِبل المستخدم. لم يتم إنشاء أي ملف.",
    },
    "btn_download_report": {
        "en": "📥 Download Approved Report ({filename})",
        "ar": "📥 تحميل التقرير المعتمد ({filename})",
    },
    "chat_input_prompt": {
        "en": "Ask RetailMind AI about your sales data...",
        "ar": "اطرح سؤالاً على RetailMind AI حول بيانات مبيعاتك...",
    },
    "spinner_agent_thinking": {
        "en": "RetailMind AI is reasoning and invoking MCP tools...",
        "ar": "الوكيل يستنتج الإجابة ويستدعي أدوات MCP الحقيقية...",
    },

    # -------------------------------------------------------------------------
    # View 3: 📁 Dataset Ingestion & Validation
    # -------------------------------------------------------------------------
    "ingestion_title": {
        "en": "📁 CSV Ingestion & Data Quality Audit",
        "ar": "📁 رفع ملفات CSV وتدقيق جودة البيانات",
    },
    "ingestion_caption": {
        "en": "Upload sales data with automated formula sanitization, schema audit, and row quarantining.",
        "ar": "رفع بيانات المبيعات مع التعقيم التلقائي ضد حقن الصيغ وتدقيق المخطط وعزل الأسطر المعيبة.",
    },
    "uploader_label": {
        "en": "Upload Retail CSV File (Max 10MB, Max 50,000 rows)",
        "ar": "رفع ملف مبيعات بصيغة CSV (الحد الأقصى 10 ميجابايت، 50,000 سطر)",
    },
    "uploader_help": {
        "en": "Required columns: date, product, quantity, unit_price. Optional: unit_cost, category, region, order_id.",
        "ar": "الأعمدة الإلزامية: date, product, quantity, unit_price. الاختيارية: unit_cost, category, region, order_id.",
    },
    "err_file_size": {
        "en": "File size exceeds 10MB limit.",
        "ar": "حجم الملف يتجاوز الحد الأقصى المسموح به (10 ميجابايت).",
    },
    "spinner_validating_csv": {
        "en": "Validating and parsing CSV...",
        "ar": "جارٍ تدقيق وتحليل ملف CSV...",
    },
    "msg_csv_success": {
        "en": "Successfully processed `{name}`!",
        "ar": "تمت معالجة وتدقيق `{name}` بنجاح!",
    },
    "err_csv_parse": {
        "en": "Error parsing dataset: {error}",
        "ar": "خطأ أثناء تحليل مجموعة البيانات: {error}",
    },
    "audit_summary_title": {
        "en": "📋 Dataset Audit Summary",
        "ar": "📋 ملخص تدقيق جودة البيانات",
    },
    "metric_total_rows": {
        "en": "Total Rows Ingested",
        "ar": "إجمالي الأسطر المستوردة",
    },
    "metric_valid_rows": {
        "en": "Valid Rows",
        "ar": "الأسطر الصالحة",
    },
    "metric_quarantined_rows": {
        "en": "Quarantined Rows",
        "ar": "الأسطر المعزولة",
    },
    "metric_duplicates": {
        "en": "Duplicates Detected",
        "ar": "الأسطر المكررة",
    },
    "warn_no_cost_column": {
        "en": "⚠️ **Notice:** This dataset lacks a `unit_cost` column. Net revenue and units sold will compute normally, but gross profit and margins will be marked UNAVAILABLE.",
        "ar": "⚠️ **تنبيه:** تفتقر هذه البيانات لعمود `unit_cost`. سيتم حساب صافي المبيعات والكميات بشكل طبيعي، بينما ستُصنف الأرباح والهوامش كـ 'غير متوفر'.",
    },
    "success_has_cost_column": {
        "en": "✅ **Cost Data Detected:** Unit cost information is available for profit and gross margin analysis.",
        "ar": "✅ **تم اكتشاف بيانات التكلفة:** معلومات تكلفة الوحدة متوفرة لتحليل الأرباح وهامش الربح.",
    },
    "preview_valid_data": {
        "en": "🔍 Valid Data Preview",
        "ar": "🔍 معاينة البيانات الصالحة",
    },
    "preview_quarantined_data": {
        "en": "⚠️ Quarantined Invalid Rows",
        "ar": "⚠️ الأسطر المعيبة المعزولة",
    },

    # -------------------------------------------------------------------------
    # View 4: 🧠 Persistent Memory Explorer
    # -------------------------------------------------------------------------
    "memory_title": {
        "en": "🧠 Persistent SQLite Analytical Memory",
        "ar": "🧠 الذاكرة التحليلية الدائمة في SQLite",
    },
    "memory_caption": {
        "en": "Inspect verified analytical findings stored persistently in SQLite. Memories survive process restarts and are isolated by user and dataset fingerprint.",
        "ar": "استعراض النتائج التحليلية المؤكدة والمحفوظة في SQLite. تبقى الذاكرة بعد إعادة التشغيل وتُعزل حسب المستخدم وبصمة البيانات.",
    },
    "info_memory_no_dataset": {
        "en": "Please load a dataset to view associated memories.",
        "ar": "يرجى تحميل مجموعة بيانات لعرض الذاكرة المرتبطة بها.",
    },
    "lbl_active_user": {
        "en": "**Active User ID:** `{user_id}`",
        "ar": "**معرف المستخدم النشط:** `{user_id}`",
    },
    "lbl_dataset_fingerprint": {
        "en": "**Dataset SHA-256 Fingerprint:** `{fingerprint}`",
        "ar": "**بصمة البيانات SHA-256:** `{fingerprint}`",
    },
    "lbl_memories_found": {
        "en": "**Verified Memories Found:** `{count}`",
        "ar": "**عدد النتائج المحققة المسجلة:** `{count}`",
    },
    "info_no_memories": {
        "en": "No prior memories recorded for this specific dataset. Ask the AI agent queries to generate verified findings!",
        "ar": "لا توجد نتائج سابقة مسجلة لهذه البيانات تحديداً. اطرح أسئلة على الوكيل لتسجيل استنتاجات مؤكدة!",
    },
    "memory_item_expander": {
        "en": "Memory #{idx}: {query} ({date})",
        "ar": "ذاكرة #{idx}: {query} ({date})",
    },
    "lbl_task_id": {
        "en": "**Task ID:** `{task_id}`",
        "ar": "**معرف المهمة:** `{task_id}`",
    },
    "lbl_verified_summary": {
        "en": "**Verified Summary:**\n{summary}",
        "ar": "**الملخص المحقق:**\n{summary}",
    },

    # -------------------------------------------------------------------------
    # View 5: 🛡️ Security & Audit Trail
    # -------------------------------------------------------------------------
    "audit_title": {
        "en": "🛡️ Security Audit Log",
        "ar": "🛡️ سجل الأمان والتدقيق",
    },
    "audit_caption": {
        "en": "Immutable append-only audit trail recorded in SQLite (WAL mode). Logs all tool executions, permission gates, and adversarial attack blocks.",
        "ar": "سجل تدقيق غير قابل للتعديل مسجل في SQLite بنمط WAL. يوثق استدعاء الأدوات، وبوابات التصاريح، وصد الهجمات العدائية.",
    },
    "lbl_db_location": {
        "en": "**Database Location:** `{path}`",
        "ar": "**موقع قاعدة البيانات:** `{path}`",
    },
    "lbl_recent_events": {
        "en": "**Recent Logged Events:** `{count}`",
        "ar": "**الأحداث الأخيرة المسجلة:** `{count}`",
    },
    "info_no_events": {
        "en": "No audit events recorded yet.",
        "ar": "لم يتم تسجيل أي أحداث أمنية بعد.",
    },
    "col_timestamp": {
        "en": "Timestamp (UTC)",
        "ar": "التوقيت (UTC)",
    },
    "col_tool": {
        "en": "Tool",
        "ar": "الأداة",
    },
    "col_action": {
        "en": "Action",
        "ar": "نوع الإجراء",
    },
    "col_decision": {
        "en": "Decision",
        "ar": "القرار",
    },
    "col_outcome": {
        "en": "Outcome",
        "ar": "النتيجة",
    },
    "col_reason": {
        "en": "Reason Code",
        "ar": "رمز السبب",
    },
    "col_transport": {
        "en": "Transport",
        "ar": "وسيط التنفيذ",
    },
    "col_task_id": {
        "en": "Task ID",
        "ar": "معرف المهمة",
    },
}


def t(key: str, lang: str = "en", **kwargs: Any) -> str:
    """Translates a key into the target language with keyword interpolation.
    
    Falls back to English if the key is missing in the target language.
    If the key is not in TRANSLATIONS at all, returns the key itself.
    """
    lang_code = "ar" if lang == "ar" else "en"
    key_dict = TRANSLATIONS.get(key)
    if not key_dict:
        return key

    template = key_dict.get(lang_code) or key_dict.get("en", key)
    if kwargs:
        try:
            return template.format(**kwargs)
        except Exception:
            return template
    return template


def get_layout_css(lang: str) -> str:
    """Returns scoped CSS for bilingual presentation (RTL for Arabic, LTR for English)."""
    if lang == "ar":
        return """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');

        /* Arabic Typography & Layout */
        html, body, [class*="st-"], .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6, label, button, .stCaption, .metric-label, .metric-delta {
            font-family: 'Cairo', 'Segoe UI', Tahoma, Arial, sans-serif !important;
        }

        /* Container Direction & Alignment */
        .main .block-container {
            direction: rtl;
            text-align: right;
        }
        section[data-testid="stSidebar"] {
            direction: rtl;
            text-align: right;
        }

        /* Chat Messages */
        .stChatMessage {
            direction: rtl;
            text-align: right;
        }

        /* Headings & Text */
        .stMarkdown, h1, h2, h3, h4, h5, h6, p, .stCaption {
            text-align: right;
        }

        /* Metric Cards */
        .metric-card {
            text-align: right;
        }
        .metric-label, .metric-delta {
            text-align: right;
        }

        /* Preserve LTR presentation for numbers, monetary values, codes, and paths */
        code, pre, .metric-value, .status-badge, [data-testid="stCodeBlock"] {
            direction: ltr !important;
            text-align: left !important;
            display: inline-block;
            font-family: "Consolas", "Courier New", monospace !important;
        }

        /* DataTables & DataFrames remain legible in standard layout */
        [data-testid="stDataFrame"], [data-testid="stTable"] {
            direction: ltr !important;
            text-align: left !important;
        }

        /* Vega-Lite / Native Charts */
        [data-testid="stVegaLiteChart"], [data-testid="stArrowVegaLiteChart"] {
            direction: ltr !important;
        }

        /* Expanders */
        [data-testid="stExpander"] details summary {
            direction: rtl;
            text-align: right;
        }
        </style>
        """
    else:
        return """
        <style>
        /* Standard English LTR styling */
        .main .block-container {
            direction: ltr;
            text-align: left;
        }
        section[data-testid="stSidebar"] {
            direction: ltr;
            text-align: left;
        }
        .stChatMessage {
            direction: ltr;
            text-align: left;
        }
        .stMarkdown, h1, h2, h3, h4, h5, h6, p, .stCaption {
            text-align: left;
        }
        .metric-card {
            text-align: left;
        }
        .metric-label, .metric-delta {
            text-align: left;
        }
        </style>
        """

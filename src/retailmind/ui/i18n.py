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
    # Short labels for custom HTML nav
    "nav_overview_short": {"en": "الرئيسية",          "ar": "الرئيسية"},
    "nav_agent_short":    {"en": "المحلل الذكي",      "ar": "المحلل الذكي"},
    "nav_dataset_short":  {"en": "البيانات والحوكمة", "ar": "البيانات والحوكمة"},
    "nav_memory_short":   {"en": "الذاكرة",           "ar": "الذاكرة"},
    "nav_audit_short":    {"en": "سجل التدقيق",       "ar": "سجل التدقيق"},
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
    "sidebar_session_dataset": {
        "en": "Active Session Dataset",
        "ar": "بيانات الجلسة النشطة",
    },
    "sidebar_guardrails_settings": {
        "en": "Guardrails & Developer Mode",
        "ar": "حواجز الأمان وبيئة التطوير",
    },
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
    "onboarding_welcome_title": {
        "en": "Welcome to RetailMind AI",
        "ar": "مرحباً بك في منصة RetailMind AI",
    },
    "onboarding_welcome_subtitle": {
        "en": "Autonomous retail intelligence & sales analytics powered by Google Gemini and MCP. Ingest your retail dataset to unlock real-time financial KPIs, anomaly detection, and natural language business insights.",
        "ar": "محرك ذكاء تجزئة مستقل وتحليلات مبيعات متقدمة مدعوم بنموذج Gemini وبروتوكول MCP. قم بتحميل بيانات مبيعاتك للحصول فورياً على مؤشرات أداء مالية دقيقة، وكشف الشذوذ، واستشارات ذكية باللغة الطبيعية.",
    },
    "onboarding_step1_title": {
        "en": "1. Ingest Sales Dataset",
        "ar": "1. استيراد بيانات المبيعات",
    },
    "onboarding_step1_desc": {
        "en": "Upload a retail CSV file (up to 10MB, max 50,000 rows) or immediately load our certified synthetic benchmark dataset.",
        "ar": "ارفع ملف مبيعات بصيغة CSV (حتى 10MB وحد أقصى 50,000 صف) أو ابدأ فوراً بتحميل العينة المرجعية المعتمدة.",
    },
    "onboarding_step2_title": {
        "en": "2. Executive KPIs & Trends",
        "ar": "2. مؤشرات أداء تنفيذية واتجاهات",
    },
    "onboarding_step2_desc": {
        "en": "Explore deterministic net revenue, volume, profit, margin, and category trends computed strictly from ground-truth data.",
        "ar": "استعرض صافي المبيعات، والكميات، وهوامش الربح، ورسوم الفئات والمناطق المحسوبة رياضياً بدقة مطلقة.",
    },
    "onboarding_step3_title": {
        "en": "3. AI Sales Agent (Gemini + MCP)",
        "ar": "3. استشر الوكيل الذكي (Gemini + MCP)",
    },
    "onboarding_step3_desc": {
        "en": "Ask complex multi-turn financial questions. Our reasoning agent uses 8 MCP tools under strict security policies.",
        "ar": "اطرح استفسارات مالية معقدة ومتعددة الخطوات. يدير الوكيل 8 أدوات MCP تحت سياسات أمان وتدقيق حازمة.",
    },
    "btn_onboarding_load_sample": {
        "en": "⚡ Load Benchmark Dataset (Recommended)",
        "ar": "⚡ تحميل البيانات المرجعية المعتمدة (موصى به)",
    },
    "btn_onboarding_goto_upload": {
        "en": "📁 Go to Dataset Ingestion",
        "ar": "📁 الانتقال لصفحة استيراد الملفات",
    },
    "catalog_pricing_notice": {
        "en": "All monetary calculations reflect catalog USD prices. Net revenue is computed strictly on validated non-quarantined rows.",
        "ar": "جميع الحسابات المالية تعكس أسعار الكتالوج المعتمدة بالدولار. صافي المبيعات محسوب حصرياً على الصفوف المدققة والصالحة.",
    },
    "active_dataset_metrics_header": {
        "en": "Dataset Context & Validation Health",
        "ar": "سياق البيانات وصحة التدقيق",
    },
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
    "axis_date": {
        "en": "Date",
        "ar": "التاريخ",
    },
    "axis_revenue": {
        "en": "Revenue ($)",
        "ar": "الإيرادات ($)",
    },
    "axis_product": {
        "en": "Product",
        "ar": "المنتج",
    },
    "axis_category": {
        "en": "Category",
        "ar": "الفئة",
    },
    "axis_region": {
        "en": "Region",
        "ar": "المنطقة",
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
    "user_steps_header": {
        "en": "Analysis & Verification Steps ({count} verified steps)",
        "ar": "خطوات التحليل والتأكيد ({count} خطوات معتمدة)",
    },
    "dev_diagnostics_header": {
        "en": "Advanced Technical Diagnostics (Authorized Developers Only)",
        "ar": "التشخيص التقني المتقدم (للمطورين المخوّلين فقط)",
    },
    "status_completed": {
        "en": "Completed ✓",
        "ar": "مكتمل ✓",
    },
    "status_pending_approval": {
        "en": "Awaiting Approval ⏳",
        "ar": "بانتظار الموافقة ⏳",
    },
    "status_failed": {
        "en": "Failed ✕",
        "ar": "تعذر التنفيذ ✕",
    },
    "status_denied": {
        "en": "Denied ✕",
        "ar": "تم الرفض ✕",
    },
    "forbidden_title": {
        "en": "🔒 403 Forbidden — Developer & Admin Console",
        "ar": "🔒 403 وصول محظور — مساحة المطور والإدارة",
    },
    "forbidden_caption": {
        "en": "Access to security audit logs and system internals is restricted to authorized engineers.",
        "ar": "الوصول إلى سجلات التدقيق الأمني والبيانات التقنية مقيد ومقتصر على المطورين المخوّلين فقط.",
    },
    "forbidden_desc": {
        "en": "You do not have permission to view this page directly. Please authenticate with your developer secret to proceed, or return to Merchant Operations.",
        "ar": "لا تملك صلاحية استعراض هذه الصفحة مباشرة. يرجى إدخال الرمز السري للمطور للمصادقة، أو العودة إلى لوحة العمليات التجارية.",
    },
    "forbidden_btn_return": {
        "en": "Return to Merchant Dashboard",
        "ar": "العودة إلى لوحة العمليات التجارية",
    },
    "forbidden_login_box_title": {
        "en": "Authenticate as Developer",
        "ar": "تسجيل دخول المطور المخوّل",
    },
    "forbidden_login_btn": {
        "en": "Unlock Developer Console",
        "ar": "فك قفل مساحة المطور",
    },
    "dev_section_title": {
        "en": "🛠️ Developer Console",
        "ar": "🛠️ مساحة المطور والإدارة",
    },
    "dev_badge_active": {
        "en": "🟢 Developer Mode: Active",
        "ar": "🟢 وضع المطور: نشط",
    },
    "dev_btn_lock": {
        "en": "Lock / Exit Developer Mode",
        "ar": "قفل / إنهاء وضع المطور",
    },
    "transparency_header": {
        "en": "🔍 Execution & Verification Details ({tools} verified steps)",
        "ar": "🔍 تفاصيل التنفيذ والتحقق ({tools} خطوات معتمدة)",
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
        "en": "Approve ✓",
        "ar": "اعتماد ✓",
    },
    "btn_deny_report": {
        "en": "Reject ✕",
        "ar": "رفض ✕",
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
        "en": "Ask about your sales, products, or customers...",
        "ar": "اسأل عن مبيعاتك أو منتجاتك أو عملائك...",
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
    "audit_summary_active_title": {
        "en": "📋 Active Dataset Audit Summary: `{name}`",
        "ar": "📋 ملخص تدقيق مجموعة البيانات النشطة: `{name}`",
    },
    "active_dataset_banner": {
        "en": "ℹ️ **Currently Active Dataset:** `{name}` ({rows:,} total rows) — Loaded & Active in Agent Memory and MCP Subprocess.",
        "ar": "ℹ️ **مجموعة البيانات النشطة حالياً:** `{name}` ({rows:,} سطر إجمالي) — محملة ونشطة في ذاكرة الوكيل ونظام MCP.",
    },
    "warn_upload_failed_active_retained": {
        "en": "⚠️ **Upload Rejected / Failed:** The uploaded file `{rejected}` was rejected and NOT loaded. The audit metrics and data preview below represent your **currently active dataset** (`{active}`, {rows:,} rows), which remains completely intact and unaffected.",
        "ar": "⚠️ **تنبيه (تم رفض الرفع):** تم رفض أو فشل رفع الملف `{rejected}` ولم يتم تحميله. ملخص التدقيق ومعاينة البيانات أدناه يوضحان **مجموعة البيانات النشطة حالياً** (`{active}`، {rows:,} سطر)، والتي بقيت سليمة ونشطة دون أي تغيير.",
    },
    "err_row_limit_title": {
        "en": "❌ Upload Rejected: Row Limit Exceeded",
        "ar": "❌ تم رفض الملف المرفوع: تجاوز الحد الأقصى للأسطر",
    },
    "err_row_limit_desc": {
        "en": "The uploaded file `{name}` contains **{rows:,}** rows, exceeding the platform limit of **50,000 rows** (governed by the CSV Data Contract for memory safety and sub-second analytics).",
        "ar": "الملف المرفوع `{name}` يحتوي على **{rows:,}** سطراً، وهو ما يتجاوز الحد الأقصى للمنصة البالغ **50,000 سطر** (المحدد في عقد بيانات CSV لأمان الذاكرة وسرعة التحليل).",
    },
    "err_row_limit_guidance": {
        "en": "💡 **What you can do:**\n1. **Filter date or region:** Narrow down your data before uploading (e.g. upload a single quarter or region).\n2. **Aggregate metrics:** Summarize transactions to daily/weekly totals rather than raw event streams.\n3. **Sample rows:** Take a representative sample of up to 50,000 rows.",
        "ar": "💡 **ما يمكنك فعله:**\n1. **التصفية حسب التاريخ أو المنطقة:** تقليص نطاق البيانات قبل الرفع (مثل رفع بيانات ربع سنوي واحد أو منطقة محددة).\n2. **تجميع البيانات:** تلخيص المعاملات يومياً أو أسبوعياً بدلاً من سجلات العمليات التفصيلية الخام.\n3. **أخذ عينة من البيانات:** استخدام عينة لا تتجاوز 50,000 سطر لإجراء التحليل.",
    },
    "err_row_limit_active_note": {
        "en": "🔒 **Active Data Retained:** Your previously active dataset `{active}` ({active_rows:,} rows) remains loaded and unaffected in the agent's memory and MCP subprocess.",
        "ar": "🔒 **البيانات النشطة محفوظة دون تغيير:** تظل مجموعة البيانات السابقة `{active}` ({active_rows:,} سطر) محملة وغير متأثرة في ذاكرة الوكيل ونظام MCP.",
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
    "dev_mode_title": {
        "en": "🔐 Local Developer Testing",
        "ar": "🔐 وضع الاختبار المحلي للمطور",
    },
    "dev_mode_badge_authorized": {
        "en": "🟢 Local Testing Mode: Authorized (127.0.0.1)",
        "ar": "🟢 وضع الاختبار المحلي: مفعل ومصرح (127.0.0.1)",
    },
    "dev_mode_badge_unauthorized": {
        "en": "🔒 Public Demo Mode (Synthetic Datasets Only)",
        "ar": "🔒 وضع العرض العام (البيانات التجريبية فقط)",
    },
    "dev_mode_secret_input": {
        "en": "Developer Authorization Secret",
        "ar": "الرمز السري لتفويض المطور",
    },
    "dev_mode_secret_placeholder": {
        "en": "Enter RETAILMIND_LOCAL_DEV_SECRET",
        "ar": "أدخل رمز RETAILMIND_LOCAL_DEV_SECRET",
    },
    "dev_mode_btn_authorize": {
        "en": "Authorize Local Uploads",
        "ar": "تفعيل الرفع المحلي",
    },
    "dev_mode_btn_revoke": {
        "en": "Lock / Revoke Local Authorization",
        "ar": "قفل / إلغاء التفويض المحلي",
    },
    "dev_mode_success_auth": {
        "en": "Local testing authorization confirmed! Custom CSV uploads are now enabled for this session.",
        "ar": "تم تأكيد تفويض الاختبار المحلي! تم تفعيل رفع ملفات CSV المخصصة لهذه الجلسة.",
    },
    "dev_mode_err_invalid": {
        "en": "Invalid developer authorization secret.",
        "ar": "الرمز السري لتفويض المطور غير صحيح.",
    },
    "dev_mode_err_no_secret_env": {
        "en": "RETAILMIND_LOCAL_DEV_SECRET is not configured in the server environment.",
        "ar": "متغير RETAILMIND_LOCAL_DEV_SECRET غير معين في بيئة الخادم.",
    },
    "dev_mode_err_public_binding": {
        "en": "🚫 Local Testing Mode Disabled: Server is bound to a public interface. Local testing is strictly restricted to 127.0.0.1 loopback.",
        "ar": "🚫 وضع الاختبار المحلي معطل: الخادم مرتبط بواجهة شبكة عامة. الاختبار المحلي مقيد حصراً بعنوان 127.0.0.1.",
    },
    "badge_dataset_synthetic": {
        "en": "🟢 Approved Synthetic Dataset",
        "ar": "🟢 مجموعة بيانات تجريبية معتمدة",
    },
    "badge_dataset_custom": {
        "en": "🔒 Custom Local Dataset (Private / Non-Synthetic)",
        "ar": "🔒 بيانات محلية مخصصة (خاصة / غير تجريبية)",
    },
    "err_demo_unauth_title": {
        "en": "🔒 Upload Restricted: Public Demo Security Policy",
        "ar": "🔒 تم حظر الرفع: سياسة أمان العرض التجريبي العام",
    },
    "err_demo_unauth_desc": {
        "en": "Arbitrary custom CSV uploads are strictly disabled in public demo mode to protect data confidentiality. In public demo mode, only approved bundled synthetic datasets may be loaded. To upload custom business CSVs locally, authorize using your developer secret in the sidebar on `127.0.0.1`.",
        "ar": "تم إيقاف رفع ملفات CSV المخصصة في وضع العرض العام لحماية خصوصية البيانات. يُسمح فقط بتحميل مجموعات البيانات التجريبية المعتمدة. لرفع ملفاتك الخاصة محلياً، يرجى تفعيل تفويض المطور عبر القائمة الجانبية على `127.0.0.1`.",
    },

    # -------------------------------------------------------------------------
    # View 4: 🧠 Persistent Memory Explorer
    # -------------------------------------------------------------------------
    "memory_title": {
        "en": "🧠 Saved Business Insights",
        "ar": "🧠 الرؤى المحفوظة والذاكرة الذكية",
    },
    "memory_caption": {
        "en": "Inspect verified business findings and historical context preserved across sessions.",
        "ar": "استعراض الرؤى التجارية والتحليلات المعتمدة المحفوظة عبر الجلسات السابقة.",
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
    # -------------------------------------------------------------------------
    # Reference-Driven UI Elements (Image 1, 2, 3)
    # -------------------------------------------------------------------------
    "ref_brand_tagline": {
        "en": "Retail Intelligence for Smarter Decisions",
        "ar": "ذكاء التجزئة لقرارات أذكى",
    },
    "ref_brand_subtagline": {
        "en": "Deeper Data · Faster Growth",
        "ar": "بيانات أعمق.. نمو أسرع",
    },
    "ref_today_date": {
        "en": "Monday, 27 October 2025",
        "ar": "الاثنين، 27 أكتوبر 2025",
    },
    "ref_last_updated_today": {
        "en": "Last update: Today",
        "ar": "آخر تحديث: اليوم",
    },
    "ref_date_range_label": {
        "en": "Last 30 days",
        "ar": "آخر 30 يوماً",
    },
    "lbl_active_dataset": {
        "en": "Active Dataset",
        "ar": "البيانات النشطة",
    },
    "lbl_valid_rows": {
        "en": "valid rows",
        "ar": "سجلات صالحة",
    },
    "lbl_total_rows": {
        "en": "total rows",
        "ar": "إجمالي السجلات",
    },
    "ref_store_status": {
        "en": "Connected to Store Data",
        "ar": "متصل ببيانات المتجر",
    },
    "ref_memory_status": {
        "en": "Persistent Memory: Active",
        "ar": "الذاكرة الدائمة: مفعلة",
    },
    "ref_permission_status": {
        "en": "Permissions: Analyst Only",
        "ar": "الصلاحيات: محلل فقط",
    },
    "ref_governance_title": {
        "en": "Data & Governance",
        "ar": "البيانات والحوكمة",
    },
    "ref_governance_subtitle": {
        "en": "Sales Data Management, Quality & Governance",
        "ar": "إدارة بيانات المبيعات وضمان جودتها وحوكمتها",
    },
    "ref_analyst_title": {
        "en": "AI Sales Analyst",
        "ar": "المحلل الذكي",
    },
    "ref_analyst_subtitle": {
        "en": "Real Intelligence for Store Growth",
        "ar": "ذكاء حقيقي لنمو متجرك",
    },
    "ref_performance_title": {
        "en": "Performance Overview",
        "ar": "نظرة عامة على الأداء",
    },
    "ref_performance_subtitle": {
        "en": "Real-time Sales & Profit Analytics",
        "ar": "تحليلات المبيعات والأرباح لحظياً",
    },
    "ref_col_matching_title": {
        "en": "Column Matching",
        "ar": "مطابقة الأعمدة",
    },
    "ref_user_greeting": {
        "en": "Welcome",
        "ar": "مرحباً بك",
    },
    "ref_staged_query": {
        "en": "Selected Prompt:",
        "ar": "الاستفسار المختار:",
    },
    "ref_btn_send_staged": {
        "en": "Execute Query 🚀",
        "ar": "إرسال الاستفسار 🚀",
    },
    "ref_btn_clear_staged": {
        "en": "Clear",
        "ar": "إلغاء",
    },
    "ref_approval_idle_title": {
        "en": "Profit Reports & Governance",
        "ar": "إدارة تقارير الأرباح والموافقات",
    },
    "ref_approval_idle_desc": {
        "en": "No reports currently pending approval. Request a new executive report via the AI Sales Agent.",
        "ar": "لا توجد تقارير معلقة بانتظار الاعتماد حالياً. يمكنك طلب تقرير مالي تنفيذي جديد عبر المحلل الذكي.",
    },
    "ref_approval_status_idle": {
        "en": "System Ready ✓",
        "ar": "النظام جاهز ✓",
    },
    "ref_audit_storage_status": {
        "en": "Audit Storage: Protected & Active (SQLite WAL)",
        "ar": "سجل العمليات والتدقيق: متصل ومحمي (SQLite WAL)",
    },
    "ref_compared_first_half": {
        "en": "vs first half of period",
        "ar": "مقارنة بالنصف الأول من الفترة",
    },
    "ref_baseline_single_period": {
        "en": "Baseline period",
        "ar": "فترة أساس أولى",
    },
    "ref_date_span_prefix": {
        "en": "Period:",
        "ar": "الفترة المشمولة:",
    },
    "ref_user_subtitle": {
        "en": "Retail's future begins with data",
        "ar": "مستقبل التجزئة يبدأ بالبيانات",
    },
    "ref_default_merchant": {
        "en": "Authorized Merchant",
        "ar": "التاجر المعتمد",
    },
    "ref_sidebar_ai_status": {
        "en": "● Connected to AI",
        "ar": "● متصل بالذكاء الاصطناعي",
    },
    "ref_nav_ops": {
        "en": "Merchant Operations",
        "ar": "العمليات التجارية",
    },
    "ref_nav_diagnostics": {
        "en": "Logs & Diagnostics",
        "ar": "السجلات والتشخيص",
    },
    "ref_advanced_diagnostics": {
        "en": "Advanced Diagnostics & Security",
        "ar": "التشخيص المتقدم والأمان",
    },
    "ref_verified_operations_title": {
        "en": "Verified Analytical Steps",
        "ar": "الخطوات التحليلية المعتمدة",
    },
    "ref_audit_col_action": {
        "en": "Operation",
        "ar": "العملية",
    },
    "ref_audit_col_status": {
        "en": "Status",
        "ar": "الحالة",
    },
    "auth_status_dev_active_banner": {
        "en": "Local Testing Mode Authorized: Custom CSV uploads enabled (Max 10 MB, 50,000 rows)",
        "ar": "وضع الاختبار المحلي مفوّض: يمكنك رفع ملفات CSV المخصصة (الحد الأقصى: 10 ميجابايت، 50,000 صف)",
    },
    "auth_notice_demo_mode_title": {
        "en": "Approved Demo Mode (Restricted Custom Uploads)",
        "ar": "وضع العرض التجريبي المعتمد (تقييد الملفات المخصصة)",
    },
    "auth_notice_demo_mode_desc": {
        "en": "To protect data confidentiality, public demo mode only permits approved bundled synthetic datasets. To upload custom business CSVs during local testing on 127.0.0.1, authorize via Developer Authorization below.",
        "ar": "لحماية سرية البيانات، يقتصر وضع العرض التجريبي على مجموعات البيانات النموذجية المعتمدة (مثل synthetic_sales.csv). إذا كنت تجري اختباراً محلياً على 127.0.0.1، يرجى تفعيل تفويض المطور المحلي أدناه لتمكين رفع الملفات المخصصة.",
    },
    "auth_expander_dev_title": {
        "en": "Local Developer Authorization (Unlock Custom Uploads)",
        "ar": "تفويض الاختبار المحلي للمطورين (تفعيل رفع الملفات المخصصة)",
    },
    "err_unauthenticated_demo_title": {
        "en": "Custom Upload Restricted in Public Demo Mode",
        "ar": "تعذر قبول الملف: وضع العرض التجريبي المعتمد",
    },
    "err_unauthenticated_demo_desc": {
        "en": "Arbitrary custom CSV uploads are disabled in unauthenticated public demo mode to guarantee confidentiality. If testing locally on 127.0.0.1, please authorize developer testing using the Developer Authorization panel above.",
        "ar": "تم رفض الملف المخصص لأن النظام يعمل في وضع العرض التجريبي غير المفوّض لحماية سرية البيانات. إذا كنت تختبر النظام محلياً على 127.0.0.1، يرجى إدخال رمز تفويض المطور المحلي في لوحة التفويض أعلاه قبل رفع الملف.",
    },
    "err_local_public_binding_title": {
        "en": "Local Testing Rejected on Public Interface",
        "ar": "تم رفض الاختبار المحلي: الخادم غير مقيد بعنوان loopback",
    },
    "err_local_public_binding_desc": {
        "en": "Local developer testing mode is strictly restricted to 127.0.0.1 loopback interface. The application appears bound to a public interface.",
        "ar": "يقتصر وضع اختبار المطورين المحلي بشكل صارم على عنوان 127.0.0.1 المحلي. الخادم مرتبط بعنوان عام أو غير محلي، لذا تم حجب الاختبار لحماية الأمان.",
    },
    "err_csv_missing_columns_title": {
        "en": "Invalid CSV Schema (Missing Required Columns)",
        "ar": "هيكل ملف CSV غير صالح (أعمدة مفقودة)",
    },
    "err_csv_missing_columns_desc": {
        "en": "The uploaded CSV file is missing required columns (date, product, quantity, unit_price). Details: {columns}",
        "ar": "ملف CSV المرفوع يفتقر إلى بعض الأعمدة الأساسية المطلوبة (date، product، quantity، unit_price). التفاصيل: {columns}",
    },
    "ref_upload_box_title": {
        "en": "Sales Data Ingestion",
        "ar": "استيراد بيانات المبيعات",
    },
    "ref_upload_box_sub": {
        "en": "Drag and drop CSV or XLSX file here",
        "ar": "اسحب وأفلت ملف CSV أو XLSX هنا",
    },
    "ref_col_type_date": {
        "en": "date",
        "ar": "تاريخ",
    },
    "ref_col_type_product": {
        "en": "product name",
        "ar": "اسم المنتج",
    },
    "ref_col_type_number": {
        "en": "number",
        "ar": "رقم",
    },
    "ref_col_cost_unavailable": {
        "en": "Cost (unavailable)",
        "ar": "التكلفة (غير متوفرة)",
    },
    "lbl_report": {
        "en": "Executive Profit Report",
        "ar": "تقرير الأرباح التنفيذي",
    },
    "ref_approval_report_desc": {
        "en": "Report generated based on imported sales data",
        "ar": "تم إنشاء التقرير بناءً على بيانات المبيعات المستوردة",
    },
    "ref_approval_created_date": {
        "en": "Creation Date: Oct 27, 2025",
        "ar": "تاريخ الإنشاء: 27 أكتوبر 2025",
    },
    "ref_audit_table_title": {
        "en": "Audit Trail",
        "ar": "سجل التدقيق",
    },
    "ref_audit_col_time": {
        "en": "Time",
        "ar": "الوقت",
    },
    "ref_audit_col_event": {
        "en": "Event",
        "ar": "الحدث",
    },
    "ref_audit_col_details": {
        "en": "Details",
        "ar": "التفاصيل",
    },
    "ref_audit_col_user": {
        "en": "User",
        "ar": "المستخدم",
    },
    "ref_audit_event_upload": {
        "en": "Data Imported",
        "ar": "تم استيراد البيانات",
    },
    "ref_audit_event_analysis": {
        "en": "Analysis Executed",
        "ar": "تم تشغيل التحليل",
    },
    "ref_audit_event_approval": {
        "en": "Pending Approval",
        "ar": "بانتظار موافقة",
    },
    "ref_audit_event_denial": {
        "en": "Approval Denied",
        "ar": "تم رفض العملية",
    },
    "ref_btn_review": {
        "en": "Review 👁",
        "ar": "مراجعة 👁",
    },
    "ref_col_date": {
        "en": "Date ✓ (date)",
        "ar": "التاريخ ✓ (تاريخ)",
    },
    "ref_col_product": {
        "en": "Product ✓ (name)",
        "ar": "المنتج ✓ (اسم المنتج)",
    },
    "ref_col_revenue": {
        "en": "Revenue ✓ (number)",
        "ar": "الإيراد ✓ (رقم)",
    },
    "ref_col_cost": {
        "en": "Cost ✓ (number)",
        "ar": "التكلفة ✓ (رقم)",
    },
    "ref_col_quantity": {
        "en": "Quantity ✓ (number)",
        "ar": "الكمية ✓ (رقم)",
    },
    "lbl_col_date": {
        "en": "Date",
        "ar": "التاريخ",
    },
    "lbl_col_product": {
        "en": "Product",
        "ar": "المنتج",
    },
    "lbl_col_price": {
        "en": "Price / Revenue",
        "ar": "الإيراد / السعر",
    },
    "lbl_col_cost": {
        "en": "Cost",
        "ar": "التكلفة",
    },
    "ref_badge_verified": {
        "en": "Verified",
        "ar": "تم التحقق",
    },
    "lbl_col_quantity": {
        "en": "Quantity",
        "ar": "الكمية",
    },
    "ref_step_analysis": {
        "en": "Sales Analysis",
        "ar": "تحليل المبيعات",
    },
    "ref_step_analysis_sub": {
        "en": "Sales analyzed by category",
        "ar": "تم تحليل أداء المبيعات حسب الفئات",
    },
    "ref_step_cost": {
        "en": "Cost Comparison",
        "ar": "مقارنة التكاليف",
    },
    "ref_step_cost_sub": {
        "en": "Costs compared to previous period",
        "ar": "تمت مقارنة التكاليف مع الفترات السابقة",
    },
    "ref_step_mcp": {
        "en": "MCP Verification",
        "ar": "التحقق عبر MCP",
    },
    "ref_step_mcp_sub": {
        "en": "Verified results via MCP tools",
        "ar": "تم التحقق من النتائج عبر مصادر متصلة (MCP)",
    },
    "ref_approval_card_title": {
        "en": "Profit Report Approval",
        "ar": "موافقة على تقرير الأرباح",
    },
    "ref_approval_card_sub": {
        "en": "Monthly Profit Report — Generated from verified sales data",
        "ar": "تقرير الأرباح الشهري — تم إنشاء التقرير بناءً على بيانات المبيعات المستوردة",
    },
    "ref_pending_review": {
        "en": "Pending Review",
        "ar": "بانتظار المراجعة",
    },
    "ref_btn_approve": {
        "en": "Approve ✓",
        "ar": "اعتماد ✓",
    },
    "ref_top_products_card_title": {
        "en": "Top Products",
        "ar": "أبرز المنتجات",
    },
    "ref_col_hash": {
        "en": "#",
        "ar": "#",
    },
    "ref_col_product_name": {
        "en": "Product",
        "ar": "المنتج",
    },
    "ref_col_category_name": {
        "en": "Category",
        "ar": "الفئة",
    },
    "ref_col_sales_volume": {
        "en": "Sales Volume",
        "ar": "المبيعات",
    },
    "ref_col_sales_revenue": {
        "en": "Revenue",
        "ar": "الإيرادات",
    },
    "ref_brand_bottom_tagline": {
        "en": "Smarter Data for Greater Growth",
        "ar": "بيانات أذكى لنمو أكبر",
    },
    "chart_category_perf": {
        "en": "Category Performance",
        "ar": "أداء الفئات",
    },
    "chart_revenue_trend": {
        "en": "Revenue Trend",
        "ar": "اتجاه الإيرادات",
    },
    "ref_compared_prev_period": {
        "en": "vs previous period",
        "ar": "مقارنة بالفترة السابقة",
    },
    "ref_orders_title": {
        "en": "Orders",
        "ar": "الطلبات",
    },
    "ref_revenue_title": {
        "en": "Revenue",
        "ar": "الإيرادات",
    },
    "ref_profit_title": {
        "en": "Net Profit",
        "ar": "صافي الربح",
    },
    "ref_margin_title": {
        "en": "Profit Margin",
        "ar": "هامش الربح",
    },
    "ref_units_sold_count": {
        "en": "{count} units sold",
        "ar": "{count} وحدة مباعة",
    },
    "ref_total_cost_sub": {
        "en": "Total cost: {cost}",
        "ar": "إجمالي التكلفة: {cost}",
    },
    "ref_completed_sales": {
        "en": "{count} completed sales",
        "ar": "{count} معاملة بيع مدققة",
    },
    "ref_margin_ground_truth": {
        "en": "Deterministic ground-truth margin",
        "ar": "هامش دقيق ومؤكد رياضياً",
    },
    "ref_active_dataset_badge": {
        "en": "Active Dataset: {filename} ({rows} verified rows)",
        "ar": "الملف النشط: {filename} ({rows} صفاً مدققاً)",
    },
    "ref_tools_employed": {
        "en": "Tools Employed",
        "ar": "الأدوات المستخدمة",
    },
    "ref_human_approval_required": {
        "en": "Human Approval Required",
        "ar": "الموافقة البشرية مطلوبة",
    },
    "ref_human_approval_desc": {
        "en": "Actions with financial impact require human approval before execution.",
        "ar": "تتطلب الإجراءات ذات التأثير المالي موافقة بشرية قبل التنفيذ.",
    },
    "ref_context_info": {
        "en": "Context Information",
        "ar": "معلومات السياق",
    },
    "ref_context_period": {
        "en": "Current Period: Verified Active Dataset",
        "ar": "الفترة الحالية: مجموعة البيانات النشطة",
    },
    "ref_context_store": {
        "en": "Store: Retail Analytics Main",
        "ar": "المتجر: المتجر الرئيسي",
    },
    "ref_context_sources": {
        "en": "Sources: Verified Sales Database",
        "ar": "المصادر: قاعدة بيانات المبيعات المعتمدة",
    },
    "ref_tagline_badge": {
        "en": "✨ Verified Insights. Smarter Decisions.",
        "ar": "✨ رؤى موثوقة. قرارات أذكى.",
    },
    "ref_followup_suggestions": {
        "en": "Suggested Follow-ups:",
        "ar": "اقتراحات المتابعة:",
    },
    "ref_pill_profit_report": {
        "en": "📊 Profit Report",
        "ar": "📊 تقرير الأرباح",
    },
    "ref_pill_top_products": {
        "en": "📦 Top Products?",
        "ar": "📦 أفضل المنتجات؟",
    },
    "ref_pill_revenue_summary": {
        "en": "📈 Revenue Analysis",
        "ar": "📈 تحليل المبيعات",
    },
    "ref_pill_anomalies": {
        "en": "⚠️ Period Comparison",
        "ar": "⚠️ مقارنة الفترات",
    },
    "ref_tool_revenue_title": {
        "en": "Revenue Analysis",
        "ar": "تحليل الإيرادات",
    },
    "ref_tool_revenue_desc": {
        "en": "Sales trends and category performance",
        "ar": "تحليل اتجاهات المبيعات والفئات",
    },
    "ref_tool_costs_title": {
        "en": "Cost Comparison",
        "ar": "مقارنة التكاليف",
    },
    "ref_tool_costs_desc": {
        "en": "Compare costs across periods",
        "ar": "مقارنة التكاليف عبر الفترات",
    },
    "ref_tool_anomalies_title": {
        "en": "Anomaly Detection",
        "ar": "كشف الشذوذ",
    },
    "ref_tool_anomalies_desc": {
        "en": "Identify statistical outliers in sales",
        "ar": "فحص المعاملات والقيم الشاذة إحصائياً",
    },
    "ref_stepper_verified_mcp": {
        "en": "Verified Calculation",
        "ar": "التحقق الحسابي المعتمد",
    },
    "ref_stepper_verified_mcp_sub": {
        "en": "Results verified via trusted analytical engine",
        "ar": "تم التحقق من النتائج عبر محرك الحسابات المعتمد",
    },
    "agent_welcome_box_title": {
        "en": "How can RetailMind AI assist you today?",
        "ar": "كيف يمكن لـ RetailMind AI مساعدتك اليوم؟",
    },
    "agent_welcome_box_sub": {
        "en": "Ask any question about your sales trends, category performance, or request a verified executive report.",
        "ar": "اطرح أي سؤال حول اتجاهات مبيعاتك، وأداء فئاتك، أو اطلب تقريراً تنفيذياً معتمداً وموثقاً بالأدوات الحقيقية.",
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
    """Returns scoped, accessible CSS for bilingual presentation (RTL for Arabic, LTR for English).
    
    Protects Streamlit's native Material Symbols ligature font from being overridden by custom webfonts,
    provides a modern responsive CSS Grid for KPI metrics that adapts across 5 screen sizes,
    and applies strict directional isolation to financial numbers and code.
    """
    common_css = """
        /* ══════════════════════════════════════════════════════════════════
           MANDATORY LIGHT SAAS THEME SPECIFICATION (Targeting Ref Images 1, 2, 3)
           Warm Ivory Canvas: #FCFBF9
           White Surfaces:    #FFFFFF
           Navy Typography:   #0F172A
           Emerald Accent:    #059669
           Borders/Dividers:  #E8E5DF
           ══════════════════════════════════════════════════════════════════ */
        
        /* 1. Global App Canvas */
        .stApp, 
        [data-testid="stAppViewContainer"], 
        .main, 
        section.main, 
        [data-testid="stHeader"] {
            background-color: #fcfbf9 !important;
            background: #fcfbf9 !important;
            color: #0f172a !important;
        }

        /* 2. Top Streamlit Header & Page Padding */
        [data-testid="stHeader"] {
            background-color: transparent !important;
            border-bottom: none !important;
            pointer-events: auto !important;
            z-index: 100 !important;
        }
        /* Hide technical deploy button and hamburger menu while preserving stExpandSidebarButton */
        [data-testid="stToolbarActions"],
        [data-testid="stMainMenu"] {
            display: none !important;
        }
        [data-testid="stToolbar"] {
            background: transparent !important;
            pointer-events: none !important;
        }
        [data-testid="stExpandSidebarButton"] {
            pointer-events: auto !important;
            display: flex !important;
            visibility: visible !important;
        }
        /* Always show collapse button with refined emerald styling */
        [data-testid="stSidebarCollapseButton"],
        [data-testid="stSidebarCollapseButton"] button {
            visibility: visible !important;
            opacity: 1 !important;
            color: #64748b !important;
        }
        [data-testid="stSidebarCollapseButton"] button:hover {
            color: #059669 !important;
            background-color: #f1f5f9 !important;
        }
        .block-container {
            padding-top: 1.8rem !important;
            padding-bottom: 2.5rem !important;
            max-width: 1440px !important;
        }

        /* 3. Typography — Deep Navy */
        h1, h2, h3, h4, h5, h6 {
            color: #0f172a !important;
            font-weight: 700 !important;
            letter-spacing: -0.015em;
        }
        p, span, label, .stMarkdown, .stText {
            color: #0f172a !important;
        }
        .stCaption, [data-testid="stCaptionContainer"] {
            color: #64748b !important;
        }

        /* 4. Light Sidebar */
        section[data-testid="stSidebar"], 
        [data-testid="stSidebarContent"], 
        [data-testid="stSidebarNav"] {
            background-color: #ffffff !important;
            border-inline-end: 1px solid #e8e5df !important;
        }
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] h4 {
            color: #0f172a !important;
        }
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] label {
            color: #334155 !important;
        }

        /* 5. Buttons Styling */
        .stButton > button {
            border-radius: 10px !important;
            border: 1px solid #e2e8f0 !important;
            background-color: #ffffff !important;
            color: #0f172a !important;
            font-weight: 600 !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.03) !important;
            transition: all 0.15s ease !important;
        }
        .stButton > button:hover {
            border-color: #059669 !important;
            color: #059669 !important;
            background-color: #f0fdf4 !important;
            box-shadow: 0 2px 6px rgba(5, 150, 105, 0.1) !important;
        }
        .stButton > button[kind="primary"] {
            background-color: #059669 !important;
            color: #ffffff !important;
            border-color: #047857 !important;
        }
        .stButton > button[kind="primary"]:hover {
            background-color: #047857 !important;
            color: #ffffff !important;
        }

        /* 6. Inputs & File Uploader */
        [data-testid="stFileUploader"] {
            background-color: #ffffff !important;
            border: 1px dashed #cbd5e1 !important;
            border-radius: 14px !important;
            padding: 16px !important;
        }
        [data-testid="stFileUploader"]:hover {
            border-color: #059669 !important;
        }
        .stTextInput > div > div > input {
            background-color: #ffffff !important;
            color: #0f172a !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 10px !important;
        }
        .stTextInput > div > div > input:focus {
            border-color: #059669 !important;
            box-shadow: 0 0 0 2px rgba(5, 150, 105, 0.2) !important;
        }

        /* 7. Chat Inputs & Bubbles */
        [data-testid="stChatInput"] {
            border-radius: 16px !important;
            border: 1px solid #cbd5e1 !important;
            background-color: #ffffff !important;
            box-shadow: 0 4px 16px rgba(0,0,0,0.04) !important;
        }
        [data-testid="stChatInput"]:focus-within {
            border-color: #059669 !important;
            box-shadow: 0 4px 18px rgba(5, 150, 105, 0.12) !important;
        }

        /* 8. Expander & Tables Surfaces */
        [data-testid="stExpander"] {
            background-color: #ffffff !important;
            border: 1px solid #e8e5df !important;
            border-radius: 12px !important;
        }
        [data-testid="stExpander"] summary {
            color: #0f172a !important;
            font-weight: 600 !important;
        }
        [data-testid="stDataFrame"], [data-testid="stTable"] {
            background-color: #ffffff !important;
            border-radius: 12px !important;
            border: 1px solid #e8e5df !important;
        }

        /* Material Symbols Ligature Font Protection */
        [data-testid="stIconMaterial"], [data-testid="stIconMaterial"] *,
        .material-symbols-rounded, .material-icons, span[translate="no"] {
            font-family: "Material Symbols Rounded", "Material Icons" !important;
            font-weight: normal !important;
            font-style: normal !important;
            line-height: 1 !important;
            letter-spacing: normal !important;
            text-transform: none !important;
            display: inline-block !important;
            white-space: nowrap !important;
            word-wrap: normal !important;
            direction: ltr !important;
            -webkit-font-smoothing: antialiased !important;
            text-rendering: optimizeLegibility !important;
            -moz-osx-font-smoothing: grayscale !important;
            font-feature-settings: 'liga' !important;
        }

        /* Responsive Modern KPI Grid (4 Cards matching Reference 3) */
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 16px;
            margin: 16px 0 24px 0;
            width: 100%;
        }
        @media (max-width: 1100px) {
            .kpi-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }
        @media (max-width: 600px) {
            .kpi-grid {
                grid-template-columns: 1fr;
                gap: 12px;
            }
        }

        /* Standard SaaS KPI Card */
        .kpi-card {
            background: #ffffff;
            border: 1px solid #e8e5df;
            border-radius: 14px;
            padding: 16px 18px;
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.03);
            transition: all 0.2s ease;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            min-height: 125px;
            box-sizing: border-box;
        }
        .kpi-card:hover {
            border-color: #059669;
            box-shadow: 0 8px 18px -4px rgba(5, 150, 105, 0.12);
            transform: translateY(-2px);
        }

        /* Hero KPI Card — Deep Emerald Gradient (Ref. Image 3) */
        .kpi-card-hero {
            background: linear-gradient(135deg, #064e3b 0%, #047857 50%, #059669 100%) !important;
            border: 1px solid #047857 !important;
            border-radius: 14px;
            padding: 16px 18px;
            box-shadow: 0 6px 20px -2px rgba(5, 150, 105, 0.35) !important;
            transition: all 0.2s ease;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            min-height: 125px;
            box-sizing: border-box;
            color: #ffffff !important;
        }
        .kpi-card-hero:hover {
            box-shadow: 0 12px 26px -2px rgba(5, 150, 105, 0.45) !important;
            transform: translateY(-2px);
        }
        .kpi-card-hero .kpi-title {
            color: #d1fae5 !important;
        }
        .kpi-card-hero .kpi-value {
            color: #ffffff !important;
            font-weight: 800 !important;
        }
        .kpi-card-hero .kpi-icon-wrap {
            color: #ffffff !important;
            background: rgba(255, 255, 255, 0.2) !important;
        }
        .kpi-card-hero .kpi-delta-pos {
            color: #a7f3d0 !important;
            font-weight: 600 !important;
        }

        .kpi-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 8px;
        }
        .kpi-title {
            font-size: 0.90rem;
            font-weight: 700;
            color: #0f172a;
            letter-spacing: -0.01em;
        }
        .kpi-icon-wrap {
            color: #059669;
            background: #ecfdf5;
            padding: 7px;
            border-radius: 10px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }
        .kpi-value {
            font-size: clamp(1.15rem, 1.4vw, 1.55rem);
            font-weight: 800;
            color: #0f172a;
            line-height: 1.2;
            white-space: nowrap;
            overflow: visible;
            direction: ltr !important;
            unicode-bidi: isolate;
        }
        .kpi-footer {
            display: flex;
            align-items: center;
            gap: 6px;
            margin-top: 6px;
            font-size: 0.76rem;
        }
        .kpi-delta-pos {
            color: #059669;
            font-weight: 600;
        }
        .kpi-delta-neg {
            color: #dc2626;
            font-weight: 600;
        }
        .kpi-delta-neutral {
            color: #64748b;
        }

        /* Status Badges */
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .badge-success {
            background: #ecfdf5;
            color: #065f46;
            border: 1px solid #a7f3d0;
        }
        .badge-info {
            background: #f0fdf4;
            color: #047857;
            border: 1px solid #bbf7d0;
        }
        .badge-warning {
            background: #fef3c7;
            color: #92400e;
            border: 1px solid #fde68a;
        }
        .badge-neutral {
            background: #f8fafc;
            color: #475569;
            border: 1px solid #e2e8f0;
        }

        /* Top Header Bar & Brandmark */
        .app-header-bar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 22px;
            padding-bottom: 14px;
            border-bottom: 1px solid #e8e5df;
            flex-wrap: wrap;
            gap: 12px;
        }
        .brand-badge {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .brand-logo-wrap {
            width: 44px;
            height: 44px;
            border-radius: 12px;
            background: #ecfdf5;
            border: 1px solid #a7f3d0;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #059669;
        }
        .header-date-pill {
            background: #ffffff;
            border: 1px solid #e8e5df;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.8rem;
            color: #475569;
            font-weight: 500;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }

        /* Onboarding Banner & Steps */
        .onboarding-card {
            background: #ffffff;
            border: 1px solid #e8e5df;
            border-radius: 16px;
            padding: 26px 24px;
            margin: 12px 0 24px 0;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.03);
        }
        .onboarding-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 20px;
            margin: 22px 0;
        }
        @media (max-width: 900px) {
            .onboarding-grid {
                grid-template-columns: 1fr;
                gap: 14px;
            }
        }
        .onboarding-step {
            background: #fcfbf9;
            border: 1px solid #e8e5df;
            border-radius: 12px;
            padding: 18px;
            display: flex;
            flex-direction: column;
        }
        .onboarding-step-icon {
            width: 36px;
            height: 36px;
            border-radius: 8px;
            background: #ecfdf5;
            color: #059669;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 12px;
        }

        /* Context Banner */
        .context-banner {
            background: #ffffff;
            border: 1px solid #e8e5df;
            border-radius: 12px;
            padding: 14px 18px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 12px;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
        }

        /* Chat bubbles */
        .stChatMessage {
            background-color: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 14px !important;
            padding: 16px 20px !important;
            margin-bottom: 16px !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02) !important;
        }
        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
            background-color: #fefce8 !important;
            border-color: #fef08a !important;
        }
        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
            background-color: #ffffff !important;
            border-color: #e2e8f0 !important;
            border-inline-start: 4px solid #059669 !important;
        }

        /* Stepper Pipeline & Cards */
        .execution-stepper {
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 12px 0 14px 0;
            flex-wrap: wrap;
        }
        .step-box {
            background: #f0fdf4;
            border: 1px solid #a7f3d0;
            border-radius: 10px;
            padding: 8px 12px;
            display: flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
        }
        .step-arrow {
            color: #94a3b8;
            font-size: 0.95rem;
            font-weight: bold;
            user-select: none;
        }

        /* Column Matching Grid */
        .col-match-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
            gap: 12px;
            margin: 14px 0 20px 0;
        }
        .col-match-pill {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 12px 14px;
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            gap: 4px;
        }
        .col-match-pill.matched {
            border-color: #a7f3d0;
            background: #f0fdf4;
        }

        /* Approval Governance Card */
        .approval-card {
            background: #ffffff;
            border: 1px solid #fde68a;
            border-radius: 14px;
            padding: 20px 22px;
            margin: 16px 0;
            box-shadow: 0 4px 14px rgba(245, 158, 11, 0.06);
        }

        /* Top Products Summary Card */
        .top-products-card {
            background: #ffffff;
            border: 1px solid #e8e5df;
            border-radius: 14px;
            padding: 20px;
            margin-top: 20px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
        }

        /* Heading Typography — Balanced SaaS Proportion */
        h1, [data-testid="stHeadingWithActionElements"] h1 {
            font-size: 1.65rem !important;
            font-weight: 800 !important;
            color: #0f172a !important;
            letter-spacing: -0.02em !important;
            margin-bottom: 2px !important;
            margin-top: 0 !important;
        }
        h2, [data-testid="stHeadingWithActionElements"] h2 {
            font-size: 1.30rem !important;
            font-weight: 700 !important;
            color: #0f172a !important;
            letter-spacing: -0.01em !important;
        }
        h3, [data-testid="stHeadingWithActionElements"] h3 {
            font-size: 1.10rem !important;
            font-weight: 600 !important;
            color: #0f172a !important;
        }

        /* Top Bar Segmented Control (Language Switcher) */
        div:has(> button[data-variant="segmented_control"]),
        [data-testid="stSegmentedControl"] {
            background: #f1f5f9 !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 20px !important;
            padding: 3px !important;
            gap: 2px !important;
            display: inline-flex !important;
            align-items: center !important;
        }
        button[data-variant="segmented_control"],
        [data-testid="stSegmentedControl"] button {
            border: none !important;
            border-radius: 16px !important;
            padding: 4px 14px !important;
            font-size: 0.80rem !important;
            font-weight: 500 !important;
            color: #64748b !important;
            background: transparent !important;
            box-shadow: none !important;
            transition: all 0.15s ease !important;
            cursor: pointer !important;
        }
        button[data-variant="segmented_control"][aria-checked="true"],
        button[data-variant="segmented_control"][data-selected="true"],
        [data-testid="stSegmentedControl"] button[aria-selected="true"],
        [data-testid="stSegmentedControl"] button[data-selected="true"] {
            background: #ffffff !important;
            color: #059669 !important;
            font-weight: 700 !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08) !important;
        }
        button[data-variant="segmented_control"][aria-checked="true"] p,
        button[data-variant="segmented_control"][data-selected="true"] p,
        [data-testid="stSegmentedControl"] button[aria-selected="true"] p,
        [data-testid="stSegmentedControl"] button[data-selected="true"] p {
            color: #059669 !important;
            font-weight: 700 !important;
        }
        button[data-variant="segmented_control"]:hover,
        [data-testid="stSegmentedControl"] button:hover {
            color: #0f172a !important;
        }

        /* Sidebar Styling — Modern Reference-Driven Navigation */
        section[data-testid="stSidebar"] {
            background-color: #ffffff !important;
        }
        /* Completely hide native circular radio indicator in sidebar navigation */
        section[data-testid="stSidebar"] [data-testid="stRadio"] label[data-testid="stRadioOption"] > div > div:first-child,
        section[data-testid="stSidebar"] [data-testid="stRadio"] label[data-testid="stRadioOption"] [class*="e1dm8mpf4"],
        section[data-testid="stSidebar"] [data-testid="stRadio"] label[data-testid="stRadioOption"] div:has(> .st-emotion-cache-16jqfj2),
        section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child {
            display: none !important;
            width: 0 !important;
            height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            opacity: 0 !important;
            visibility: hidden !important;
            pointer-events: none !important;
        }
        section[data-testid="stSidebar"] [data-testid="stRadio"] label[data-testid="stRadioOption"],
        section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label {
            width: 100% !important;
            padding: 10px 14px !important;
            border-radius: 12px !important;
            margin-bottom: 5px !important;
            font-size: 0.90rem !important;
            font-weight: 500 !important;
            border: 1px solid transparent !important;
            transition: all 0.15s ease !important;
            cursor: pointer !important;
            background: transparent !important;
            color: #475569 !important;
            display: flex !important;
            align-items: center !important;
        }
        section[data-testid="stSidebar"] [data-testid="stRadio"] label[data-testid="stRadioOption"]:hover,
        section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:hover {
            background: #f8fafc !important;
            border-color: #e2e8f0 !important;
            color: #0f172a !important;
        }
        section[data-testid="stSidebar"] [data-testid="stRadio"] label[data-testid="stRadioOption"][data-selected="true"],
        section[data-testid="stSidebar"] [data-testid="stRadio"] label[data-testid="stRadioOption"]:has(input:checked),
        section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) {
            background: #ecfdf5 !important;
            border: 1px solid #a7f3d0 !important;
            color: #065f46 !important;
            font-weight: 700 !important;
            box-shadow: 0 1px 4px rgba(5, 150, 105, 0.08) !important;
        }
        section[data-testid="stSidebar"] [data-testid="stRadio"] label[data-testid="stRadioOption"][data-selected="true"] p,
        section[data-testid="stSidebar"] [data-testid="stRadio"] label[data-testid="stRadioOption"]:has(input:checked) p,
        section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) p {
            color: #065f46 !important;
            font-weight: 700 !important;
        }
        section[data-testid="stSidebar"] [data-testid="stRadio"] label[data-testid="stRadioOption"] > div {
            width: 100% !important;
            display: flex !important;
            align-items: center !important;
        }
        section[data-testid="stSidebar"] [data-testid="stRadio"] label[data-testid="stRadioOption"] [data-testid="stMarkdownContainer"] {
            width: 100% !important;
        }
        section[data-testid="stSidebar"] [data-testid="stRadio"] label[data-testid="stRadioOption"] [data-testid="stMarkdownContainer"] p {
            margin: 0 !important;
            line-height: 1.4 !important;
        }

        /* Unified Lucide SVG Navigation Icons via CSS pseudo-elements */
        section[data-testid="stSidebar"] [data-testid="stRadio"] label[data-testid="stRadioOption"]::before {
            content: "";
            display: inline-block;
            width: 18px;
            height: 18px;
            margin-inline-end: 10px;
            background-size: contain;
            background-repeat: no-repeat;
            background-position: center;
            flex-shrink: 0;
            transition: transform 0.15s ease;
        }

        /* 1. Overview Dashboard (Home Icon) */
        section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > *:nth-child(1) label::before {
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z'/%3E%3Cpolyline points='9 22 9 12 15 12 15 22'/%3E%3C/svg%3E");
        }
        section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > *:nth-child(1) label:has(input:checked)::before,
        section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > *:nth-child(1) label[data-selected="true"]::before {
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23059669' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z'/%3E%3Cpolyline points='9 22 9 12 15 12 15 22'/%3E%3C/svg%3E");
        }

        /* 2. AI Sales Agent (Sparkles Icon) */
        section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > *:nth-child(2) label::before {
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z'/%3E%3Cpath d='M5 3v4'/%3E%3Cpath d='M19 17v4'/%3E%3Cpath d='M3 5h4'/%3E%3Cpath d='M17 19h4'/%3E%3C/svg%3E");
        }
        section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > *:nth-child(2) label:has(input:checked)::before,
        section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > *:nth-child(2) label[data-selected="true"]::before {
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23059669' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z'/%3E%3Cpath d='M5 3v4'/%3E%3Cpath d='M19 17v4'/%3E%3Cpath d='M3 5h4'/%3E%3Cpath d='M17 19h4'/%3E%3C/svg%3E");
        }

        /* 3. Dataset Ingestion & Validation (Database Icon) */
        section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > *:nth-child(3) label::before {
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cellipse cx='12' cy='5' rx='9' ry='3'/%3E%3Cpath d='M3 5V19A9 3 0 0 0 21 19V5'/%3E%3Cpath d='M3 12A9 3 0 0 0 21 12'/%3E%3C/svg%3E");
        }
        section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > *:nth-child(3) label:has(input:checked)::before,
        section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > *:nth-child(3) label[data-selected="true"]::before {
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23059669' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cellipse cx='12' cy='5' rx='9' ry='3'/%3E%3Cpath d='M3 5V19A9 3 0 0 0 21 19V5'/%3E%3Cpath d='M3 12A9 3 0 0 0 21 12'/%3E%3C/svg%3E");
        }

        /* 4. Memory Explorer (Brain Icon) with Section Divider */
        section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > *:nth-child(4) {
            margin-top: 14px !important;
            padding-top: 12px !important;
            border-top: 1px dashed #e2e8f0 !important;
        }
        section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > *:nth-child(4) label::before {
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z'/%3E%3Cpath d='M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z'/%3E%3Cpath d='M12 5v13'/%3E%3C/svg%3E");
        }
        section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > *:nth-child(4) label:has(input:checked)::before,
        section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > *:nth-child(4) label[data-selected="true"]::before {
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23059669' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z'/%3E%3Cpath d='M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z'/%3E%3Cpath d='M12 5v13'/%3E%3C/svg%3E");
        }

        /* 5. Security & Audit Trail (Shield Check Icon) */
        section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > *:nth-child(5) label::before {
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z'/%3E%3Cpath d='m9 12 2 2 4-4'/%3E%3C/svg%3E");
        }
        section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > *:nth-child(5) label:has(input:checked)::before,
        section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > *:nth-child(5) label[data-selected="true"]::before {
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23059669' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z'/%3E%3Cpath d='m9 12 2 2 4-4'/%3E%3C/svg%3E");
        }

        /* KPI Values — sized to fit full currency strings cleanly without truncation */
        .kpi-value {
            font-size: clamp(1.15rem, 1.4vw, 1.55rem) !important;
            font-weight: 800 !important;
            color: #0f172a !important;
            line-height: 1.15 !important;
            white-space: nowrap !important;
            overflow: visible !important;
        }
        .kpi-card-hero .kpi-value {
            font-size: clamp(1.15rem, 1.4vw, 1.55rem) !important;
            color: #ffffff !important;
        }

        /* Analytics Card Surface (Ref. Image 3) */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: #ffffff !important;
            border: 1px solid #e8e5df !important;
            border-radius: 14px !important;
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.03) !important;
            padding: 16px 18px 12px 18px !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"] > div {
            gap: 10px !important;
        }
        .analytics-card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
        }
        .analytics-card-title {
            font-size: 1.05rem;
            font-weight: 700;
            color: #0f172a;
        }
        .analytics-legend {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 0.78rem;
            color: #64748b;
        }

        /* Reference Table Surface (Ref. Image 3 Bottom Card) */
        .ref-table-wrap {
            overflow-x: auto;
            margin-top: 10px;
        }
        .ref-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.88rem;
        }
        .ref-table th {
            background: #f8fafc;
            color: #64748b;
            font-weight: 600;
            font-size: 0.80rem;
            padding: 12px 16px;
            border-bottom: 1px solid #e8e5df;
            text-align: inherit;
        }
        .ref-table td {
            padding: 14px 16px;
            border-bottom: 1px solid #f1f5f9;
            color: #0f172a;
            vertical-align: middle;
        }
        .ref-table tr:hover td {
            background: #fafaf9;
        }
        .ref-table tr:last-child td {
            border-bottom: none;
        }

        /* Hide technical action menu in VegaLite charts */
        [data-testid="stVegaLiteChart"] summary,
        [data-testid="stArrowVegaLiteChart"] summary {
            display: none !important;
        }
    """

    if lang == "ar":
        return (
            "<style>\n"
            "@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');\n"
            + common_css
            + """
        /* Arabic Typography — Applied strictly to text elements to avoid clobbering icon fonts */
        html, body, .main, [data-testid="stSidebar"],
        h1, h2, h3, h4, h5, h6,
        p, .stMarkdown, .stText, .stCaption,
        label, .metric-label, .metric-delta, .kpi-title {
            font-family: 'Cairo', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        }

        /* Arabic RTL Layout: Move Sidebar to the RIGHT (Ref. Image 3) */
        @media (min-width: 768px) {
            [data-testid="stAppViewContainer"] {
                flex-direction: row-reverse !important;
            }
        }
        section[data-testid="stSidebar"]:not([data-collapsed="true"]):not([aria-expanded="false"]) {
            border-left: 1px solid #ebe8e2 !important;
            border-right: none !important;
            width: 260px !important;
            min-width: 260px !important;
            max-width: 260px !important;
            background: #ffffff !important;
            display: block !important;
            visibility: visible !important;
        }

        /* Collapsed Sidebar: Completely remove from layout and pointer-tree to prevent interception */
        section[data-testid="stSidebar"][data-collapsed="true"],
        section[data-testid="stSidebar"][aria-expanded="false"] {
            display: none !important;
            width: 0 !important;
            min-width: 0 !important;
            max-width: 0 !important;
            pointer-events: none !important;
            visibility: hidden !important;
            transform: none !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        /* Arabic Collapsed Sidebar Expand Button on Top-Right */
        [data-testid="stExpandSidebarButton"],
        [data-testid="stSidebarCollapsedControl"] {
            position: fixed !important;
            top: 0.65rem !important;
            right: 1rem !important;
            left: auto !important;
            z-index: 999999 !important;
            pointer-events: auto !important;
            display: flex !important;
            visibility: visible !important;
            background: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 8px !important;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08) !important;
            color: #059669 !important;
        }
        [data-testid="stExpandSidebarButton"] button {
            color: #059669 !important;
        }

        /* Container Direction & Alignment */
        .main .block-container,
        section[data-testid="stSidebar"],
        .stChatMessage,
        .stMarkdown, h1, h2, h3, h4, h5, h6, p, .stCaption {
            direction: rtl;
            text-align: right;
        }

        /* Strict LTR isolation for numbers, monetary values, codes, and paths */
        code, pre, .kpi-value, .metric-value, .status-badge, [data-testid="stCodeBlock"] {
            direction: ltr !important;
            text-align: left !important;
            display: inline-block;
            unicode-bidi: isolate;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        }

        /* DataTables & DataFrames remain legible in standard layout */
        [data-testid="stDataFrame"], [data-testid="stTable"],
        [data-testid="stVegaLiteChart"], [data-testid="stArrowVegaLiteChart"] {
            direction: ltr !important;
            text-align: left !important;
        }

        /* Expanders */
        [data-testid="stExpander"] details summary {
            direction: rtl;
            text-align: right;
        }
        </style>
        """
        )
    else:
        return (
            "<style>\n"
            "@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');\n"
            + common_css
            + """
        /* English Typography */
        html, body, .main, [data-testid="stSidebar"],
        h1, h2, h3, h4, h5, h6,
        p, .stMarkdown, .stText, .stCaption,
        label, .metric-label, .metric-delta, .kpi-title {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        }

        /* English LTR Layout: Sidebar on LEFT */
        @media (min-width: 768px) {
            [data-testid="stAppViewContainer"] {
                flex-direction: row !important;
            }
        }
        section[data-testid="stSidebar"]:not([data-collapsed="true"]):not([aria-expanded="false"]) {
            border-right: 1px solid #ebe8e2 !important;
            border-left: none !important;
            width: 260px !important;
            min-width: 260px !important;
            max-width: 260px !important;
            background: #ffffff !important;
            display: block !important;
            visibility: visible !important;
        }

        /* Collapsed Sidebar: Completely remove from layout and pointer-tree */
        section[data-testid="stSidebar"][data-collapsed="true"],
        section[data-testid="stSidebar"][aria-expanded="false"] {
            display: none !important;
            width: 0 !important;
            min-width: 0 !important;
            max-width: 0 !important;
            pointer-events: none !important;
            visibility: hidden !important;
            transform: none !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        /* English Collapsed Sidebar Expand Button on Top-Left */
        [data-testid="stExpandSidebarButton"],
        [data-testid="stSidebarCollapsedControl"] {
            position: fixed !important;
            top: 0.65rem !important;
            left: 1rem !important;
            right: auto !important;
            z-index: 999999 !important;
            pointer-events: auto !important;
            display: flex !important;
            visibility: visible !important;
            background: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 8px !important;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08) !important;
            color: #059669 !important;
        }
        [data-testid="stExpandSidebarButton"] button {
            color: #059669 !important;
        }

        .main .block-container,
        section[data-testid="stSidebar"],
        .stChatMessage,
        .stMarkdown, h1, h2, h3, h4, h5, h6, p, .stCaption {
            direction: ltr;
            text-align: left;
        }
        </style>
        """
        )

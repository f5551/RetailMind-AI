// ==============================================================================
// RetailMind AI — GitHub Pages Interactive Script
// Bilingual Support (Arabic RTL & English LTR)
// ==============================================================================

const TRANSLATIONS = {
  ar: {
    tagline: "وكيل الذكاء الاصطناعي لتحليل بيانات المبيعات التجارية",
    github_repo: "مستودع المشروع",
    banner_title: "بوابة التوثيق التفاعلية على GitHub Pages:",
    banner_desc: "تعرض هذه الصفحة معمارية النظام، ومواصفات الأدوات، ونموذج البيانات المعياري مع فحص حسابي محلي. يتطلب تشغيل وكيل Gemini الذكي الكامل مع خادم بروتوكول MCP والذاكرة المستدامة تشغيل خادم Python الخلفي.",
    hero_status: "مشروع التخرج المعتمد — 183 اختباراً ناجحاً بنسبة 100%",
    hero_heading: "تحليل بيانات مبيعات التجزئة بدقة استدلالية وأمان صارم",
    hero_lead: "RetailMind AI هو وكيل استدلال فردي (Single Reasoning Agent) مبني لتحليل ملفات مبيعات التجزئة CSV. يربط نماذج Google Gemini (gemini-3.1-flash-lite) ببروتوكول سياق النموذج الرسمي (Model Context Protocol - MCP)، ويقدم تحليلات مالية دقيقة، وكشفاً للأنماط الشاذة، وتوليد تقارير محكومة بموافقة بشرية صريحة.",
    stat_tools: "أدوات MCP مدمجة",
    stat_budget: "سقف الميزانية لكل مهمة",
    stat_tests: "اختبار مؤتمت ناجح",
    stat_coverage: "تغطية الكود الأساسي",
    pillars_title: "ركائز المعمارية والحوكمة",
    pillars_sub: "تصميم هندسي متين يلبي كافة متطلبات Capstone الصارمة",
    pillar_agent_title: "وكيل استدلال فردي وحقيقي",
    pillar_agent_desc: "حلقة استدلال حقيقية تستدعي الأدوات ديناميكياً عبر Gemini API (google-genai). آلية إيقاف ثلاثية صارمة: الحد الأقصى للجولات (8 جولات)، وسقف التكلفة ($0.10)، والإجابة النهائية للنموذج.",
    pillar_mcp_title: "بروتوكول MCP القياسي",
    pillar_mcp_desc: "ربط 8 أدوات برمجية دقيقة عبر خادم وعميل MCP رسمي (mcp==2.3.0) يعمل عبر subprocess وstdio، مع عزل كامل لمعاملات الجلسات ومطابقة الهوية الموثوقة.",
    pillar_security_title: "أمان صارم وتفويض كتابة",
    pillar_security_desc: "سياسة ask_on_write: التحليل المالي يعمل تلقائياً، بينما توليد التقارير وتصديرها يتطلب موافقة بشرية صريحة محكومة بكود برمجي عبر تذاكر مشفرة في SQLite وسجل تدقيق غير قابل للتعديل.",
    pillar_memory_title: "ذاكرة SQLite المستدامة",
    pillar_memory_desc: "تخزين دائم للسياقات التحليلية وسجلات التدقيق في SQLite WAL، مع إثبات تعافي الذاكرة واستعادتها بنجاح تام بعد إعادة تشغيل العملية بالكامل.",
    tools_title: "أدوات التحليل الثمانية (MCP Tools Contract)",
    tools_sub: "أدوات حسابية قطعية خالية من أي هلوسة أو استنتاجات غير مثبتة",
    th_tool: "الأداة",
    th_type: "النوع والترخيص",
    th_desc: "الوصف الوظيفي والناتج الحسابي",
    td_inspect: "فحص بنية الملف، أسماء الأعمدة، عدد السجلات الصالحة، وفحص سجلات الحجر الصحي.",
    td_validate: "تدقيق نطاقات الأسعار والكميات، رصد الصفوف المكررة، والتأكد من سلامة المعاملات.",
    td_summarize: "احتساب صافي الإيرادات مجموع(الكمية × السعر)، وإجمالي الأرباح، ونسبة هامش الربح الإجمالي بدقة.",
    td_rank: "ترتيب المنتجات تصاعدياً أو تنازلياً حسب الإيرادات والكميات، وحصة كل منتج من المبيعات.",
    td_compare: "مقارنة فترتين زمنيتين، رصد تباين التكاليف، واحتساب معدل النمو النسبي بدقة صفرية.",
    td_anomalies: "كشف القيم المتطرفة إحصائياً باستخدام أسلوب المدى الربيعي الديناميكي (Dynamic IQR).",
    td_segment: "تجزئة المبيعات والإيرادات حسب الفئة أو المنطقة أو مجموعات المنتجات الفرعية.",
    td_report: "صياغة تقرير مالي وتنفيذي وتصديره إلى صيغة Markdown محكمة؛ يستلزم موافقة المستخدم الصريحة.",
    sample_title: "مجموعة البيانات المعتمدة للاختبار القياسي (Benchmark)",
    sample_sub: "مجموعة synthetic_sales.csv المعتمدة لمطابقة الحسابات المالية",
    lbl_revenue: "صافي الإيرادات:",
    lbl_profit: "صافي الربح:",
    lbl_margin: "هامش الربح:",
    lbl_units: "إجمالي الوحدات:",
    lbl_orders: "إجمالي الطلبات:",
    docs_title: "دليل التشغيل المحلي ووثائق المشروع",
    docs_sub: "روابط ومستندات الحوكمة الرسمية في المستودع",
    qs_heading: "تشغيل الوكيل كاملاً على جهازك المحلي عبر Python:",
    spec_desc: "المواصفة الرسمية من صفحة واحدة",
    cost_desc: "تحليل التكاليف وحساب أسعار الرموز",
    req_desc: "عقد المتطلبات غير القابل للتعديل",
    arch_desc: "معمارية النظام وحدود الثقة"
  },
  en: {
    tagline: "Intelligent Retail Sales Analytics Agent",
    github_repo: "Project Repository",
    banner_title: "Interactive GitHub Pages Documentation Portal:",
    banner_desc: "This page presents the system architecture, tool contracts, and benchmark data model with client-side verification. Running the complete live Gemini reasoning agent with MCP subprocesses and persistent SQLite memory requires running the Python backend.",
    hero_status: "Approved Capstone Project — 183 Automated Tests Passing (100%)",
    hero_heading: "Rigorous Retail Sales Analytics with Reasoning Precision and Guardrails",
    hero_lead: "RetailMind AI is a single-agent conversational analytics system designed for CSV retail sales data. It pairs Google Gemini (gemini-3.1-flash-lite) with the Model Context Protocol (MCP) to deliver verifiable insights, statistical anomaly detection, performance rankings, and approval-gated report generation.",
    stat_tools: "Official MCP Tools",
    stat_budget: "Per-Task Budget Ceiling",
    stat_tests: "Passing Automated Tests",
    stat_coverage: "Core Backend Coverage",
    pillars_title: "Architectural & Governance Pillars",
    pillars_sub: "Engineered to satisfy all capstone acceptance criteria with zero compromises",
    pillar_agent_title: "Authentic Single Reasoning Agent",
    pillar_agent_desc: "True tool-calling reasoning loop using Gemini API via google-genai. Enforces tripartite loop termination: max_turns (8), budget cap ($0.10 USD), and model final answer.",
    pillar_mcp_title: "Standard Model Context Protocol",
    pillar_mcp_desc: "Connects 8 deterministic tools via official MCP server & client (mcp==2.3.0) communicating over subprocess stdio with trusted session identity isolation.",
    pillar_security_title: "Strict Guardrails & Write Approval",
    pillar_security_desc: "ask_on_write policy: read-only analysis runs autonomously; report generation requires explicit human approval enforced in code via cryptographic SQLite capability tickets.",
    pillar_memory_title: "Persistent SQLite Memory",
    pillar_memory_desc: "Durable analytical memory and append-only audit trail in SQLite WAL, proven to survive complete process restarts and recover isolated session context.",
    tools_title: "The 8 Model Context Protocol Tools",
    tools_sub: "Deterministic arithmetic engines free of hallucinations or invented data",
    th_tool: "Tool Name",
    th_type: "Type & Policy",
    th_desc: "Functional Description & Arithmetic Output",
    td_inspect: "Inspects dataset structure, column headers, valid rows, and quarantined invalid entries.",
    td_validate: "Validates price and quantity ranges, identifies duplicate rows, and verifies transaction integrity.",
    td_summarize: "Calculates net revenue as sum(quantity * unit_price), profit, and gross margin percentage.",
    td_rank: "Ranks products by sales revenue and quantity sold with individual revenue share percentages.",
    td_compare: "Compares performance across two distinct periods, calculating zero-base growth rates.",
    td_anomalies: "Detects statistical price outliers using dynamic Interquartile Range (IQR) analysis.",
    td_segment: "Segments sales performance and revenue distribution across categories or geographical regions.",
    td_report: "Drafts executive financial markdown report; requires explicit human-in-the-loop approval.",
    sample_title: "Approved Benchmark Dataset Preview",
    sample_sub: "synthetic_sales.csv benchmark fixture used for financial accuracy verification",
    lbl_revenue: "Net Revenue:",
    lbl_profit: "Net Profit:",
    lbl_margin: "Gross Margin:",
    lbl_units: "Total Units:",
    lbl_orders: "Total Orders:",
    docs_title: "Local Setup Guide & Project Documentation",
    docs_sub: "Official repository governance links and architecture documents",
    qs_heading: "Run the Full AI Agent Locally via Python:",
    spec_desc: "Official One-Page Specification",
    cost_desc: "Token Pricing & Monthly Projections",
    req_desc: "Immutable Capstone Contract",
    arch_desc: "System Boundaries & Threat Model"
  }
};

let currentLang = localStorage.getItem("retailmind_pages_lang") || "ar";

function applyLanguage(lang) {
  currentLang = lang;
  localStorage.setItem("retailmind_pages_lang", lang);

  const isAr = lang === "ar";
  document.documentElement.lang = lang;
  document.documentElement.dir = isAr ? "rtl" : "ltr";

  // Update button text
  const btnText = document.getElementById("langBtnText");
  if (btnText) {
    btnText.textContent = isAr ? "English" : "العربية";
  }

  // Update all translatable elements
  const dict = TRANSLATIONS[lang] || TRANSLATIONS.ar;
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    if (dict[key]) {
      el.textContent = dict[key];
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  applyLanguage(currentLang);

  const toggleBtn = document.getElementById("langToggleBtn");
  if (toggleBtn) {
    toggleBtn.addEventListener("click", () => {
      applyLanguage(currentLang === "ar" ? "en" : "ar");
    });
  }
});

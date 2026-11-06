import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding='utf-8')
from src.retailmind.ui.i18n import t

keys = [
    "ref_pill_revenue_summary",
    "ref_pill_top_products",
    "ref_pill_profit_report",
    "ref_pill_anomalies",
    "ref_date_range_label",
    "ref_performance_title",
    "ref_analyst_title",
    "ref_governance_title",
    "ref_brand_tagline"
]
for k in keys:
    print(f"{k} -> AR: {t(k, 'ar')} | EN: {t(k, 'en')}")

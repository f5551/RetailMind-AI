"""RetailMind AI — Tool Registry and Gemini Tool Conversion Engine."""

from typing import Any, Callable, Dict, List, Optional
from pydantic import ValidationError

from src.retailmind.tools.implementations import (
    compare_periods,
    detect_anomalies,
    generate_report,
    inspect_dataset,
    rank_products,
    segment_sales,
    summarize_sales,
    validate_dataset,
)
from src.retailmind.tools.schemas import (
    ComparePeriodsInput,
    DetectAnomaliesInput,
    GenerateReportInput,
    InspectDatasetInput,
    RankProductsInput,
    SegmentSalesInput,
    SummarizeSalesInput,
    ValidateDatasetInput,
)

TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "inspect_dataset": {
        "function": inspect_dataset,
        "schema": InspectDatasetInput,
        "description": "Returns row count, column inventory, detected types, date range, and preview sample rows.",
        "permission": "read_only",
    },
    "validate_dataset": {
        "function": validate_dataset,
        "schema": ValidateDatasetInput,
        "description": "Audits CSV data against contract rules, returns quarantined rows count, issues, and profit availability.",
        "permission": "read_only",
    },
    "summarize_sales": {
        "function": summarize_sales,
        "schema": SummarizeSalesInput,
        "description": "Calculates total orders, net units sold, net revenue, and profit/margin (if unit cost available).",
        "permission": "read_only",
    },
    "rank_products": {
        "function": rank_products,
        "schema": RankProductsInput,
        "description": "Ranks top or bottom products by revenue, units sold, or profit with revenue share percentages.",
        "permission": "read_only",
    },
    "compare_periods": {
        "function": compare_periods,
        "schema": ComparePeriodsInput,
        "description": "Compares revenue and units between two date windows (Period A vs Period B) with growth deltas.",
        "permission": "read_only",
    },
    "detect_anomalies": {
        "function": detect_anomalies,
        "schema": DetectAnomaliesInput,
        "description": "Identifies statistical outlier sales transactions using Z-score or IQR thresholds.",
        "permission": "read_only",
    },
    "segment_sales": {
        "function": segment_sales,
        "schema": SegmentSalesInput,
        "description": "Segments sales volume and net revenue across dimensions like category or region.",
        "permission": "read_only",
    },
    "generate_report": {
        "function": generate_report,
        "schema": GenerateReportInput,
        "description": "WRITE ACTION (approval required): Writes a formatted executive markdown report to disk in reports/.",
        "permission": "write_approval_required",
    },
}


def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any], is_approved: bool = False) -> Dict[str, Any]:
    """Deterministically validates and executes a tool call."""
    if tool_name not in TOOL_REGISTRY:
        return {
            "status": "error",
            "error_code": "UNKNOWN_TOOL",
            "message": f"Tool '{tool_name}' is not an authorized tool. Allowed tools: {list(TOOL_REGISTRY.keys())}",
        }

    meta = TOOL_REGISTRY[tool_name]
    schema_cls = meta["schema"]
    func: Callable = meta["function"]

    try:
        validated_input = schema_cls.model_validate(arguments)
    except ValidationError as ve:
        return {
            "status": "error",
            "error_code": "INVALID_ARGUMENTS",
            "message": f"Validation failed for tool '{tool_name}' arguments.",
            "details": ve.errors(),
        }

    try:
        if tool_name == "generate_report":
            return func(validated_input, is_approved=is_approved)
        return func(validated_input)
    except Exception as exc:
        return {
            "status": "error",
            "error_code": "TOOL_EXECUTION_EXCEPTION",
            "message": f"Exception raised during '{tool_name}' execution: {str(exc)}",
        }


def get_gemini_tool_declarations() -> List[Dict[str, Any]]:
    """Returns validated Google Gemini FunctionDeclaration dictionaries for all 8 tools."""
    return [
        {
            "name": "inspect_dataset",
            "description": "Returns row count, column inventory, detected types, date range, and preview sample rows.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "session_id": {"type": "STRING", "description": "Active session identifier."},
                    "sample_size": {"type": "INTEGER", "description": "Number of preview sample rows to return."},
                },
                "required": ["session_id"],
            },
        },
        {
            "name": "validate_dataset",
            "description": "Audits CSV data against contract rules, returns quarantined rows count, issues, and profit availability.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "session_id": {"type": "STRING", "description": "Active session identifier."},
                },
                "required": ["session_id"],
            },
        },
        {
            "name": "summarize_sales",
            "description": "Calculates total orders, net units sold, net revenue, and profit/margin (if unit cost available).",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "session_id": {"type": "STRING", "description": "Active session identifier."},
                    "start_date": {"type": "STRING", "description": "Optional ISO start date filter (YYYY-MM-DD)."},
                    "end_date": {"type": "STRING", "description": "Optional ISO end date filter (YYYY-MM-DD)."},
                    "group_by": {
                        "type": "STRING",
                        "enum": ["category", "region", "product"],
                        "description": "Optional grouping dimension.",
                    },
                },
                "required": ["session_id"],
            },
        },
        {
            "name": "rank_products",
            "description": "Ranks top or bottom products by revenue, units sold, or profit with revenue share percentages.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "session_id": {"type": "STRING", "description": "Active session identifier."},
                    "metric": {
                        "type": "STRING",
                        "enum": ["revenue", "units", "profit"],
                        "description": "Ranking metric.",
                    },
                    "top_n": {"type": "INTEGER", "description": "Number of top products to return."},
                    "ascending": {"type": "BOOLEAN", "description": "True for lowest/bottom, False for highest/top."},
                },
                "required": ["session_id"],
            },
        },
        {
            "name": "compare_periods",
            "description": "Compares revenue and units between two date windows (Period A vs Period B) with growth deltas.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "session_id": {"type": "STRING", "description": "Active session identifier."},
                    "period_a": {
                        "type": "OBJECT",
                        "description": "Baseline period A window.",
                        "properties": {
                            "start_date": {"type": "STRING", "description": "Start date (YYYY-MM-DD)."},
                            "end_date": {"type": "STRING", "description": "End date (YYYY-MM-DD)."},
                        },
                        "required": ["start_date", "end_date"],
                    },
                    "period_b": {
                        "type": "OBJECT",
                        "description": "Comparison period B window.",
                        "properties": {
                            "start_date": {"type": "STRING", "description": "Start date (YYYY-MM-DD)."},
                            "end_date": {"type": "STRING", "description": "End date (YYYY-MM-DD)."},
                        },
                        "required": ["start_date", "end_date"],
                    },
                },
                "required": ["session_id", "period_a", "period_b"],
            },
        },
        {
            "name": "detect_anomalies",
            "description": "Identifies statistical outlier sales transactions using Z-score or IQR thresholds.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "session_id": {"type": "STRING", "description": "Active session identifier."},
                    "column": {
                        "type": "STRING",
                        "enum": ["revenue", "quantity", "unit_price"],
                        "description": "Column to inspect for outliers.",
                    },
                    "method": {
                        "type": "STRING",
                        "enum": ["zscore", "iqr"],
                        "description": "Outlier detection algorithm.",
                    },
                    "threshold": {"type": "NUMBER", "description": "Statistical threshold sensitivity."},
                },
                "required": ["session_id"],
            },
        },
        {
            "name": "segment_sales",
            "description": "Segments sales volume and net revenue across dimensions like category or region.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "session_id": {"type": "STRING", "description": "Active session identifier."},
                    "dimension": {
                        "type": "STRING",
                        "enum": ["category", "region"],
                        "description": "Primary segment dimension.",
                    },
                    "secondary_dimension": {
                        "type": "STRING",
                        "enum": ["category", "region"],
                        "description": "Optional secondary dimension.",
                    },
                },
                "required": ["session_id", "dimension"],
            },
        },
        {
            "name": "generate_report",
            "description": "WRITE ACTION (approval required): Writes a formatted executive markdown report to disk in reports/.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "session_id": {"type": "STRING", "description": "Active session identifier."},
                    "title": {"type": "STRING", "description": "Executive report title."},
                    "sections": {
                        "type": "ARRAY",
                        "description": "Report content sections.",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "heading": {"type": "STRING", "description": "Section heading."},
                                "content": {"type": "STRING", "description": "Section narrative content."},
                            },
                            "required": ["heading", "content"],
                        },
                    },
                    "format": {
                        "type": "STRING",
                        "enum": ["markdown", "csv"],
                        "description": "Report output format.",
                    },
                    "approval_token": {
                        "type": "STRING",
                        "description": "One-time session confirmation authorization token.",
                    },
                },
                "required": ["session_id", "title", "sections"],
            },
        },
    ]

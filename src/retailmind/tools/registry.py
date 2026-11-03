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
    """Converts Pydantic schemas into Google Gemini FunctionDeclaration dictionaries."""
    declarations = []
    for name, meta in TOOL_REGISTRY.items():
        schema_dict = meta["schema"].model_json_schema()
        # Clean schema for Gemini API
        properties = {}
        for prop_name, prop_meta in schema_dict.get("properties", {}).items():
            clean_prop = {
                "type": prop_meta.get("type", "string").upper(),
                "description": prop_meta.get("description", ""),
            }
            if "enum" in prop_meta:
                clean_prop["enum"] = prop_meta["enum"]
            properties[prop_name] = clean_prop

        decl = {
            "name": name,
            "description": meta["description"],
            "parameters": {
                "type": "OBJECT",
                "properties": properties,
                "required": schema_dict.get("required", []),
            },
        }
        declarations.append(decl)
    return declarations

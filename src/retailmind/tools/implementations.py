"""RetailMind AI — Deterministic Python Tool Implementations.

All calculations are performed deterministically with zero LLM math hallucinations.
"""

import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from src.retailmind.config import settings
import csv
import logging
from src.retailmind.data.loader import DatasetManager, ProcessedDataset, sanitize_cell_value
from src.retailmind.tools.schemas import (
    AnomalyItem,
    ComparePeriodsInput,
    ComparePeriodsOutput,
    DetectAnomaliesInput,
    DetectAnomaliesOutput,
    GenerateReportInput,
    GenerateReportOutput,
    GroupSummary,
    InspectDatasetInput,
    InspectDatasetOutput,
    ProductRankItem,
    RankProductsInput,
    RankProductsOutput,
    SegmentItem,
    SegmentSalesInput,
    SegmentSalesOutput,
    SummarizeSalesInput,
    SummarizeSalesOutput,
    ValidateDatasetInput,
    ValidateDatasetOutput,
    ValidationIssueItem,
)


logger = logging.getLogger("retailmind.tools.implementations")


def count_distinct_orders(df: pd.DataFrame) -> int:
    """Computes distinct order count: distinct non-empty order_ids, plus rows lacking an order_id."""
    if len(df) == 0:
        return 0
    if "order_id" in df.columns:
        valid_orders = df["order_id"].dropna()
        valid_orders = valid_orders[valid_orders.astype(str).str.strip().ne("")]
        distinct_named = int(valid_orders.nunique())
        missing_count = len(df) - len(valid_orders)
        return distinct_named + missing_count
    return len(df)


def inspect_dataset(args: InspectDatasetInput) -> Dict[str, Any]:
    """Inspects structural overview and metadata of the uploaded dataset."""
    dataset = DatasetManager.get_dataset(args.session_id)
    raw_df = dataset.raw_df

    detected_types = {col: str(raw_df[col].dtype) for col in raw_df.columns}
    sample_rows = raw_df.head(args.sample_size).to_dict(orient="records")

    output = InspectDatasetOutput(
        status="success",
        total_rows=len(raw_df),
        columns=raw_df.columns.tolist(),
        detected_types=detected_types,
        date_range={"start_date": dataset.date_range[0], "end_date": dataset.date_range[1]},
        sample_rows=sample_rows,
    )
    return output.model_dump()


def validate_dataset(args: ValidateDatasetInput) -> Dict[str, Any]:
    """Audits schema compliance, quarantined rows, and profit availability."""
    dataset = DatasetManager.get_dataset(args.session_id)

    issues = [
        ValidationIssueItem(
            row_index=i.row_index,
            issue_type=i.issue_type,
            column=i.column,
            details=i.details,
        )
        for i in dataset.issues
    ]

    output = ValidateDatasetOutput(
        status="success",
        is_valid=len(dataset.issues) == 0,
        total_rows=len(dataset.raw_df),
        valid_rows=len(dataset.valid_df),
        quarantined_rows=len(dataset.quarantined_df),
        has_cost_data=dataset.has_cost_data,
        duplicate_rows_count=dataset.duplicate_rows_count,
        issues_detected=issues,
    )
    return output.model_dump()


def summarize_sales(args: SummarizeSalesInput) -> Dict[str, Any]:
    """Computes exact sales totals, units, and net revenue with deterministic math."""
    dataset = DatasetManager.get_dataset(args.session_id)
    df = dataset.valid_df.copy()

    # Apply date filters if provided
    if args.start_date:
        df = df[df["date"] >= args.start_date]
    if args.end_date:
        df = df[df["date"] <= args.end_date]

    total_orders = count_distinct_orders(df)
    net_units = float(df["quantity"].sum()) if len(df) > 0 else 0.0
    net_revenue = float(df["line_revenue"].sum()) if len(df) > 0 else 0.0

    if not math.isfinite(net_units) or not math.isfinite(net_revenue):
        raise ValueError("Non-finite numerical result detected in sales summary.")

    # Profit and margin policy: only if cost is present for all valid rows
    if dataset.has_cost_data and len(df) > 0:
        net_profit = float(df["line_profit"].sum())
        if not math.isfinite(net_profit):
            raise ValueError("Non-finite profit detected in sales summary.")
        margin_pct = float((net_profit / net_revenue * 100.0) if net_revenue != 0 else 0.0)
        profit_metrics = {
            "available": True,
            "net_profit": round(net_profit, 2),
            "gross_margin_percentage": round(margin_pct, 2),
        }
    else:
        profit_metrics = {
            "available": False,
            "net_profit": "UNAVAILABLE",
            "gross_margin_percentage": "UNAVAILABLE",
            "reason": "unit_cost column is missing or incomplete in dataset",
        }

    groups_summary = None
    if args.group_by and args.group_by in df.columns and total_orders > 0:
        grouped = df.groupby(args.group_by)
        groups_list = []
        for name, g in grouped:
            g_units = float(g["quantity"].sum())
            g_rev = float(g["line_revenue"].sum())
            g_profit = float(g["line_profit"].sum()) if dataset.has_cost_data else None
            groups_list.append(
                GroupSummary(
                    group_name=str(name),
                    net_units=round(g_units, 2),
                    net_revenue=round(g_rev, 2),
                    net_profit=round(g_profit, 2) if g_profit is not None else None,
                )
            )
        groups_summary = groups_list

    output = SummarizeSalesOutput(
        status="success",
        date_filter={"start_date": args.start_date, "end_date": args.end_date},
        total_orders=total_orders,
        net_units=round(net_units, 2),
        net_revenue=round(net_revenue, 2),
        currency="USD",
        profit_metrics=profit_metrics,
        groups=groups_summary,
    )
    return output.model_dump()


def rank_products(args: RankProductsInput) -> Dict[str, Any]:
    """Ranks products by revenue, units, or profit with exact revenue share."""
    dataset = DatasetManager.get_dataset(args.session_id)
    df = dataset.valid_df.copy()

    if len(df) == 0:
        return RankProductsOutput(
            status="success", metric=args.metric, order="ascending" if args.ascending else "descending", rankings=[]
        ).model_dump()

    total_revenue = float(df["line_revenue"].sum())

    # Group by product
    agg_dict = {
        "quantity": "sum",
        "line_revenue": "sum",
    }
    if "category" in df.columns:
        agg_dict["category"] = "first"
    if dataset.has_cost_data:
        agg_dict["line_profit"] = "sum"

    grouped = df.groupby("product", as_index=False).agg(agg_dict)

    sort_col = "line_revenue"
    if args.metric == "units":
        sort_col = "quantity"
    elif args.metric == "profit":
        if not dataset.has_cost_data:
            raise ValueError("Cannot rank by profit: unit_cost data is UNAVAILABLE.")
        sort_col = "line_profit"

    grouped = grouped.sort_values(by=sort_col, ascending=args.ascending).head(args.top_n)

    rankings: List[ProductRankItem] = []
    for rank_idx, (_, row) in enumerate(grouped.iterrows(), start=1):
        prod_rev = float(row["line_revenue"])
        share_pct = (prod_rev / total_revenue * 100.0) if total_revenue != 0 else 0.0
        profit_val = round(float(row["line_profit"]), 2) if dataset.has_cost_data else None

        rankings.append(
            ProductRankItem(
                rank=rank_idx,
                product=str(row["product"]),
                category=str(row.get("category", "Uncategorized")),
                units=round(float(row["quantity"]), 2),
                net_revenue=round(prod_rev, 2),
                net_profit=profit_val,
                revenue_share_percentage=round(share_pct, 2),
            )
        )

    output = RankProductsOutput(
        status="success",
        metric=args.metric,
        order="ascending" if args.ascending else "descending",
        rankings=rankings,
    )
    return output.model_dump()


def compare_periods(args: ComparePeriodsInput) -> Dict[str, Any]:
    """Compares sales volume and revenue delta between two temporal intervals."""
    dataset = DatasetManager.get_dataset(args.session_id)
    df = dataset.valid_df.copy()

    # Period A
    df_a = df[(df["date"] >= args.period_a.start_date) & (df["date"] <= args.period_a.end_date)]
    rev_a = float(df_a["line_revenue"].sum()) if len(df_a) > 0 else 0.0
    units_a = float(df_a["quantity"].sum()) if len(df_a) > 0 else 0.0
    orders_a = count_distinct_orders(df_a)

    # Period B
    df_b = df[(df["date"] >= args.period_b.start_date) & (df["date"] <= args.period_b.end_date)]
    rev_b = float(df_b["line_revenue"].sum()) if len(df_b) > 0 else 0.0
    units_b = float(df_b["quantity"].sum()) if len(df_b) > 0 else 0.0
    orders_b = count_distinct_orders(df_b)

    rev_delta = rev_b - rev_a
    # FIX B2: Mathematical convention for revenue growth from zero / negative base
    if rev_a == 0.0:
        if rev_b == 0.0:
            rev_growth = 0.0
            rev_growth_status = "UNCHANGED_ZERO_BASE"
        else:
            rev_growth = None
            rev_growth_status = "UNDEFINED_PREVIOUS_PERIOD_ZERO"
    elif rev_a < 0.0:
        rev_growth = round((rev_delta / abs(rev_a)) * 100.0, 2)
        rev_growth_status = "NEGATIVE_BASE_REVENUE"
    else:
        rev_growth = round((rev_delta / rev_a) * 100.0, 2)
        rev_growth_status = "CALCULATED"

    units_delta = units_b - units_a
    # FIX B2: Mathematical convention for units growth from zero / negative base
    if units_a == 0.0:
        if units_b == 0.0:
            units_growth = 0.0
            units_growth_status = "UNCHANGED_ZERO_BASE"
        else:
            units_growth = None
            units_growth_status = "UNDEFINED_PREVIOUS_PERIOD_ZERO"
    elif units_a < 0.0:
        units_growth = round((units_delta / abs(units_a)) * 100.0, 2)
        units_growth_status = "NEGATIVE_BASE_UNITS"
    else:
        units_growth = round((units_delta / units_a) * 100.0, 2)
        units_growth_status = "CALCULATED"

    output = ComparePeriodsOutput(
        status="success",
        period_a={
            "label": f"{args.period_a.start_date} to {args.period_a.end_date}",
            "net_revenue": round(rev_a, 2),
            "net_units": round(units_a, 2),
            "orders_count": orders_a,
        },
        period_b={
            "label": f"{args.period_b.start_date} to {args.period_b.end_date}",
            "net_revenue": round(rev_b, 2),
            "net_units": round(units_b, 2),
            "orders_count": orders_b,
        },
        variance={
            "revenue_delta": round(rev_delta, 2),
            "revenue_growth_percentage": rev_growth,
            "revenue_growth_status": rev_growth_status,
            "units_delta": round(units_delta, 2),
            "units_growth_percentage": units_growth,
            "units_growth_status": units_growth_status,
        },
    )
    return output.model_dump()


def detect_anomalies(args: DetectAnomaliesInput) -> Dict[str, Any]:
    """Identifies statistical sales anomalies using Z-score or IQR thresholds."""
    if not math.isfinite(args.threshold) or args.threshold <= 0:
        return {
            "status": "error",
            "error_code": "INVALID_THRESHOLD",
            "message": f"Threshold must be a finite, positive number. Got: {args.threshold}",
        }

    dataset = DatasetManager.get_dataset(args.session_id)
    df = dataset.valid_df.copy()

    if len(df) < 3:
        return DetectAnomaliesOutput(
            status="success",
            method_used=args.method,
            column_analyzed=args.column,
            anomalies_count=0,
            anomalies=[],
        ).model_dump()

    target_series = df["line_revenue"] if args.column == "revenue" else df[args.column].astype(float)
    anomalies: List[AnomalyItem] = []

    if args.method == "zscore":
        mean = float(target_series.mean())
        std = float(target_series.std(ddof=1))
        # Handle zero variance or constant-value column
        if std == 0.0 or not math.isfinite(std):
            return DetectAnomaliesOutput(
                status="success",
                method_used=args.method,
                column_analyzed=args.column,
                anomalies_count=0,
                anomalies=[],
            ).model_dump()

        z_scores = (target_series - mean) / std
        outliers = df[np.abs(z_scores) >= args.threshold]
        for idx in outliers.index:
            row = df.loc[idx]
            score = float(z_scores.loc[idx])
            anomalies.append(
                AnomalyItem(
                    order_id=str(row.get("order_id", f"ROW-{idx}")),
                    date=str(row["date"]),
                    product=str(row["product"]),
                    value=round(float(target_series.loc[idx]), 2),
                    score=round(score, 2),
                    description=f"Transaction value deviates {round(score, 2)} standard deviations from mean ({round(mean, 2)})",
                )
            )
    elif args.method == "iqr":
        q25 = float(target_series.quantile(0.25))
        q75 = float(target_series.quantile(0.75))
        iqr = float(q75 - q25)
        # Handle zero variance or constant-value column
        if iqr == 0.0 or not math.isfinite(iqr):
            return DetectAnomaliesOutput(
                status="success",
                method_used=args.method,
                column_analyzed=args.column,
                anomalies_count=0,
                anomalies=[],
            ).model_dump()

        lower_bound = q25 - (args.threshold * iqr)
        upper_bound = q75 + (args.threshold * iqr)
        outliers = df[(target_series < lower_bound) | (target_series > upper_bound)]
        for idx in outliers.index:
            row = df.loc[idx]
            val = float(target_series.loc[idx])
            score_delta = val - (upper_bound if val > upper_bound else lower_bound)
            anomalies.append(
                AnomalyItem(
                    order_id=str(row.get("order_id", f"ROW-{idx}")),
                    date=str(row["date"]),
                    product=str(row["product"]),
                    value=round(val, 2),
                    score=round(score_delta, 2),
                    description=f"Transaction value outside IQR bounds [{round(lower_bound, 2)}, {round(upper_bound, 2)}] with threshold {args.threshold}",
                )
            )

    output = DetectAnomaliesOutput(
        status="success",
        method_used=args.method,
        column_analyzed=args.column,
        anomalies_count=len(anomalies),
        anomalies=anomalies,
    )
    return output.model_dump()


def segment_sales(args: SegmentSalesInput) -> Dict[str, Any]:
    """Segments sales across business dimensions like category or region."""
    dataset = DatasetManager.get_dataset(args.session_id)
    df = dataset.valid_df.copy()

    if args.dimension not in df.columns:
        raise ValueError(f"Dimension '{args.dimension}' not present in dataset columns.")

    total_revenue = float(df["line_revenue"].sum()) if len(df) > 0 else 0.0

    segments: List[SegmentItem] = []
    for dim_val, group_df in df.groupby(args.dimension):
        rev = float(group_df["line_revenue"].sum())
        units = float(group_df["quantity"].sum())
        orders = count_distinct_orders(group_df)
        pct = (rev / total_revenue * 100.0) if total_revenue != 0 else 0.0
        segments.append(
            SegmentItem(
                name=str(dim_val),
                net_orders=orders,
                net_units=round(units, 2),
                net_revenue=round(rev, 2),
                revenue_percentage=round(pct, 2),
            )
        )

    # Sort descending by net revenue
    segments.sort(key=lambda s: s.net_revenue, reverse=True)

    output = SegmentSalesOutput(
        status="success",
        dimension=args.dimension,
        segments=segments,
    )
    return output.model_dump()


def generate_report(args: GenerateReportInput, is_approved: bool = False) -> Dict[str, Any]:
    """WRITE ACTION: Generates formatted executive report upon explicit human approval."""
    if not is_approved:
        return GenerateReportOutput(
            status="approval_required",
            error_code="PERMISSION_DENIED_PENDING_APPROVAL",
            message="Action 'generate_report' is a write operation and requires explicit human user authorization.",
            approval_status="DENIED_OR_PENDING",
            pending_action={
                "tool": "generate_report",
                "session_id": args.session_id,
                "title": args.title,
                "format": args.format,
            },
        ).model_dump()

    if args.format not in ("markdown", "csv"):
        return {
            "status": "error",
            "error_code": "INVALID_REPORT_FORMAT",
            "message": f"Unsupported report format '{args.format}'. Allowed formats are 'markdown' and 'csv'.",
        }

    # Human authorization verified: execute report persistence
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_title = "".join(c for c in args.title if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_").lower()

    if args.format == "csv":
        filename = f"{safe_title}_{timestamp_str}.csv"
        report_path = settings.reports_dir / filename

        output_rows: List[List[str]] = [
            ["Report Title", sanitize_cell_value(args.title)],
            ["Generated At (UTC)", datetime.now(timezone.utc).isoformat()],
            ["Session ID", sanitize_cell_value(args.session_id)],
            [],
        ]

        for section in args.sections:
            output_rows.append(["Section", sanitize_cell_value(section.heading)])
            output_rows.append(["Summary", sanitize_cell_value(section.content)])
            if section.table_data:
                table_headers = list(section.table_data[0].keys())
                sanitized_headers = [sanitize_cell_value(h) for h in table_headers]
                output_rows.append(sanitized_headers)
                for r in section.table_data:
                    row_vals = [sanitize_cell_value(str(r.get(h, ""))) for h in table_headers]
                    output_rows.append(row_vals)
            output_rows.append([])

        with open(report_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(output_rows)

        file_bytes = report_path.stat().st_size

    else:
        # Markdown format
        filename = f"{safe_title}_{timestamp_str}.md"
        report_path = settings.reports_dir / filename

        content_lines = [
            f"# {args.title}",
            f"*Generated on: {datetime.now(timezone.utc).isoformat()} (UTC)*",
            f"*Session: {args.session_id}*",
            "",
        ]

        for section in args.sections:
            content_lines.append(f"## {section.heading}")
            content_lines.append(section.content)
            content_lines.append("")
            if section.table_data:
                # Format markdown table
                headers = list(section.table_data[0].keys())
                content_lines.append("| " + " | ".join(headers) + " |")
                content_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
                for r in section.table_data:
                    content_lines.append("| " + " | ".join(str(r.get(h, "")) for h in headers) + " |")
                content_lines.append("")

        full_text = "\n".join(content_lines)
        report_path.write_text(full_text, encoding="utf-8")
        file_bytes = len(full_text.encode("utf-8"))

    return GenerateReportOutput(
        status="success",
        file_path=str(report_path.relative_to(settings.workspace_root)),
        file_size_bytes=file_bytes,
        format=args.format,
        created_at=datetime.now(timezone.utc).isoformat(),
        approval_status="APPROVED",
    ).model_dump()

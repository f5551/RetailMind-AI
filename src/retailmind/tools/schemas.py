"""RetailMind AI — Pydantic Schemas for 8 MCP Analytical Tools."""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


# ------------------------------------------------------------------------------
# 1. inspect_dataset
# ------------------------------------------------------------------------------
class InspectDatasetInput(BaseModel):
    session_id: str = Field(..., description="Active session or user identifier mapping to uploaded dataset.")
    sample_size: int = Field(3, ge=1, le=10, description="Number of sample preview rows to return.")


class InspectDatasetOutput(BaseModel):
    status: str = "success"
    total_rows: int
    columns: List[str]
    detected_types: Dict[str, str]
    date_range: Dict[str, Optional[str]]
    sample_rows: List[Dict[str, Any]]


# ------------------------------------------------------------------------------
# 2. validate_dataset
# ------------------------------------------------------------------------------
class ValidateDatasetInput(BaseModel):
    session_id: str = Field(..., description="Active session identifier.")


class ValidationIssueItem(BaseModel):
    row_index: int
    issue_type: str
    column: str
    details: str


class ValidateDatasetOutput(BaseModel):
    status: str = "success"
    is_valid: bool
    total_rows: int
    valid_rows: int
    quarantined_rows: int
    has_cost_data: bool
    duplicate_rows_count: int
    issues_detected: List[ValidationIssueItem]


# ------------------------------------------------------------------------------
# 3. summarize_sales
# ------------------------------------------------------------------------------
class SummarizeSalesInput(BaseModel):
    session_id: str = Field(..., description="Active session identifier.")
    start_date: Optional[str] = Field(None, description="Optional ISO start date filter (YYYY-MM-DD).")
    end_date: Optional[str] = Field(None, description="Optional ISO end date filter (YYYY-MM-DD).")
    group_by: Optional[Literal["category", "region", "product"]] = Field(None, description="Optional aggregation dimension.")


class GroupSummary(BaseModel):
    group_name: str
    net_units: float
    net_revenue: float
    net_profit: Optional[Any] = None


class SummarizeSalesOutput(BaseModel):
    status: str = "success"
    date_filter: Dict[str, Optional[str]]
    total_orders: int
    net_units: float
    net_revenue: float
    currency: str = "USD"
    profit_metrics: Dict[str, Any]
    groups: Optional[List[GroupSummary]] = None


# ------------------------------------------------------------------------------
# 4. rank_products
# ------------------------------------------------------------------------------
class RankProductsInput(BaseModel):
    session_id: str = Field(..., description="Active session identifier.")
    metric: Literal["revenue", "units", "profit"] = Field("revenue", description="Ranking metric.")
    top_n: int = Field(5, ge=1, le=50, description="Number of top products to return.")
    ascending: bool = Field(False, description="True for lowest, False for highest.")


class ProductRankItem(BaseModel):
    rank: int
    product: str
    category: Optional[str] = None
    units: float
    net_revenue: float
    net_profit: Optional[Any] = None
    revenue_share_percentage: float


class RankProductsOutput(BaseModel):
    status: str = "success"
    metric: str
    order: str
    rankings: List[ProductRankItem]


# ------------------------------------------------------------------------------
# 5. compare_periods
# ------------------------------------------------------------------------------
class PeriodWindow(BaseModel):
    start_date: str = Field(..., description="Start date (YYYY-MM-DD).")
    end_date: str = Field(..., description="End date (YYYY-MM-DD).")


class ComparePeriodsInput(BaseModel):
    session_id: str = Field(..., description="Active session identifier.")
    period_a: PeriodWindow = Field(..., description="Baseline period A window.")
    period_b: PeriodWindow = Field(..., description="Comparison period B window.")


class ComparePeriodsOutput(BaseModel):
    status: str = "success"
    period_a: Dict[str, Any]
    period_b: Dict[str, Any]
    variance: Dict[str, Any]


# ------------------------------------------------------------------------------
# 6. detect_anomalies
# ------------------------------------------------------------------------------
class DetectAnomaliesInput(BaseModel):
    session_id: str = Field(..., description="Active session identifier.")
    column: Literal["revenue", "quantity", "unit_price"] = Field("revenue", description="Column to inspect.")
    method: Literal["zscore", "iqr"] = Field("zscore", description="Anomaly detection algorithm.")
    threshold: float = Field(2.5, ge=0.1, le=10.0, description="Outlier sensitivity threshold.")


class AnomalyItem(BaseModel):
    order_id: Optional[str]
    date: str
    product: str
    value: float
    score: float
    description: str


class DetectAnomaliesOutput(BaseModel):
    status: str = "success"
    method_used: str
    column_analyzed: str
    anomalies_count: int
    anomalies: List[AnomalyItem]


# ------------------------------------------------------------------------------
# 7. segment_sales
# ------------------------------------------------------------------------------
class SegmentSalesInput(BaseModel):
    session_id: str = Field(..., description="Active session identifier.")
    dimension: Literal["category", "region"] = Field(..., description="Primary segment dimension.")
    secondary_dimension: Optional[Literal["category", "region"]] = Field(None, description="Optional secondary sub-dimension.")


class SegmentItem(BaseModel):
    name: str
    net_orders: int
    net_units: float
    net_revenue: float
    revenue_percentage: float


class SegmentSalesOutput(BaseModel):
    status: str = "success"
    dimension: str
    segments: List[SegmentItem]


# ------------------------------------------------------------------------------
# 8. generate_report (WRITE ACTION; approval required)
# ------------------------------------------------------------------------------
class ReportSectionItem(BaseModel):
    heading: str
    content: str
    table_data: Optional[List[Dict[str, Any]]] = None


class GenerateReportInput(BaseModel):
    session_id: str = Field(..., description="Active session identifier.")
    title: str = Field(..., description="Executive report title.")
    sections: List[ReportSectionItem] = Field(..., description="Report content sections.")
    format: Literal["markdown", "csv"] = Field("markdown", description="Report output format.")
    approval_token: Optional[str] = Field(None, description="One-time confirmation authorization token.")


class GenerateReportOutput(BaseModel):
    status: str
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    format: Optional[str] = None
    created_at: Optional[str] = None
    approval_status: str
    error_code: Optional[str] = None
    message: Optional[str] = None
    pending_action: Optional[Dict[str, Any]] = None

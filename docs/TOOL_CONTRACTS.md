# RetailMind AI — Tool Contracts & Interface Specification

This document defines the strict API contracts, input schemas, output schemas, execution semantics, and permission levels for all eight tools exposed by RetailMind AI through the Model Context Protocol (MCP).

---

## Tool Overview & Permission Matrix

| # | Tool Name | Permission Level | State Mutation | Description |
|---|---|---|---|---|
| 1 | `inspect_dataset` | `read_only` (Auto) | None | Ingests CSV metadata, column inventory, data types, date boundaries, and sample rows. |
| 2 | `validate_dataset` | `read_only` (Auto) | None | Audits schema compliance, checks missing/invalid columns, identifies quarantined rows. |
| 3 | `summarize_sales` | `read_only` (Auto) | None | Aggregates overall volume, net units, net revenue, and profit/margin (if cost exists). |
| 4 | `rank_products` | `read_only` (Auto) | None | Sorts top-N or bottom-N products by net revenue, volume, or profit. |
| 5 | `compare_periods` | `read_only` (Auto) | None | Evaluates metric variance between two distinct date ranges (Period A vs Period B). |
| 6 | `detect_anomalies` | `read_only` (Auto) | None | Computes statistical outlier transactions using z-score or IQR thresholds. |
| 7 | `segment_sales` | `read_only` (Auto) | None | Breaks down sales metrics across categories, regions, or custom dimensions. |
| 8 | `generate_report` | `write_approval_required` | Creates file | Generates a structured markdown or CSV report in `reports/` upon explicit user consent. |

---

## Common Error Payload
All tools return a consistent error structure when encountering bad inputs, missing datasets, or execution exceptions:

```json
{
  "status": "error",
  "error_code": "INVALID_ARGUMENT | DATASET_NOT_FOUND | VALIDATION_FAILED | PERMISSION_DENIED | ARITHMETIC_ERROR",
  "message": "Human-readable description of the error",
  "details": {}
}
```

---

## 1. `inspect_dataset`

- **Purpose**: Provides quick structural discovery of the dataset without reading all data into prompt context.
- **Permission**: `read_only` (Automatic execution).

### Input Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "session_id": {
      "type": "string",
      "description": "Active session or user identifier mapping to uploaded dataset."
    },
    "sample_size": {
      "type": "integer",
      "default": 3,
      "minimum": 1,
      "maximum": 10,
      "description": "Number of sample preview rows to return."
    }
  },
  "required": ["session_id"],
  "additionalProperties": false
}
```

### Output Schema
```json
{
  "status": "success",
  "total_rows": 1500,
  "columns": ["order_id", "date", "product", "category", "quantity", "unit_price", "unit_cost", "region"],
  "detected_types": {
    "order_id": "string",
    "date": "datetime64",
    "product": "string",
    "category": "string",
    "quantity": "int64",
    "unit_price": "float64",
    "unit_cost": "float64",
    "region": "string"
  },
  "date_range": {
    "start_date": "2026-01-01",
    "end_date": "2026-06-30"
  },
  "sample_rows": [
    {"order_id": "ORD-1001", "date": "2026-01-05", "product": "Mouse", "quantity": 5, "unit_price": 25.0}
  ]
}
```

---

## 2. `validate_dataset`

- **Purpose**: Audits dataset against `docs/CSV_DATA_CONTRACT.md` before performing aggregations.
- **Permission**: `read_only` (Automatic execution).

### Input Schema
```json
{
  "type": "object",
  "properties": {
    "session_id": { "type": "string" }
  },
  "required": ["session_id"],
  "additionalProperties": false
}
```

### Output Schema
```json
{
  "status": "success",
  "is_valid": true,
  "total_rows": 1500,
  "valid_rows": 1495,
  "quarantined_rows": 5,
  "has_cost_data": true,
  "issues_detected": [
    {
      "row_index": 42,
      "issue_type": "MISSING_REQUIRED_FIELD",
      "column": "unit_price",
      "details": "unit_price is null or blank"
    },
    {
      "row_index": 108,
      "issue_type": "INVALID_DATE_FORMAT",
      "column": "date",
      "details": "Value '2026-99-99' failed ISO-8601 parsing"
    }
  ],
  "duplicate_rows_count": 0
}
```

---

## 3. `summarize_sales`

- **Purpose**: Calculates overall transactional totals or totals grouped by a specified column.
- **Permission**: `read_only` (Automatic execution).

### Input Schema
```json
{
  "type": "object",
  "properties": {
    "session_id": { "type": "string" },
    "start_date": { "type": "string", "format": "date", "description": "Optional ISO start date filter." },
    "end_date": { "type": "string", "format": "date", "description": "Optional ISO end date filter." },
    "group_by": {
      "type": "string",
      "enum": ["category", "region", "product"],
      "description": "Optional aggregation dimension."
    }
  },
  "required": ["session_id"],
  "additionalProperties": false
}
```

### Output Schema
```json
{
  "status": "success",
  "date_filter": { "start_date": "2026-01-01", "end_date": "2026-06-30" },
  "total_orders": 1495,
  "net_units": 8420,
  "net_revenue": 215450.00,
  "currency": "USD",
  "profit_metrics": {
    "available": true,
    "net_profit": 86180.00,
    "gross_margin_percentage": 40.00
  },
  "groups": [
    {
      "group_name": "Electronics",
      "net_units": 4500,
      "net_revenue": 150000.00,
      "net_profit": 60000.00
    }
  ]
}
```

---

## 4. `rank_products`

- **Purpose**: Computes top or bottom products ordered by revenue, units sold, or profit.
- **Permission**: `read_only` (Automatic execution).

### Input Schema
```json
{
  "type": "object",
  "properties": {
    "session_id": { "type": "string" },
    "metric": {
      "type": "string",
      "enum": ["revenue", "units", "profit"],
      "default": "revenue"
    },
    "top_n": { "type": "integer", "default": 5, "minimum": 1, "maximum": 50 },
    "ascending": { "type": "boolean", "default": false, "description": "True for bottom performers, False for top performers." }
  },
  "required": ["session_id"],
  "additionalProperties": false
}
```

### Output Schema
```json
{
  "status": "success",
  "metric": "revenue",
  "order": "descending",
  "rankings": [
    {
      "rank": 1,
      "product": "Mechanical Keyboard",
      "category": "Electronics",
      "units": 520,
      "net_revenue": 41600.00,
      "net_profit": 18200.00,
      "revenue_share_percentage": 19.31
    }
  ]
}
```

---

## 5. `compare_periods`

- **Purpose**: Evaluates comparative delta between two temporal intervals.
- **Permission**: `read_only` (Automatic execution).

### Input Schema
```json
{
  "type": "object",
  "properties": {
    "session_id": { "type": "string" },
    "period_a": {
      "type": "object",
      "properties": {
        "start_date": { "type": "string", "format": "date" },
        "end_date": { "type": "string", "format": "date" }
      },
      "required": ["start_date", "end_date"]
    },
    "period_b": {
      "type": "object",
      "properties": {
        "start_date": { "type": "string", "format": "date" },
        "end_date": { "type": "string", "format": "date" }
      },
      "required": ["start_date", "end_date"]
    }
  },
  "required": ["session_id", "period_a", "period_b"],
  "additionalProperties": false
}
```

### Output Schema
```json
{
  "status": "success",
  "period_a": { "label": "2026-01-01 to 2026-01-31", "net_revenue": 32000.00, "net_units": 1200 },
  "period_b": { "label": "2026-02-01 to 2026-02-28", "net_revenue": 38400.00, "net_units": 1440 },
  "variance": {
    "revenue_delta": 6400.00,
    "revenue_growth_percentage": 20.00,
    "units_delta": 240,
    "units_growth_percentage": 20.00
  }
}
```

---

## 6. `detect_anomalies`

- **Purpose**: Flags statistical transaction outliers (e.g. unusually high transaction volume or price anomalies).
- **Permission**: `read_only` (Automatic execution).

### Input Schema
```json
{
  "type": "object",
  "properties": {
    "session_id": { "type": "string" },
    "column": { "type": "string", "enum": ["revenue", "quantity", "unit_price"], "default": "revenue" },
    "method": { "type": "string", "enum": ["zscore", "iqr"], "default": "zscore" },
    "threshold": { "type": "number", "default": 2.5, "minimum": 1.0, "maximum": 5.0 }
  },
  "required": ["session_id"],
  "additionalProperties": false
}
```

### Output Schema
```json
{
  "status": "success",
  "method_used": "zscore",
  "column_analyzed": "revenue",
  "anomalies_count": 2,
  "anomalies": [
    {
      "order_id": "ORD-9999",
      "date": "2026-03-15",
      "product": "Enterprise Server Rack",
      "value": 15000.00,
      "z_score": 4.82,
      "description": "Value exceeds mean + 4.82 standard deviations"
    }
  ]
}
```

---

## 7. `segment_sales`

- **Purpose**: Cross-tabulates sales by business dimensions (e.g. region by category).
- **Permission**: `read_only` (Automatic execution).

### Input Schema
```json
{
  "type": "object",
  "properties": {
    "session_id": { "type": "string" },
    "dimension": { "type": "string", "enum": ["category", "region"], "description": "Primary dimension to segment." },
    "secondary_dimension": { "type": "string", "enum": ["category", "region"], "description": "Optional sub-dimension." }
  },
  "required": ["session_id", "dimension"],
  "additionalProperties": false
}
```

### Output Schema
```json
{
  "status": "success",
  "dimension": "region",
  "segments": [
    {
      "name": "North",
      "net_orders": 600,
      "net_units": 3200,
      "net_revenue": 85000.00,
      "revenue_percentage": 39.45
    },
    {
      "name": "South",
      "net_orders": 895,
      "net_units": 5220,
      "net_revenue": 130450.00,
      "revenue_percentage": 60.55
    }
  ]
}
```

---

## 8. `generate_report` (STATE-CHANGING WRITE ACTION)

- **Purpose**: Formats and persists an executive report to the `reports/` directory.
- **Permission**: `write_approval_required`.
- **Enforcement Mechanism**: The backend agent engine intercepts calls to `generate_report`. If the user has not confirmed execution with `approved: true` for the exact parameters, the tool call is blocked and returns `PERMISSION_DENIED_PENDING_APPROVAL`.

### Input Schema
```json
{
  "type": "object",
  "properties": {
    "session_id": { "type": "string" },
    "title": { "type": "string", "description": "Report title." },
    "sections": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "heading": { "type": "string" },
          "content": { "type": "string" },
          "table_data": {
            "type": "array",
            "items": { "type": "object" },
            "description": "Optional rows for tabular rendering."
          }
        },
        "required": ["heading", "content"]
      }
    },
    "format": { "type": "string", "enum": ["markdown", "csv"], "default": "markdown" },
    "approval_token": {
      "type": "string",
      "description": "One-time session authorization token signed or granted by user."
    }
  },
  "required": ["session_id", "title", "sections"],
  "additionalProperties": false
}
```

### Output Schema (Upon Approval)
```json
{
  "status": "success",
  "file_path": "reports/sales_summary_20261103_0255.md",
  "file_size_bytes": 1420,
  "format": "markdown",
  "created_at": "2026-11-03T02:55:00Z",
  "approval_status": "APPROVED"
}
```

### Output Schema (When Approval Pending or Denied)
```json
{
  "status": "approval_required",
  "error_code": "PERMISSION_DENIED_PENDING_APPROVAL",
  "message": "Action 'generate_report' requires explicit user authorization before writing to disk.",
  "pending_action": {
    "tool": "generate_report",
    "target_file": "reports/sales_summary_20261103_0255.md",
    "title": "Q1 Executive Sales Summary"
  }
}
```

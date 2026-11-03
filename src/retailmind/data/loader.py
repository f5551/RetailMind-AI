"""RetailMind AI — CSV Ingestion, Parsing, and Validation Engine."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd


# Forbidden leading formula injection characters
FORMULA_INJECTION_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


@dataclass
class ValidationIssue:
    row_index: int
    issue_type: str
    column: str
    details: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "row_index": self.row_index,
            "issue_type": self.issue_type,
            "column": self.column,
            "details": self.details,
        }


@dataclass
class ProcessedDataset:
    raw_df: pd.DataFrame
    valid_df: pd.DataFrame
    quarantined_df: pd.DataFrame
    issues: List[ValidationIssue] = field(default_factory=list)
    has_cost_data: bool = False
    duplicate_rows_count: int = 0
    date_range: Tuple[Optional[str], Optional[str]] = (None, None)


def sanitize_cell_value(val: Any) -> Any:
    """Neutralize formula injection by prefixing dangerous characters with an apostrophe.

    Pure numeric strings (e.g. '-1', '-25.50') are preserved as valid numeric transaction data.
    """
    if isinstance(val, str):
        # Pure numeric values are safe numbers, not formula injections
        try:
            float(val)
            return val
        except ValueError:
            pass

        if val.startswith(FORMULA_INJECTION_PREFIXES):
            return "'" + val
    return val


class DatasetManager:
    """Manages active session datasets in memory."""

    _sessions: Dict[str, ProcessedDataset] = {}

    @classmethod
    def register_dataset(cls, session_id: str, csv_path_or_df: Any) -> ProcessedDataset:
        """Loads, cleans, validates, and registers a dataset for a session."""
        if isinstance(csv_path_or_df, (str, Path)):
            path = Path(csv_path_or_df)
            if not path.exists():
                raise FileNotFoundError(f"CSV file not found: {path}")

            # Enforce 10 MB file size limit
            if path.stat().st_size > 10 * 1024 * 1024:
                raise ValueError("File exceeds 10 MB maximum allowed upload size.")

            # Read CSV safely
            try:
                raw_df = pd.read_csv(path, encoding="utf-8", dtype=str)
            except UnicodeDecodeError:
                raw_df = pd.read_csv(path, encoding="latin-1", dtype=str)
        elif isinstance(csv_path_or_df, pd.DataFrame):
            raw_df = csv_path_or_df.astype(str)
        else:
            raise TypeError("Dataset must be a file path or pandas DataFrame.")

        # Enforce 50,000 row count limit
        if len(raw_df) > 50000:
            raise ValueError("Dataset exceeds 50,000 maximum allowed row count limit.")

        processed = cls._process_raw_dataframe(raw_df)
        cls._sessions[session_id] = processed
        return processed

    @classmethod
    def get_dataset(cls, session_id: str) -> ProcessedDataset:
        """Retrieves processed dataset for a session, or raises KeyError."""
        if session_id not in cls._sessions:
            raise KeyError(f"No dataset found for session '{session_id}'. Please upload or inspect dataset first.")
        return cls._sessions[session_id]

    @classmethod
    def clear_session(cls, session_id: str) -> None:
        """Removes a session dataset from memory."""
        cls._sessions.pop(session_id, None)

    @classmethod
    def _process_raw_dataframe(cls, raw_df: pd.DataFrame) -> ProcessedDataset:
        """Audits, normalizes, and segments rows into valid vs quarantined."""
        issues: List[ValidationIssue] = []

        # Standardize column headers: lowercase, stripped
        raw_df.columns = [c.strip().lower() for c in raw_df.columns]

        # Sanitize all text cells against formula injection
        cleaned_df = raw_df.map(sanitize_cell_value)

        # Check required columns
        required_cols = ["date", "product", "quantity", "unit_price"]
        missing_required_cols = [c for c in required_cols if c not in cleaned_df.columns]
        if missing_required_cols:
            raise ValueError(f"Dataset is missing required columns: {missing_required_cols}")

        valid_indices: List[int] = []
        quarantined_indices: List[int] = []

        # Convert and validate row by row
        parsed_dates = []
        parsed_quantities = []
        parsed_unit_prices = []
        parsed_unit_costs = []

        has_cost_col = "unit_cost" in cleaned_df.columns

        for idx, row in cleaned_df.iterrows():
            row_has_issue = False

            # 1. Product check
            prod = str(row.get("product", "")).strip()
            if not prod or prod.lower() in ("nan", "none", "null"):
                issues.append(ValidationIssue(idx, "MISSING_REQUIRED_FIELD", "product", "Product name is empty or null"))
                row_has_issue = True

            # 2. Date check (ISO-8601 YYYY-MM-DD or standard parseable)
            date_raw = str(row.get("date", "")).strip()
            parsed_date_val = None
            try:
                parsed_dt = pd.to_datetime(date_raw, errors="raise")
                parsed_date_val = parsed_dt.strftime("%Y-%m-%d")
            except Exception:
                issues.append(ValidationIssue(idx, "INVALID_DATE_FORMAT", "date", f"Value '{date_raw}' failed ISO-8601 parsing"))
                row_has_issue = True

            # 3. Quantity check (numeric, non-zero)
            qty_raw = str(row.get("quantity", "")).strip()
            parsed_qty_val = None
            try:
                parsed_qty_val = float(qty_raw)
                if parsed_qty_val == 0:
                    issues.append(ValidationIssue(idx, "ZERO_QUANTITY", "quantity", "Quantity cannot be zero"))
                    row_has_issue = True
            except ValueError:
                issues.append(ValidationIssue(idx, "INVALID_NUMERIC", "quantity", f"Quantity '{qty_raw}' is not a valid number"))
                row_has_issue = True

            # 4. Unit Price check (numeric, >= 0)
            price_raw = str(row.get("unit_price", "")).strip()
            parsed_price_val = None
            try:
                parsed_price_val = float(price_raw)
                if parsed_price_val < 0:
                    issues.append(ValidationIssue(idx, "NEGATIVE_PRICE", "unit_price", f"Unit price '{price_raw}' cannot be negative"))
                    row_has_issue = True
            except ValueError:
                issues.append(ValidationIssue(idx, "INVALID_NUMERIC", "unit_price", f"Unit price '{price_raw}' is not a valid number"))
                row_has_issue = True

            # 5. Unit Cost check (optional, if present must be >= 0)
            parsed_cost_val = None
            if has_cost_col:
                cost_raw = str(row.get("unit_cost", "")).strip()
                if cost_raw and cost_raw.lower() not in ("nan", "none", "null"):
                    try:
                        cost_num = float(cost_raw)
                        if cost_num < 0:
                            issues.append(ValidationIssue(idx, "NEGATIVE_COST", "unit_cost", f"Unit cost '{cost_raw}' cannot be negative"))
                            row_has_issue = True
                        else:
                            parsed_cost_val = cost_num
                    except ValueError:
                        issues.append(ValidationIssue(idx, "INVALID_NUMERIC", "unit_cost", f"Unit cost '{cost_raw}' is not numeric"))
                        row_has_issue = True

            if row_has_issue:
                quarantined_indices.append(idx)
            else:
                valid_indices.append(idx)
                parsed_dates.append(parsed_date_val)
                parsed_quantities.append(parsed_qty_val)
                parsed_unit_prices.append(parsed_price_val)
                parsed_unit_costs.append(parsed_cost_val)

        # Create valid DataFrame with strongly typed columns
        if valid_indices:
            valid_df = cleaned_df.loc[valid_indices].copy()
            valid_df["date"] = parsed_dates
            valid_df["quantity"] = parsed_quantities
            valid_df["unit_price"] = parsed_unit_prices
            if has_cost_col:
                valid_df["unit_cost"] = parsed_unit_costs
            # Deterministic calculated column
            valid_df["line_revenue"] = valid_df["quantity"] * valid_df["unit_price"]
        else:
            valid_df = pd.DataFrame(columns=cleaned_df.columns.tolist() + ["line_revenue"])

        quarantined_df = cleaned_df.loc[quarantined_indices].copy() if quarantined_indices else pd.DataFrame(columns=cleaned_df.columns)

        # Check duplicates
        duplicate_count = int(raw_df.duplicated().sum())

        # Check profit availability (must have cost for 100% of valid rows)
        has_cost_data = False
        if has_cost_col and len(valid_df) > 0:
            has_cost_data = valid_df["unit_cost"].notna().all()
            if has_cost_data:
                valid_df["line_profit"] = valid_df["quantity"] * (valid_df["unit_price"] - valid_df["unit_cost"])

        # Determine date range
        date_range = (None, None)
        if len(valid_df) > 0 and "date" in valid_df.columns:
            date_range = (str(valid_df["date"].min()), str(valid_df["date"].max()))

        return ProcessedDataset(
            raw_df=cleaned_df,
            valid_df=valid_df,
            quarantined_df=quarantined_df,
            issues=issues,
            has_cost_data=has_cost_data,
            duplicate_rows_count=duplicate_count,
            date_range=date_range,
        )

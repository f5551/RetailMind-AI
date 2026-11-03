# RetailMind AI — CSV Data Contract & Integrity Rules

This document establishes the binding data specification, parsing rules, arithmetic invariants, and security constraints for all CSV files processed by RetailMind AI.

---

## 1. Supported Schema Definition

A valid sales dataset must provide the four required columns. Optional columns enrich analytical capabilities (such as categorization, regional breakdowns, and profit calculations) but are not mandatory for base ingestion.

| Field Name | Type | Requirement | Description / Valid Values | Example |
|---|---|---|---|---|
| `date` | String / Date | **Required** | Transaction date in ISO-8601 format (`YYYY-MM-DD`). | `2026-01-15` |
| `product` | String | **Required** | Product name or SKU. Non-empty trimmed string. | `Wireless Mouse` |
| `quantity` | Integer / Float | **Required** | Number of units sold or returned. Must be non-zero numeric. | `5` or `-1` |
| `unit_price` | Float | **Required** | Selling price per unit. Must be $\ge 0.00$. | `25.00` |
| `unit_cost` | Float | Optional | Cost of goods per unit. If provided, must be $\ge 0.00$. | `12.50` |
| `category` | String | Optional | Product category or taxonomy group. | `Electronics` |
| `region` | String | Optional | Sales territory or geographical region. | `North` |
| `order_id` | String | Optional | Unique transaction identifier. | `ORD-1001` |

---

## 2. Ingestion & File Constraints

To ensure predictable latency, memory safety, and prevent Denial of Service (DoS):

- **Maximum File Size**: 10 MB (Megabytes). Files exceeding this limit are rejected at upload before parsing.
- **Maximum Row Count**: 50,000 rows. Files exceeding 50,000 rows are rejected with a clear message requesting filtering or sampled upload.
- **Encoding**: UTF-8 preferred. Automatic detection fallback to `latin-1` / `cp1252` if UTF-8 decoding encounters byte errors.
- **Delimiter**: Auto-detected (comma `,`, semicolon `;`, or tab `\t`), defaulting to comma.
- **Row Structure**: Uniform column count across all rows. Ragged rows are quarantined during validation.

---

## 3. Data Cleaning & Quarantining Rules

The validation engine categorizes every row into either **Valid** (included in analysis) or **Quarantined** (excluded from aggregates, reported in `validate_dataset`).

### A. Missing Values (`Null` / `NaN` / Blank)
- **Required Columns Missing**: If any of `date`, `product`, `quantity`, or `unit_price` is missing or unparseable, the row is marked invalid and quarantined.
- **Optional Columns Missing**:
  - Missing `category` defaults to `"Uncategorized"`.
  - Missing `region` defaults to `"Unknown"`.
  - Missing `order_id` is assigned a generated sequence `GEN-{index}`.
  - Missing `unit_cost` is preserved as `null` (disabling profit calculations for that row/dataset).

### B. Duplicate Rows
- If `order_id` is present: Rows with duplicate `order_id` and identical line contents are deduplicated (first occurrence kept, duplicates logged). Rows with duplicate `order_id` but differing line items are preserved as multi-item orders.
- If `order_id` is absent: Rows with exact identical values across all columns are flagged as potential duplicates; the summary report explicitly discloses the count of identical rows.

### C. Dates and Time Zones
- The standard format is ISO-8601 (`YYYY-MM-DD`).
- Parsing accommodates common representations (`YYYY/MM/DD`, `DD/MM/YYYY`, `MM/DD/YYYY`) where unambiguous. Unparseable dates cause the row to be quarantined.
- Timestamps are normalized to UTC dates (`YYYY-MM-DD`).

### D. Returns and Negative Amounts
- **Returns Policy**: A negative `quantity` with a positive `unit_price` indicates a returned item or credit.
  - Line Transaction Value = `quantity * unit_price` (yields a negative credit).
  - Returns are legitimately subtracted from total net units and net revenue.
- **Negative Price**: A negative `unit_price` is considered corrupt data; rows with `unit_price < 0` are quarantined as invalid.
- **Zero Quantity**: Rows with `quantity == 0` are quarantined as non-transactional.

---

## 4. Deterministic Arithmetic Invariants

To eliminate LLM hallucinations, all mathematical operations are performed strictly within deterministic Python tools:

1. **Line Revenue**:
   $$\text{line\_revenue} = \text{quantity} \times \text{unit\_price}$$
2. **Total Net Revenue**:
   $$\text{Net Revenue} = \sum_{i \in \text{ValidRows}} (\text{quantity}_i \times \text{unit\_price}_i)$$
3. **Total Units**:
   $$\text{Net Units} = \sum_{i \in \text{ValidRows}} \text{quantity}_i$$
4. **Profit & Margin Policy**:
   - **Condition**: Profit is calculated **only if** `unit_cost` is populated and valid ($\ge 0$) for 100% of the aggregated rows.
   - **Line Profit**:
     $$\text{line\_profit} = \text{quantity} \times (\text{unit\_price} - \text{unit\_cost})$$
   - **Net Profit**:
     $$\text{Net Profit} = \sum_{i \in \text{ValidRows}} \text{line\_profit}_i$$
   - **Gross Margin Percentage**:
     $$\text{Margin \%} = \frac{\text{Net Profit}}{\text{Net Revenue}} \times 100\%$$
   - **Missing Cost Rule**: If any required row lacks `unit_cost`, `profit` and `margin` fields in the tool JSON output are strictly returned as `"UNAVAILABLE"`. The agent is forbidden from estimating, guessing, or fabricating profit metrics.

---

## 5. Security & CSV Formula Injection Defense

CSV files may contain malicious payloads designed to execute arbitrary code when opened in spreadsheet software (Excel, LibreOffice, Google Sheets).

### Formula Sanitization Invariant
- Any string cell whose leading character is one of `=`, `+`, `-`, `@`, `\t`, or `\r` represents a formula injection vector.
- **Ingestion**: The CSV parser treats all cell values purely as literal data strings or numbers, never evaluating formulas.
- **Export / Reporting (`generate_report`)**:
  - All text cells exported in tabular reports or CSV downloads are sanitized by prefixing dangerous characters with an apostrophe `'` (e.g., `=SUM(...)` becomes `'=SUM(...)`) or stripping formula tokens.
  - Cell strings are strictly stripped of script tags (`<script>`) and control characters.

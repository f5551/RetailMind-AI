# RetailMind AI — Cost & Token Usage Analysis

> **STATUS NOTE**: The measurements in this document represent **current development measurements** observed during live execution of the single-agent loop against the Google Gemini API. Final production costs are subject to deployment verification during Phase 5.

---

## 1. Executive Summary & Model Pricing Reference

RetailMind AI operates a single-agent reasoning loop powered by Google's `gemini-3.1-flash-lite` model. Token usage is metered at the turn level directly from provider API responses, and dollar costs are computed against official Standard Paid-Tier rates.

- **Provider**: Google Gemini API (Google AI Studio)
- **Model ID**: `gemini-3.1-flash-lite`
- **Pricing Source**: [https://ai.google.dev/gemini-api/docs/pricing](https://ai.google.dev/gemini-api/docs/pricing)
- **Pricing Verification Date**: **2026-11-03**
- **Standard Paid-Tier Reference Rates**:
  - **Standard Input (Prompt)**: **$0.25** per 1,000,000 tokens ($0.00000025 per token)
  - **Standard Output (Candidates, incl. Thinking)**: **$1.50** per 1,000,000 tokens ($0.00000150 per token)
  - **Context-Cached Input**: **$0.025** per 1,000,000 tokens ($0.000000025 per token)
- **Per-Task Hard Budget Cap**: **$0.10 USD** (enforced in application code before and after each model call)
- **Token Usage Reconciliation (Phase B)**: Full metadata reconciliation supporting prompt tokens, context-cached tokens, candidate tokens, thinking tokens (`thoughts_token_count`), and tool prompt tokens (`tool_use_prompt_token_count`), strictly reconciling with provider's `total_token_count` to eliminate under-counting or double-counting.
- **Actual Billed Provider Cost**: **$0.00 USD** (active Google AI Studio development free tier; reported status: `UNKNOWN_NO_BILLING_EVIDENCE` for billing invoices)

---

## 2. Reconciled Live Scenario Cost & Token Breakdown

All figures below are extracted directly from authentic, active JSONL traces in `traces/` and verified by automated unit tests in `tests/test_cost_accounting.py`.

| Scenario / Task | Trace File | Turns | Prompt (P) | Cached (C) | Output (O) | Thinking (Th) | Total Tokens | Exact Cost (USD) | Trace Cost (USD, 6-dec) | Actual Billed (Free Tier) |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Scenario 1: Sales Summary** | `traces/scenario_1_summary.jsonl` | 2 | 3,080 | 0 | 108 | 0 | 3,188 | $0.00093200 | $0.000932 | $0.00 |
| **Scenario 2: Product Ranking** | `traces/scenario_2_rankings.jsonl` | 2 | 3,194 | 0 | 130 | 0 | 3,324 | $0.00099350 | $0.000994 | $0.00 |
| **Scenario 3: Period Comparison** | `traces/scenario_3_comparison.jsonl` | 2 | 3,328 | 0 | 317 | 0 | 3,645 | $0.00130750 | $0.001308 | $0.00 |
| **Scenario 4: Anomaly Detection** | `traces/scenario_4_anomalies.jsonl` | 3 | 4,721 | 0 | 125 | 0 | 4,846 | $0.00136775 | $0.001368 | $0.00 |
| **Scenario 5: Schema Validation** | `traces/scenario_5_validation.jsonl` | 2 | 3,057 | 0 | 77 | 0 | 3,134 | $0.00087975 | $0.000880 | $0.00 |
| **Scenario 6: Report Generation** | `traces/scenario_6_report_approval.jsonl` | 6 | 12,975 | 0 | 604 | 0 | 13,579 | $0.00414975 | $0.004150 | $0.00 |
| **Missing-Cost Analysis** | `traces/scenario_missing_cost.jsonl` | 2 | 3,095 | 0 | 97 | 0 | 3,192 | $0.00091925 | $0.000919 | $0.00 |

*Note on arithmetic:*
`Exact Cost = (Prompt * 0.25 / 1,000,000) + (Cached * 0.025 / 1,000,000) + (Output * 1.50 / 1,000,000)`.
Trace costs reflect standard 6-decimal rounding of the exact accumulated turn costs. Discrepancies between trace values and exact arithmetic are $\le \$0.00000050$ (half a millionth of a cent).

---

## 3. Cost Aggregations & Metrics

All averages are calculated with explicit mathematical denominators:

### A. Average Cost of Five Original Scenarios (N = 5)
- **Scenarios Included**: Scenario 1, Scenario 2, Scenario 3, Scenario 4, Scenario 5
- **Total Paid-Tier Cost**: $0.00093200 + $0.00099350 + $0.00130750 + $0.00136775 + $0.00087975 = **$0.00548050 USD**
- **Average Cost per Task ($/task)**: $\frac{\$0.00548050}{5} =$ **$0.00109610 USD** (~$0.0011 / task)
- **Average Tokens per Task**: $\frac{3,188 + 3,324 + 3,645 + 4,846 + 3,134}{5} = \frac{18,137}{5} =$ **3,627.4 tokens**

### B. Average Cost Including Missing-Cost Scenario (N = 6)
- **Scenarios Included**: Scenarios 1–5 + Missing-Cost Scenario
- **Total Paid-Tier Cost**: $0.00548050 + $0.00091925 = **$0.00639975 USD**
- **Average Cost per Task ($/task)**: $\frac{\$0.00639975}{6} =$ **$0.001066625 USD** (~$0.001067 / task)
- **Average Tokens per Task**: $\frac{21,329}{6} =$ **3,554.83 tokens**

### C. Highest Observed Task Cost
- **Task**: Scenario 6 (Multi-turn executive sales report generation with human approval)
- **Total Turns Executed**: 6 turns (5 tool calls)
- **Total Tokens**: 13,579 tokens (12,975 prompt + 604 output)
- **Exact Task Cost**: **$0.00414975 USD** ($0.004150 USD)
- **Budget Margin**: Represents **4.15%** of the $0.10 task budget ceiling.

### D. Hard Budget Limit Enforcement
- **Budget Limit**: **$0.10 USD per task**
- **Enforcement Mechanism**:
  1. `pre_flight_check()`: Halts loop before calling model if cumulative spending reaches or exceeds $0.10.
  2. `post_flight_check()`: Halts loop immediately after model response if cumulative spending exceeds $0.10.
  3. Loop halts safely with `stop_reason="BUDGET_EXCEEDED"`.

---

## 4. Monthly Cost Projections

Assuming a commercial small-to-medium retail deployment analyzing daily sales feeds:

| Usage Volume | Query Type Mix | Monthly Tokens | Estimated Paid-Tier Cost (USD) | Actual Billed (Free Tier) |
|---|---|---|---|---|
| **Low (100 tasks/month)** | 90 analytical queries + 10 executive reports | ~462,000 tokens | **~$0.14 USD / month** | $0.00 |
| **Medium (1,000 tasks/month)** | 900 analytical queries + 100 executive reports | ~4,622,000 tokens | **~$1.40 USD / month** | $0.00 |
| **High (10,000 tasks/month)** | 9,000 analytical queries + 1,000 executive reports | ~46,220,000 tokens | **~$14.01 USD / month** | Tier upgrade required |

---

## 5. Billing Verification Statement

- **Estimated Paid-Tier Equivalent**: Calculated deterministically on every API call from exact token usage metadata using official Google Gemini API published rates.
- **Verified Billed Cost**: Billed cost is recorded as **$0.00 USD** because development and testing are performed under Google AI Studio's non-billable free tier quota. We make no unverified claims of provider invoices.

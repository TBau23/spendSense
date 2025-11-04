# Epic 2: Feature Engineering - Technical Design

**Status**: Ready for Implementation  
**Epic Goal**: Compute behavioral signals for 30d and 180d windows  
**Dependencies**: Epic 1 complete (SQLite data operational)

---

## Overview

Compute all behavioral signals (subscriptions, savings, credit, income, cash_flow) for consented and non-consented users. Store features in Parquet for fast analytics. Support dynamic date windows for demo flexibility.

---

## Requirements Summary

From `project_requirements.md` and `roadmap.md`:
- **5 Signal Types**: Subscriptions, Savings, Credit, Income Stability, Cash Flow
- **2 Time Windows**: 30-day and 180-day
- **Output Format**: Parquet (columnar storage)
- **Window Strategy**: Rolling windows with `as_of_date` parameter
- **Consent**: Compute for all users, filtering deferred to Epic 5

---

## Signal Specifications

### 1. Subscriptions (`features/subscriptions.parquet`)

**Criteria** (from requirements lines 47-50):
- Recurring merchants: ≥3 occurrences in 90 days with monthly/weekly cadence
- Monthly recurring spend: Sum of recurring transaction amounts
- Subscription share: Recurring spend / total spend

**Detection Logic**:
- Group transactions by `merchant_name`, count occurrences in window
- For merchants with ≥3 occurrences, compute gaps between consecutive transactions
- **Monthly cadence**: ≥70% of gaps are 28-32 days (±2 from 30)
- **Weekly cadence**: ≥70% of gaps are 5-9 days (±2 from 7)
- Sum amounts for qualifying merchants

**Output Schema**:
```
user_id | window_days | as_of_date | recurring_merchant_count | monthly_recurring_spend | subscription_share
```

---

### 2. Savings (`features/savings.parquet`)

**Criteria** (from requirements lines 51-54):
- Net inflow: Sum of deposits to savings-type accounts (savings, money_market, hsa)
- Growth rate: (End balance - Start balance) / Start balance
- Emergency fund coverage: Savings balance / average monthly expenses

**Account Types** (from Epic 1):
- `account_type IN ('savings', 'money_market', 'hsa')`

**Output Schema**:
```
user_id | window_days | as_of_date | net_inflow | growth_rate | emergency_fund_coverage_months | avg_monthly_expenses
```

---

### 3. Credit (`features/credit.parquet`)

**Criteria** (from requirements lines 55-60):
- Utilization: balance_current / balance_limit per card
- Utilization flags: ≥30%, ≥50%, ≥80%
- Minimum payment only: last_payment_amount ≈ minimum_payment_amount (within 10%)
- Interest charges: Any transactions with `category_primary='BANK_FEES'` and `category_detailed='Interest'`
- Overdue status: From `liabilities.is_overdue`

**Output Schema**:
```
user_id | window_days | as_of_date | max_utilization | min_utilization | avg_utilization | has_high_utilization | minimum_payment_only | interest_charges_present | is_overdue
```

---

### 4. Income Stability (`features/income.parquet`)

**Criteria** (from requirements lines 61-64):
- Payroll detection: `merchant_name = 'PAYROLL DEPOSIT'` OR `category_primary = 'INCOME'`
- Payment frequency: Median gap between consecutive payroll deposits
- Cash-flow buffer: Current checking balance / average monthly expenses

**Output Schema**:
```
user_id | window_days | as_of_date | payroll_count | median_pay_gap_days | cash_flow_buffer_months | avg_monthly_expenses
```

---

### 5. Cash Flow (`features/cash_flow.parquet`)

**Criteria** (Persona 5 from roadmap lines 50-56):
- Low balance frequency: % of days with checking balance <$100
- Balance volatility: std_dev(daily_balance) / mean(daily_balance)

**Implementation**:
- Reconstruct daily balances from transaction history (chronological replay)
- For each day in window, compute balance = start_balance + sum(transactions up to that day)
- Compute metrics across daily balance array

**Output Schema**:
```
user_id | window_days | as_of_date | pct_days_below_100 | balance_volatility | min_balance | max_balance | avg_balance
```

---

## Module Structure

```
backend/
└── features/
    ├── __init__.py
    ├── compute.py           # Main orchestrator, window handling
    ├── subscriptions.py     # Subscription detection
    ├── savings.py           # Savings metrics
    ├── credit.py            # Credit utilization + liability checks
    ├── income.py            # Payroll detection + stability
    ├── cash_flow.py         # Balance reconstruction + volatility
    └── storage.py           # Parquet read/write utilities
```

---

## Feature Computation Workflow

1. **Initialize**: Load SQLite data (accounts, transactions, liabilities)
2. **Set Windows**: Compute date ranges for 30d and 180d from `as_of_date`
3. **For Each User**:
   - Filter transactions/accounts to window
   - Compute each signal type (subscriptions, savings, credit, income, cash_flow)
   - Write row to in-memory DataFrame
4. **Export**: Write 5 Parquet files (one per signal type)
5. **Validation**: Check coverage (all consented users have features)

---

## Window Strategy

**Fixed Date Demo**:
- Default `as_of_date = None` → uses current date
- Can specify `as_of_date = "2025-11-04"` for reproducible demos

**Window Definitions**:
- **30-day**: `(as_of_date - 30 days, as_of_date]` inclusive
- **180-day**: `(as_of_date - 180 days, as_of_date]` inclusive
- **90-day** (for subscription detection only): `(as_of_date - 90 days, as_of_date]`

---

## Design Decisions

### 1. Parquet Over SQLite for Features
**Decision**: Store features in Parquet files, not SQLite tables  
**Rationale**: Columnar format optimized for analytics, faster aggregations, smaller file size  
**Impact**: Epic 3 reads from Parquet for persona assignment

### 2. Reconstruct Daily Balances On-the-Fly
**Decision**: Compute daily balances from transactions during feature computation, don't store separately  
**Rationale**: One-time computation cached in Parquet, avoids schema changes, ~15k operations negligible for 75 users  
**Impact**: `cash_flow.py` has chronological replay logic

### 3. Subscription Cadence Tolerance
**Decision**: ±2 days for monthly/weekly, ≥70% gaps must match cadence  
**Rationale**: Handles billing date drift (e.g., 30 vs 31 day months), filters out irregular purchases  
**Impact**: `subscriptions.py` gap analysis logic

### 4. Average Monthly Expenses Definition
**Decision**: Sum of all outflow transactions (amount < 0) / months in window  
**Rationale**: Simple, captures spending patterns across categories  
**Impact**: Used in savings and income features for coverage/buffer calculations

### 5. Compute All Users (Including Non-Consented)
**Decision**: Compute features for all users, consent filtering happens in Epic 5  
**Rationale**: Simpler Epic 2 implementation, clean separation of concerns, enables testing  
**Impact**: Operator view (Epic 5) must filter by consent before displaying

---

## Testing Strategy

### Unit Tests (≥5 for Epic 2)
1. Subscription detection with known recurring merchants
2. Savings growth rate calculation
3. Credit utilization thresholds (30%, 50%, 80%)
4. Income median pay gap calculation
5. Cash flow daily balance reconstruction

### Integration Tests (≥2 for Epic 2)
1. End-to-end feature computation for all signal types
2. Parquet read/write round-trip (write features, read back, validate)

### Validation Against Epic 1 Archetypes
- High Utilizer → credit features show utilization ≥50%
- Variable Income → income features show median_pay_gap >45 days
- Subscription Heavy → subscription features show ≥3 recurring merchants
- Savings Builder → savings features show positive growth_rate
- Cash Flow Stressed → cash_flow features show pct_days_below_100 ≥0.30

---

## Configuration

Extend `config.json`:
```json
{
  "features": {
    "output_dir": "data/features",
    "windows": [30, 180],
    "as_of_date": null,
    "subscription_gap_tolerance_days": 2,
    "subscription_cadence_threshold": 0.7
  }
}
```

---

## Next Epic Prerequisites

**What Epic 3 Needs from Epic 2**:
- [ ] 5 Parquet files populated: subscriptions, savings, credit, income, cash_flow
- [ ] All 75 users have feature rows for both 30d and 180d windows
- [ ] Feature validation confirms archetype expectations (High Utilizer has high credit utilization, etc.)
- [ ] Feature computation script runnable via `python scripts/compute_features.py`
- [ ] Tests passing (≥7 tests)

---

## Success Criteria

Epic 2 complete when:
- [ ] All 5 signal types compute successfully
- [ ] Parquet files created with correct schema
- [ ] 100% coverage: All 75 users have features for both windows
- [ ] Feature values align with Epic 1 archetypes
- [ ] ≥7 tests passing
- [ ] Decision log updated
- [ ] One-command execution: `python scripts/compute_features.py`

---

## Decision Log Updates Needed

After implementation, document:
- Average monthly expenses calculation approach
- Subscription cadence matching logic refinements
- Any performance optimizations
- Parquet schema decisions


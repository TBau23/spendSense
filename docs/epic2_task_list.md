# Epic 2: Feature Engineering - Task List

**Status**: Ready for Implementation  
**Design Doc**: `epic2_technical_design.md`  
**Core Problem**: Compute 5 behavioral signal types across 2 time windows for all users

---

## Implementation Tasks

### 1. Feature Module Setup
**Task**: Create feature computation module structure and Parquet storage utilities  
**Output**: Module skeleton with storage helpers  
**Key Files**: 
- `backend/features/__init__.py`
- `backend/features/storage.py` (Parquet read/write)
- `backend/features/compute.py` (orchestrator, window logic)

### 2. Subscription Detection
**Task**: Implement recurring merchant detection with cadence analysis  
**Output**: Subscription features (recurring_merchant_count, monthly_recurring_spend, subscription_share)  
**Key Files**: `backend/features/subscriptions.py`  
**Critical**: 
- ≥3 occurrences in 90-day window
- ±2 day tolerance for monthly (28-32 days) and weekly (5-9 days) cadence
- ≥70% of gaps must match cadence

### 3. Savings Metrics
**Task**: Compute savings growth, net inflow, emergency fund coverage  
**Output**: Savings features (net_inflow, growth_rate, emergency_fund_coverage_months)  
**Key Files**: `backend/features/savings.py`  
**Critical**: 
- Filter accounts by type (savings, money_market, hsa)
- Calculate average monthly expenses for emergency fund coverage

### 4. Credit Utilization & Liabilities
**Task**: Compute credit metrics from accounts and liabilities tables  
**Output**: Credit features (utilization levels, minimum_payment_only, interest_charges, is_overdue)  
**Key Files**: `backend/features/credit.py`  
**Critical**: 
- Join accounts with liabilities for credit cards
- Flag utilization thresholds (30%, 50%, 80%)
- Detect minimum-payment-only (within 10% tolerance)

### 5. Income Stability Detection
**Task**: Identify payroll transactions and compute payment frequency metrics  
**Output**: Income features (payroll_count, median_pay_gap_days, cash_flow_buffer_months)  
**Key Files**: `backend/features/income.py`  
**Critical**: 
- Filter by `merchant_name = 'PAYROLL DEPOSIT'` OR `category_primary = 'INCOME'`
- Calculate median of consecutive payment gaps
- Compute cash-flow buffer (checking balance / avg monthly expenses)

### 6. Cash Flow Analysis
**Task**: Reconstruct daily balances and compute volatility metrics  
**Output**: Cash flow features (pct_days_below_100, balance_volatility, min/max/avg_balance)  
**Key Files**: `backend/features/cash_flow.py`  
**Critical**: 
- Chronologically replay transactions to build daily balance array
- Compute % of days with balance <$100
- Calculate balance volatility (std_dev / mean)

### 7. Feature Computation Orchestrator
**Task**: Build main computation pipeline with window handling  
**Output**: Unified feature computation for all signal types  
**Key Files**: `backend/features/compute.py`  
**Critical**: 
- Accept `as_of_date` parameter (defaults to current date)
- Compute 30-day and 180-day windows
- Generate 5 Parquet files with consistent schema

### 8. Feature Computation Script
**Task**: Create CLI entry point for feature generation  
**Output**: One-command execution via `python scripts/compute_features.py`  
**Key Files**: `scripts/compute_features.py`  
**Critical**: 
- Load config from `config.json`
- Call feature computation orchestrator
- Generate validation report

### 9. Configuration Extension
**Task**: Extend config.json with feature computation settings  
**Output**: Feature configuration section  
**Key Files**: `config.json`  
**Critical**: 
- Output directory path
- Window sizes (30, 180)
- Subscription detection thresholds

### 10. Testing
**Task**: Write unit and integration tests  
**Output**: ≥7 tests passing  
**Key Files**: `backend/tests/test_features.py`  
**Critical Tests**:
- Subscription detection with known recurring merchants
- Savings growth rate calculation
- Credit utilization threshold flags
- Income median pay gap calculation
- Cash flow daily balance reconstruction
- End-to-end feature computation
- Parquet round-trip (write and read)

---

## Validation Criteria

Before moving to Epic 3, verify:
- [ ] All 5 Parquet files created: subscriptions, savings, credit, income, cash_flow
- [ ] All 75 users have feature rows for both 30d and 180d windows (150 rows per file)
- [ ] High Utilizer archetype users show credit utilization ≥50%
- [ ] Variable Income archetype users show median_pay_gap >45 days
- [ ] Subscription Heavy archetype users show ≥3 recurring merchants
- [ ] Savings Builder archetype users show positive growth_rate
- [ ] Cash Flow Stressed archetype users show pct_days_below_100 ≥0.30
- [ ] Feature computation completes in <30 seconds for 75 users
- [ ] Tests passing (≥7)

---

## Dependencies

**External Libraries**:
- `pandas` - DataFrame operations
- `pyarrow` - Parquet read/write
- `numpy` - Statistical calculations
- Standard Python libraries (datetime, statistics, etc.)

**From Epic 1**:
- SQLite database at `data/spendsense.db`
- Tables: users, accounts, transactions, liabilities
- 75 users with validated archetypes

**Config**:
- Extend `config.json` with features section

---

## Epic Completion

**Definition of Done**:
1. ✅ All 5 signal types compute successfully
2. ✅ Parquet files created with correct schema
3. ✅ 100% coverage: All users have features for both windows
4. ✅ Feature values align with Epic 1 archetypes
5. ✅ Tests passing (≥7)
6. ✅ Decision log updated with implementation notes
7. ✅ Feature computation script works via single command
8. ✅ Next Epic Prerequisites documented

---

## Implementation Notes

### Average Monthly Expenses
Used in multiple features (savings, income). Define once, reuse:
- Sum of all outflow transactions (amount < 0) in window
- Divide by number of months in window
- Handle edge case: if window has no expenses, use $1 to avoid division by zero

### Checking Account Identification
For cash-flow buffer and daily balance:
- Primary checking: `account_type = 'checking'`
- If multiple checking accounts, use the one with highest transaction volume

### Window Boundary Handling
- Windows are **inclusive** of as_of_date
- 30-day window: `(as_of_date - 30 days, as_of_date]`
- 180-day window: `(as_of_date - 180 days, as_of_date]`
- 90-day window (subscriptions only): `(as_of_date - 90 days, as_of_date]`

### Performance Considerations
- Load all transactions once, filter by window per user
- Use pandas groupby operations for merchant aggregations
- Cache computed features in Parquet for Epic 3+


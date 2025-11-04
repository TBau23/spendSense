# Epic 1: Data Foundation - Technical Design

**Status**: Draft  
**Epic Goal**: Synthetic data generator + schemas + consent distribution  
**Dependencies**: None (foundational epic)

---

## Overview

Generate synthetic Plaid-style transaction data for 50-100 users across 7 months, ensuring diverse financial behaviors that will trigger all 5 personas. Establish SQLite schema for relational data and Parquet storage for analytics.

---

## Requirements Summary

From `project_requirements.md`:
- **Users**: 50-100 synthetic users, no real PII
- **Data Structures**: Accounts (checking, savings, credit, etc.), Transactions, Liabilities
- **Time Range**: 7 months of transaction history
- **Consent Distribution**: 90% consent=true, 10% consent=false
- **Persona Coverage**: User archetypes must represent all 5 personas + edge cases

---

## Data Schema Design

### SQLite Tables (Relational)

#### 1. Users Table
```sql
users (
  user_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  consent_status BOOLEAN NOT NULL,
  consent_updated_at TIMESTAMP
)
```

#### 2. Accounts Table
```sql
accounts (
  account_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  account_type TEXT NOT NULL,  -- checking, savings, credit_card, money_market, hsa
  account_subtype TEXT,
  balance_available REAL,
  balance_current REAL,
  balance_limit REAL,           -- for credit cards
  iso_currency_code TEXT DEFAULT 'USD',
  holder_category TEXT,         -- personal only (no business)
  FOREIGN KEY (user_id) REFERENCES users(user_id)
)
```

#### 3. Transactions Table
```sql
transactions (
  transaction_id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  date DATE NOT NULL,
  amount REAL NOT NULL,
  merchant_name TEXT,
  payment_channel TEXT,
  category_primary TEXT,
  category_detailed TEXT,
  pending BOOLEAN DEFAULT 0,
  FOREIGN KEY (account_id) REFERENCES accounts(account_id),
  FOREIGN KEY (user_id) REFERENCES users(user_id)
)
```

#### 4. Liabilities Table
```sql
liabilities (
  liability_id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  liability_type TEXT NOT NULL,  -- credit_card, mortgage, student_loan
  apr_percentage REAL,
  apr_type TEXT,                 -- fixed, variable
  minimum_payment_amount REAL,
  last_payment_amount REAL,
  is_overdue BOOLEAN DEFAULT 0,
  next_payment_due_date DATE,
  last_statement_balance REAL,
  interest_rate REAL,            -- for mortgages/student loans
  FOREIGN KEY (account_id) REFERENCES accounts(account_id),
  FOREIGN KEY (user_id) REFERENCES users(user_id)
)
```

### Parquet Storage (Analytics)

Will be populated in Epic 2. Structure:
- `/data/features/subscriptions.parquet` - Subscription signals per user per window
- `/data/features/savings.parquet` - Savings signals per user per window
- `/data/features/credit.parquet` - Credit utilization signals per user per window
- `/data/features/income.parquet` - Income stability signals per user per window
- `/data/features/cash_flow.parquet` - Cash flow stress signals per user per window

---

## User Archetype Design

To ensure all personas are triggered, generate users with these archetypes:

### Archetype Distribution (Target: 50-100 users)

| Archetype | Count | Persona Triggered | Key Characteristics |
|-----------|-------|-------------------|---------------------|
| High Utilizer | 15-20 | Persona 1 | Credit utilization ≥50%, interest charges, minimum payments |
| Variable Income | 10-15 | Persona 2 | Irregular payroll (>45 day gaps), low cash buffer (<1 month) |
| Subscription Heavy | 10-15 | Persona 3 | ≥3 recurring merchants, $50+ monthly recurring spend |
| Savings Builder | 10-15 | Persona 4 | Consistent savings inflow, low utilization, emergency fund growing |
| Cash Flow Stressed | 8-12 | Persona 5 | Checking balance frequently <$100, high balance volatility |
| Multi-Persona (overlap) | 10-15 | Multiple | Combinations (e.g., high utilization + cash flow stress) |
| Stable/No Issues | 5-10 | None | Control group, low risk behaviors |
| Edge Cases | 5-10 | Varies | Boundary conditions (exactly 30% low balance days, etc.) |

### Edge Cases to Include
- User with exactly 50% credit utilization (Persona 1 threshold)
- User with exactly 3 recurring merchants (Persona 3 threshold)
- User with exactly 30% of days with balance <$100 (Persona 5 threshold)
- User with consent=false but would qualify for Persona 1 (tests consent enforcement)
- User with 0 transactions (tests empty data handling)
- User with only pending transactions
- User with all cash transactions (no credit)

---

## Synthetic Data Generation Strategy

### Time Range
- **Start Date**: 7 months before "today" (current date at generation time)
- **End Date**: "Today"
- **Transaction Frequency**: Varies by archetype (2-30 transactions/month)

### Merchant Categories (Plaid-Style)
Use realistic categories:
- **Subscriptions**: Netflix, Spotify, Gym, Cloud Storage, News, Meal Kit
- **Payroll**: "PAYROLL ACH" or company names
- **Groceries**: Whole Foods, Safeway, Trader Joe's
- **Dining**: Various restaurant names
- **Gas**: Shell, Chevron, BP
- **Utilities**: Electric, Water, Internet
- **Shopping**: Amazon, Target, Walmart
- **Healthcare**: Pharmacy, Doctor visits

### Transaction Amount Realism
- Payroll: $2,000 - $8,000 (varies by archetype)
- Subscriptions: $5 - $50
- Groceries: $30 - $200
- Dining: $15 - $80
- Rent/Mortgage: $1,000 - $3,000
- Credit card payments: Varies (minimum to full balance)

### Balance Tracking (for Cash Flow Stressed)
For Cash Flow Stressed archetype:
- Start with low checking balance ($50-$200)
- Generate spending that frequently dips balance below $100
- Payday deposits followed by large expense clusters (rent, bills)
- High volatility: balance swings from $20 to $1,500 and back down within week
- At least 30% of days should have balance <$100

---

## Implementation Approach

### Module Structure
```
backend/
└── core/
    └── data_gen/
        ├── __init__.py
        ├── generator.py          # Main orchestrator
        ├── archetypes.py         # User archetype definitions
        ├── accounts.py           # Account generation logic
        ├── transactions.py       # Transaction generation logic
        ├── liabilities.py        # Liability generation logic
        └── validation.py         # Data quality checks

backend/
└── storage/
    ├── __init__.py
    ├── database.py              # SQLite connection and setup
    └── schemas.py               # Schema definitions

scripts/
└── generate_data.py             # CLI entry point
```

### Generation Workflow
1. **Initialize Database**: Create SQLite tables
2. **Generate Users**: Create 50-100 users with consent distribution
3. **Assign Archetypes**: Map users to archetypes
4. **Generate Accounts**: Create checking, savings, credit accounts per user
5. **Generate Transactions**: 7 months of transactions per archetype behavior (tracking balances for Cash Flow Stressed)
6. **Generate Liabilities**: Credit card/loan details
7. **Validate Data**: Check persona coverage, data quality
8. **Export Summary**: User counts, persona distribution, date ranges

### Determinism
- Use **fixed seed** for reproducibility (e.g., `random.seed(42)`, `np.random.seed(42)`)
- Document seed in generation logs
- Ensures consistent data across runs

---

## Data Validation

### Quality Checks
- [ ] All users have ≥1 account
- [ ] All accounts belong to valid users
- [ ] All transactions have valid dates within 7-month range
- [ ] All credit accounts have corresponding liabilities
- [ ] Consent distribution: 88-92% consent=true (allows ±2% variance)
- [ ] All 5 personas have ≥5 users that would trigger them
- [ ] No business accounts (holder_category validation)
- [ ] No real PII (names from fake name generator)

### Output Validation Report
Generate JSON summary:
```json
{
  "generation_date": "2025-11-04",
  "seed": 42,
  "user_count": 75,
  "consent_distribution": {
    "consented": 68,
    "not_consented": 7
  },
  "archetype_distribution": {
    "high_utilizer": 18,
    "variable_income": 12,
    ...
  },
  "date_range": {
    "start": "2025-04-04",
    "end": "2025-11-04"
  },
  "transaction_count": 4523,
  "account_count": 178,
  "validation_passed": true
}
```

---

## Testing Strategy

### Unit Tests (≥3 for Epic 1)
1. Test archetype generation logic
2. Test schema creation
3. Test consent distribution (90/10 split)

### Integration Tests (≥1 for Epic 1)
1. End-to-end generation: Users → Accounts → Transactions → Validation

### Test Data
- Use separate test seed for predictable test outcomes
- Generate small dataset (10 users) for fast tests

---

## Configuration

### config.json
```json
{
  "data_generation": {
    "user_count": 75,
    "consent_ratio": 0.9,
    "seed": 42,
    "date_range_months": 7,
    "archetypes": {
      "high_utilizer": 18,
      "variable_income": 12,
      "subscription_heavy": 12,
      "savings_builder": 12,
      "cash_flow_stressed": 10,
      "multi_persona": 12,
      "stable": 6,
      "edge_cases": 8
    }
  },
  "database": {
    "path": "data/spendsense.db"
  }
}
```

---

## Design Decisions Resolved

1. **PII Masking**: ✅ Use `Faker` library for names and fake data generation
2. **Account ID Format**: ✅ Match Plaid format (`acc_xxxxx`, `txn_xxxxx`) where it adds value
3. **Transaction Pending Logic**: ✅ Minimal - only if impacts persona classification (likely not needed)
4. **Balance Tracking**: ✅ Generate transactions chronologically with running balance tracking to ensure Cash Flow Stressed archetype validity

---

## Next Epic Prerequisites

**What Epic 2 Needs from Epic 1**:
- [ ] SQLite database at `data/spendsense.db` with all tables populated
- [ ] Validation report confirming all 5 personas represented
- [ ] Consent distribution at 90/10 (±2%)
- [ ] Date range: 7 months ending "today"
- [ ] No validation errors
- [ ] Data generation script runnable via `python scripts/generate_data.py`

---

## Success Criteria

Epic 1 complete when:
- [ ] 50-100 synthetic users generated
- [ ] 90% consent=true, 10% consent=false
- [ ] All 5 personas have representative users
- [ ] SQLite schema operational
- [ ] Data validation report passes all checks
- [ ] ≥4 tests passing
- [ ] Documentation in decision log updated
- [ ] One-command generation: `python scripts/generate_data.py`

---

## Decision Log Updates Needed

After implementation, document:
- Chosen archetype distributions
- Merchant category mapping approach
- PII masking strategy
- Any schema modifications from this design


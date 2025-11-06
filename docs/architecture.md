# SpendSense Architecture

**Purpose**: This document explains the technical architecture of SpendSense - how data flows through the system, key entities, and how information reaches the operator dashboard.

---

## System Overview

SpendSense is a consent-aware financial behavior analysis system that:
1. Ingests synthetic Plaid-style transaction data
2. Computes behavioral features across time windows
3. Assigns users to personas based on rules-based criteria
4. Generates personalized recommendations with LLM-assisted content
5. Routes recommendations through operator review before delivery

**Tech Stack**: Python/FastAPI backend, React frontend, SQLite + Parquet storage

---

## Core Data Entities

### Primary Entities (SQLite)
- **users**: User records with `consent_status` flag (90% consented, 10% not)
- **accounts**: Checking, savings, credit card accounts with balances/limits
- **transactions**: Transaction history (7 months, ~200-500 per user)
- **liabilities**: Credit card APRs, minimum payments, overdue status

### Feature Entities (Parquet)
- **subscriptions**: Recurring merchants, monthly spend, subscription share
- **savings**: Net inflow, growth rate, emergency fund coverage
- **credit**: Utilization %, interest charges, minimum payment detection
- **income**: Payroll frequency, pay gaps, cash buffer
- **cash_flow**: Low balance frequency, balance volatility

### Recommendation Entities (SQLite)
- **recommendations**: Generated recommendation packages per user
- **recommendation_items**: Educational/actionable/partner offer content
- **decision_traces**: Audit trail explaining why recommendations were made

---

## Module Structure

```
backend/
├── core/data_gen/         # Synthetic data generation
│   ├── archetypes.py      # User financial behavior templates
│   ├── generator.py       # Orchestrates data generation
│   └── validation.py      # Data quality checks
│
├── features/              # Behavioral signal detection
│   ├── compute.py         # Orchestrator for feature computation
│   ├── subscriptions.py   # Recurring merchant detection
│   ├── savings.py         # Savings behavior analysis
│   ├── credit.py          # Credit utilization/payment patterns
│   ├── income.py          # Payroll detection and stability
│   ├── cash_flow.py       # Balance volatility analysis
│   └── storage.py         # Save features to Parquet
│
├── personas/              # Rules-based persona assignment
│   ├── assign.py          # Orchestrator - assigns personas per user/window
│   ├── evaluators.py      # 5 persona evaluation functions
│   ├── prioritize.py      # Severity-based ranking (CRITICAL > HIGH > MEDIUM > LOW)
│   ├── metadata.py        # Persona definitions (criteria, focus, priority)
│   └── trace.py           # Generate assignment audit trails
│
├── recommend/             # Recommendation generation
│   ├── generator.py       # Orchestrator - builds recommendation packages
│   ├── persona_handler.py # Load persona context + features
│   ├── content_selector.py # Select educational content from catalog
│   ├── eligibility.py     # Check eligibility for partner offers
│   ├── llm_client.py      # OpenAI integration for content generation
│   ├── prompts.py         # LLM prompt builders with user context
│   ├── approval.py        # Operator approval workflow
│   ├── storage.py         # Save recommendations to SQLite
│   └── traces.py          # Generate decision traces
│
├── guardrails/            # Consent & compliance
│   ├── consent.py         # Enforce consent before processing
│   └── metrics.py         # Compute operator dashboard metrics
│
├── api/                   # REST API layer
│   ├── main.py            # FastAPI application entry point
│   └── operator.py        # Operator endpoints (users, recs, approval)
│
└── storage/               # Data persistence
    ├── database.py        # SQLite connection utilities
    ├── schemas.py         # Table definitions (users, accounts, etc.)
    └── migrations.py      # Schema migrations

frontend/
└── src/
    ├── components/        # Reusable UI components
    │   ├── UserList.jsx          # List of consented users
    │   ├── RecommendationCard.jsx # Recommendation display
    │   ├── ApprovalActions.jsx   # Approve/flag buttons
    │   ├── DecisionTrace.jsx     # Audit trail viewer
    │   └── MetricsPanel.jsx      # Dashboard metrics
    └── pages/
        ├── OperatorDashboard.jsx # Main operator view
        └── UserDetailView.jsx    # Single user drill-down
```

---

## Data Flow Pipeline

### 1. Data Generation (Epic 1)
```
scripts/generate_data.py
  → core/data_gen/archetypes.py (define 8 user templates per persona)
  → core/data_gen/generator.py (generate synthetic transactions)
  → storage/schemas.py (create tables)
  → SQLite: users, accounts, transactions, liabilities
```

**Output**: 50-100 users with 7 months of realistic transaction history

### 2. Feature Computation (Epic 2)
```
scripts/compute_features.py
  → features/compute.py (orchestrator)
  → For each user:
      → features/subscriptions.py (detect recurring merchants)
      → features/savings.py (compute net inflow, growth)
      → features/credit.py (compute utilization, interest)
      → features/income.py (detect payroll, gaps)
      → features/cash_flow.py (analyze balance volatility)
  → features/storage.py
  → Parquet: 5 feature files (subscriptions, savings, credit, income, cash_flow)
```

**Windows**: 30-day and 180-day lookback periods  
**Output**: ~5 Parquet files with behavioral metrics

### 3. Persona Assignment (Epic 3)
```
scripts/assign_personas.py
  → personas/assign.py (orchestrator)
  → For each user/window:
      → Load features from Parquet
      → personas/evaluators.py (evaluate all 5 personas)
      → personas/prioritize.py (rank by severity)
      → personas/trace.py (generate audit trail)
  → storage: persona_assignments.parquet + decision_traces table
```

**Personas** (severity-ranked):
1. **High Utilization** (CRITICAL): ≥50% credit utilization OR overdue
2. **Variable Income Budgeter** (HIGH): Pay gaps >45d + buffer <1 month
3. **Subscription-Heavy** (MEDIUM): ≥3 recurring merchants + ≥$50/mo
4. **Savings Builder** (LOW): Growth ≥2% + utilization <30%
5. **Cash Flow Stressed** (HIGH): ≥30% days with balance <$100 + high volatility

**Output**: Primary/secondary persona per user per window

### 4. Recommendation Generation (Epic 4)
```
scripts/generate_recommendations.py
  → recommend/generator.py (orchestrator)
  → For each consented user:
      → recommend/persona_handler.py (load context)
      → recommend/content_selector.py (select 3-5 educational items)
      → recommend/eligibility.py (filter partner offers)
      → recommend/llm_client.py (generate rationales, actionable items)
      → recommend/storage.py (save package)
      → recommend/traces.py (log decisions)
  → SQLite: recommendations + recommendation_items
  → Status: PENDING_REVIEW
```

**Recommendation Package** (per user):
- 3-5 educational content items (persona-mapped articles/guides)
- 1-3 actionable items with data-backed rationales
- 0-2 partner offers (eligibility-filtered)
- Decision trace explaining selections

**LLM Role**: Generate human-readable content text only; all logic is rules-based

### 5. Operator Review (Epic 5)
```
Frontend: OperatorDashboard.jsx
  → API: GET /api/operator/users (filtered by consent_status=1)
  → Display: User list with personas and rec counts
  
User Selection: UserDetailView.jsx
  → API: GET /api/operator/users/{user_id}
  → API: GET /api/operator/users/{user_id}/recommendations
  → Display: Features, personas, recommendations
  
Approval Action: ApprovalActions.jsx
  → API: POST /api/operator/recommendations/{rec_id}/approve
  → recommend/approval.py (update status to APPROVED)
  → SQLite: recommendations.status = APPROVED
```

**Operator Actions**:
- **Approve**: Mark deliverable to user
- **Flag**: Block from delivery with notes
- **Trace View**: See why persona was assigned and content selected

---

## Storage Architecture

### SQLite (Relational)
**Purpose**: Transactional data with foreign key integrity

**Tables**:
- `users` → `accounts` → `transactions` (1:N:N)
- `users` → `liabilities` (1:N)
- `recommendations` → `recommendation_items` (1:N)
- `decision_traces` (audit log)

**Indexes**: `idx_transactions_user_date`, `idx_transactions_account`

### Parquet (Columnar)
**Purpose**: Analytical features - fast window queries

**Files**: `data/features/*.parquet`
- subscriptions.parquet
- savings.parquet
- credit.parquet
- income.parquet
- cash_flow.parquet
- persona_assignments.parquet

**Schema**: Each row = (user_id, window_days, as_of_date, ...features)

---

## API Layer

### Operator Endpoints (`/api/operator`)

**User Management**:
```
GET  /users                    # List all consented users (filterable)
GET  /users/{user_id}          # User detail with features/personas
GET  /users/{user_id}/recommendations  # All recs for user
```

**Recommendation Review**:
```
GET  /recommendations/{rec_id}          # Fetch rec with items
POST /recommendations/{rec_id}/approve  # Approve for delivery
POST /recommendations/{rec_id}/flag     # Block with notes
```

**Decision Traces**:
```
GET  /traces/{user_id}         # Audit trail (persona + content decisions)
```

**Metrics**:
```
GET  /metrics                  # Dashboard summary (counts, approval rate)
```

**Consent Enforcement**: All endpoints call `guardrails.consent.check_consent()` before returning user data. Returns 403 if `consent_status=0`.

---

## Key Design Patterns

### 1. Consent-First Processing
Every data access checks consent:
```python
from backend.guardrails.consent import check_consent, ConsentError

try:
    check_consent(user_id, db_path)  # Raises ConsentError if not consented
    # ... proceed with data access
except ConsentError:
    return HTTP 403
```

### 2. Rules-Based Logic
All persona assignment and eligibility checks are deterministic:
- No ML black boxes
- Fully auditable via decision traces
- Operators can validate assignments

### 3. Feature-Persona-Recommendation Flow
```
Raw Transactions → Features (Parquet) → Personas (rules) → Recommendations (LLM content + rules)
```
Each stage is decoupled and can be recomputed independently.

### 4. Operator-in-the-Loop
Recommendations start as `PENDING_REVIEW` and require operator approval before delivery. Prevents crossing into financial advice territory.

---

## Computation Windows

All features computed across two windows:
- **30-day**: Recent behavior, short-term patterns
- **180-day**: Long-term trends, stability indicators

Personas assigned per window, allowing operators to see:
- Recent behavior vs. historical trends
- Emerging patterns (e.g., new subscription habit)

---

## How Information Reaches Operator View

```
1. Operator opens dashboard (OperatorDashboard.jsx)
   ↓
2. Frontend calls GET /api/operator/users
   ↓
3. Backend checks consent_status=1 filter (guardrails/consent.py)
   ↓
4. Backend joins:
   - SQLite: users table
   - Parquet: persona_assignments (30d window)
   - SQLite: recommendations table (count by status)
   ↓
5. guardrails/metrics.py computes:
   - User name, persona, rec counts
   - Latest recommendation status
   ↓
6. Returns JSON array of consented users
   ↓
7. Frontend displays sortable/filterable user list

When operator selects a user:
8. Frontend calls GET /api/operator/users/{user_id}
   ↓
9. Backend loads:
   - Parquet: All 5 feature types (30d + 180d)
   - Parquet: Persona assignments (both windows)
   - SQLite: Recommendations with items
   ↓
10. UserDetailView.jsx displays:
    - Account balances
    - Feature metrics (subscriptions, savings, etc.)
    - Personas (30d vs 180d comparison)
    - Recommendations with approve/flag actions
```

---

## Critical Dependencies

**Epic 1 → Epic 2**: SQLite schema + synthetic transactions must exist  
**Epic 2 → Epic 3**: Feature Parquet files required for persona evaluation  
**Epic 3 → Epic 4**: Persona assignments needed to select content  
**Epic 4 → Epic 5**: Recommendations must exist to populate operator queue  

---

## Limitations

- Synthetic data only (no live Plaid integration)
- Local SQLite (not production-scale)
- Single machine execution (no distributed processing)
- LLM used only for content text generation (not logic)
- No real-time updates (batch processing)


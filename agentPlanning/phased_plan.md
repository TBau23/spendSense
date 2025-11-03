# SpendSense Implementation Plan

## Project Overview

**Goal:** Build an explainable, consent-aware system that detects behavioral patterns from transaction data, assigns personas, and delivers personalized financial education with strict compliance guardrails.

**Tech Stack:** Python + FastAPI + React (Monorepo)

**Key Constraint:** Compliance-first architecture - no harmful suggestions, automated validation with safe fallbacks

---

## Success Criteria

| Category | Metric | Target |
|----------|--------|--------|
| Coverage | Users with assigned persona + ≥3 behaviors | 100% |
| Explainability | Recommendations with rationales | 100% |
| Latency | Time to generate recommendations per user | <5 seconds |
| Auditability | Recommendations with decision traces | 100% |
| Code Quality | Passing unit/integration tests | ≥10 tests |
| Documentation | Schema and decision log clarity | Complete |

---

## Monorepo Structure

```
spendsense/
├── backend/
│   ├── api/                    # FastAPI routes
│   ├── core/
│   │   ├── data_gen/           # Synthetic data generator
│   │   ├── signals/            # Feature detection (subscriptions, savings, credit, income)
│   │   ├── personas/           # Assignment logic & prioritization
│   │   ├── engine/             # Recommendation engine (LLM + templates)
│   │   └── guardrails/         # Consent/eligibility/tone validation
│   ├── storage/                # SQLAlchemy models, DB connection
│   ├── eval/                   # Metrics harness
│   └── tests/                  # Unit & integration tests
├── frontend/                   # React operator dashboard
├── shared/                     # Shared types/constants
├── data/                       # Generated datasets (users, transactions, liabilities)
├── scripts/                    # CLI tools (generate_data.py, seed_db.py)
├── docs/                       # Decision log, schema documentation
└── README.md                   # Setup instructions
```

---

## Epic 0: Setup & Scaffolding

**Goal:** Working monorepo with basic infrastructure

### Tasks
- [ x] Initialize monorepo structure (all directories)
- [ x] Set up Python environment
  - FastAPI, SQLAlchemy, pandas, numpy, pytest, pydantic
  - OpenAI SDK for LLM integration
  - `requirements.txt`
- [ ] Set up React frontend
  - Vite or Create React App
  - Basic routing structure
  - API client setup
- [ ] Configure SQLite database
  - Initial schema (users, accounts, transactions, liabilities, consent)
  - SQLAlchemy models
- [ ] Basic FastAPI "hello world" endpoint
- [ ] React app connecting to API
- [ ] README with setup instructions
  - `pip install -r requirements.txt`
  - `npm install`
  - How to run both servers

### Done When
- `npm install && pip install -r requirements.txt` runs successfully
- Both backend and frontend servers start
- Basic API health check works

---

## Epic 1: Data Generation

**Goal:** Synthetic Plaid-style dataset for 50-100 users with 6+ months of history

### Tasks
- [ ] Define Plaid schema models (Pydantic)
  - **Accounts:** account_id, type/subtype, balances, currency, holder_category
  - **Transactions:** account_id, date, amount, merchant_name, payment_channel, personal_finance_category, pending
  - **Liabilities:** credit cards (APR, min_payment, is_overdue), mortgages/loans (interest_rate, next_payment)
- [ ] Build user archetype templates
  - High earner with debt
  - Gig worker (variable income)
  - Steady income, building savings
  - Subscription-heavy spender
  - Paycheck-to-paycheck
  - High credit utilization
- [ ] Transaction generator
  - Realistic recurring patterns (subscriptions, payroll)
  - Variable spending (groceries, dining, entertainment)
  - 6+ months of transaction history
  - Dates that support 30d and 180d windows
- [ ] Liability data generator
  - Credit cards with varying utilization, APRs, payment history
  - Some with overdue status, minimum payments only
- [ ] CLI script: `python scripts/generate_data.py --users 100 --seed 42`
- [ ] Output to JSON/CSV in `/data` folder
- [ ] Database seeding script: `python scripts/seed_db.py`

### Tests
- [ ] `test_generate_users_creates_valid_plaid_schema()`
- [ ] `test_transactions_have_realistic_date_ranges()`
- [ ] `test_synthetic_data_includes_diverse_scenarios()`
- [ ] `test_data_generator_is_deterministic_with_seed()`

### Done When
- Generated data validates against Plaid schema
- Dataset covers diverse financial situations
- 50-100 users with 6+ months of transaction history
- Data can be regenerated with different parameters

---

## Epic 2: Feature Engineering

**Goal:** Signal detection from transaction data (30d and 180d windows)

### Tasks
- [ ] Subscription detection
  - Recurring merchants (≥3 occurrences in 90 days)
  - Monthly/weekly cadence analysis
  - Monthly recurring spend calculation
  - Subscription share of total spend
- [ ] Savings analysis
  - Net inflow to savings-like accounts (savings, money market, HSA)
  - Growth rate calculation
  - Emergency fund coverage = savings balance / avg monthly expenses
- [ ] Credit metrics
  - Utilization = balance / limit
  - Flags for ≥30%, ≥50%, ≥80% utilization
  - Minimum-payment-only detection
  - Interest charges present
  - Overdue status tracking
- [ ] Income stability
  - Payroll ACH detection
  - Payment frequency and variability
  - Cash-flow buffer in months
  - Median pay gap calculation
- [ ] Windowing logic (30-day and 180-day)
- [ ] Store computed signals in database
- [ ] API endpoint: `GET /signals/{user_id}`

### Tests
- [ ] `test_subscription_detection_finds_recurring_merchants()`
- [ ] `test_savings_growth_rate_calculation()`
- [ ] `test_credit_utilization_flags_thresholds()`
- [ ] `test_income_stability_payroll_detection()`
- [ ] `test_30_day_vs_180_day_window_differences()`

### Done When
- API endpoint returns behavioral signals for any user_id
- Signals computed for both 30d and 180d windows
- Signal computation completes in <5 seconds per user

---

## Epic 3: Persona System

**Goal:** Assign personas based on behavioral signals with prioritization logic

### Tasks
- [ ] Implement Persona 1: High Utilization
  - Criteria: Any card utilization ≥50% OR interest charges > 0 OR minimum-payment-only OR is_overdue = true
  - Focus: Reduce utilization, payment planning, autopay education
- [ ] Implement Persona 2: Variable Income Budgeter
  - Criteria: Median pay gap > 45 days AND cash-flow buffer < 1 month
  - Focus: Percent-based budgets, emergency fund basics, smoothing strategies
- [ ] Implement Persona 3: Subscription-Heavy
  - Criteria: Recurring merchants ≥3 AND (monthly recurring spend ≥$50 in 30d OR subscription spend share ≥10%)
  - Focus: Subscription audit, cancellation/negotiation tips, bill alerts
- [ ] Implement Persona 4: Savings Builder
  - Criteria: Savings growth rate ≥2% over window OR net savings inflow ≥$200/month, AND all card utilizations < 30%
  - Focus: Goal setting, automation, APY optimization (HYSA/CD basics)
- [ ] Design Persona 5: [Custom - TBD]
  - Document criteria based on behavioral signals
  - Rationale for why this persona matters
  - Primary educational focus
- [ ] Prioritization logic
  - High Utilization > Variable Income > Subscription-Heavy > Savings Builder > Custom
  - Store primary + secondary persona assignments
- [ ] API endpoint: `GET /profile/{user_id}` returns persona + signals

### Tests
- [ ] `test_high_utilization_persona_assignment()`
- [ ] `test_variable_income_persona_assignment()`
- [ ] `test_subscription_heavy_persona_assignment()`
- [ ] `test_savings_builder_persona_assignment()`
- [ ] `test_persona_prioritization_logic()`
- [ ] `test_multiple_persona_matches_returns_highest_priority()`

### Done When
- Every user assigned a primary persona
- Prioritization tested with users matching multiple criteria
- Persona assignment logic documented with clear rationale

---

## Epic 4: Recommendation Engine with LLM

**Goal:** Generate personalized recommendations with rationales (LLM + safe fallbacks)

### Architecture
```
User Request
  ↓
Generate LLM recommendation (OpenAI)
  ↓
Strict Validation
  ↓
├─ PASS → Return LLM output
└─ FAIL → Return template fallback for persona
```

### Tasks

#### 4.1 Template System (Safe Fallbacks)
- [ ] Create template library for all 5 personas
  - 3-5 education items per persona
  - 1-3 partner offers per persona
  - Rationale templates with data placeholders
- [ ] Template rendering engine
  - Fill variables with actual user data
  - Generate rationales citing specific numbers
- [ ] Pre-approved product catalog
  - Balance transfer cards (eligibility: credit score ≥670)
  - High-yield savings accounts (eligibility: any)
  - Budgeting apps (eligibility: variable income)
  - Subscription management tools (eligibility: subscription-heavy)

#### 4.2 LLM Integration
- [ ] OpenAI API setup (GPT-4)
- [ ] Prompt engineering
  - System prompt with strict constraints
  - Prohibited products list (payday loans, crypto, etc.)
  - Prohibited claims (guaranteed, promise, risk-free)
  - Required elements (disclaimer, data citations)
  - Tone guidelines (supportive, non-judgmental)
- [ ] Structured output (JSON schema)
  - recommendation text
  - rationale with data citations
  - tone_check flag
  - disclaimer
- [ ] LLM call wrapper with error handling

#### 4.3 Validation Pipeline
- [ ] Prohibited content checker
  - Prohibited products (payday loan, crypto, forex)
  - Prohibited claims (guaranteed, will improve, risk-free)
  - Blocklist of shaming phrases
- [ ] Data citation verifier
  - Extract numbers/claims from rationale
  - Verify against actual user data
  - Ensure card numbers, percentages, amounts match
- [ ] Tone validator
  - Check for judgmental language
  - Ensure supportive, educational tone
- [ ] Required elements checker
  - "This is educational content, not financial advice"
  - "Consult a licensed advisor"
- [ ] Validation result logging

#### 4.4 Recommendation Engine
- [ ] Recommendation ranking algorithm
  - Map persona to relevant content
  - Score by signal relevance and recency
  - Diversity constraint (mix education + offers)
- [ ] Eligibility filtering
  - Check minimum income/credit requirements
  - Filter based on existing accounts
  - No duplicate product types
- [ ] Fallback logic
  - If LLM validation fails → use template
  - If LLM call errors → use template
  - Always return 3-5 education + 1-3 offers
- [ ] API endpoint: `GET /recommendations/{user_id}`
- [ ] Audit logging
  - Track LLM vs template usage
  - Log validation failures with reasons
  - Decision trace for each recommendation

### Tests
- [ ] `test_template_generation_fills_user_data()`
- [ ] `test_llm_validation_rejects_prohibited_products()`
- [ ] `test_llm_validation_rejects_prohibited_claims()`
- [ ] `test_data_citation_verification()`
- [ ] `test_tone_validation_blocks_shaming_language()`
- [ ] `test_fallback_to_template_on_validation_failure()`
- [ ] `test_recommendations_include_required_disclaimer()`
- [ ] `test_eligibility_filters_ineligible_offers()`

### Done When
- API returns 3-5 education items + 1-3 offers with rationales
- LLM outputs validated with strict checks
- Safe template fallbacks exist for all personas
- Audit log tracks LLM success rate and validation failures
- All recommendations cite specific user data

---

## Epic 5: Guardrails

**Goal:** Consent, eligibility, tone enforcement

### Tasks

#### 5.1 Consent System
- [ ] Database schema for consent tracking
  - user_id, consent_status (bool), consent_date, revoked_date
- [ ] API endpoints
  - `POST /consent` - Record user consent
  - `DELETE /consent/{user_id}` - Revoke consent
  - `GET /consent/{user_id}` - Check consent status
- [ ] Consent enforcement in recommendation engine
  - Block processing without consent
  - Return error or limited response
- [ ] Synthetic data includes consent flags
  - Some users opted in, some didn't

#### 5.2 Eligibility System
- [ ] Product eligibility rules
  - Minimum income requirements
  - Credit score requirements
  - Existing account checks (don't offer savings if they have one)
- [ ] Eligibility checker service
  - Filter offers based on user data
  - No recommendations for ineligible products
- [ ] Harmful product blocklist
  - Payday loans
  - Predatory lending products
  - High-risk investments

#### 5.3 Tone Enforcement
- [ ] Prohibited phrase database
  - "you're overspending"
  - "bad decision"
  - "irresponsible"
  - "wasteful"
- [ ] Tone validation in recommendation pipeline
  - Run on all LLM outputs
  - Block outputs with violations
- [ ] Positive language guidelines documented

#### 5.4 Disclosure System
- [ ] Standard disclaimer injection
  - "This is educational content, not financial advice. Consult a licensed advisor for personalized guidance."
  - Automatically appended to all recommendations
- [ ] Product-specific disclaimers
  - Balance transfer fees
  - Variable APY
  - FDIC insurance status

### Tests
- [ ] `test_recommendations_blocked_without_consent()`
- [ ] `test_consent_revocation_stops_processing()`
- [ ] `test_ineligible_offers_filtered()`
- [ ] `test_tone_validation_blocks_shaming_language()`
- [ ] `test_harmful_products_never_recommended()`
- [ ] `test_disclaimer_present_on_all_recommendations()`

### Done When
- Consent tracked and enforced in database
- Recommendations blocked without consent
- Eligibility filters prevent ineligible offers
- Tone checks enforce supportive language
- Standard disclaimer on all recommendations
- Harmful products never suggested

---

## Epic 6: Operator Dashboard

**Goal:** Functional React UI for human oversight

### Tasks

#### 6.1 User List View
- [ ] Display all users with key info
  - User ID, name (masked)
  - Primary persona
  - Consent status
  - Last updated
- [ ] Filtering options
  - By persona
  - By consent status
  - By validation issues
- [ ] Search functionality

#### 6.2 User Detail View
- [ ] Behavioral signals display
  - 30-day signals
  - 180-day signals
  - Visual indicators (charts/badges)
- [ ] Persona assignment
  - Primary and secondary personas
  - Criteria that triggered assignment
- [ ] Decision trace
  - Timeline of signal detection → persona → recommendations
  - Why each recommendation was selected
  - Validation results (LLM vs template)

#### 6.3 Recommendation Review
- [ ] Generated recommendations display
  - Education items with rationales
  - Partner offers with eligibility info
  - Source indicator (LLM or template)
- [ ] Validation status
  - Passed/failed checks
  - Specific failure reasons
- [ ] Override mechanism
  - Approve/reject recommendations
  - Add notes

#### 6.4 Audit & Monitoring
- [ ] LLM performance metrics
  - Success rate
  - Validation failure breakdown
  - Template fallback rate
- [ ] System health indicators
  - Latency per user
  - Coverage percentage
  - Consent status breakdown
- [ ] Flagged items queue
  - Validation warnings
  - High-risk scenarios

### Done When
- Dashboard displays all users with persona assignments
- User detail view shows signals, decision trace, recommendations
- Validation results visible (LLM vs template)
- Operator can review and override recommendations
- Audit metrics displayed (LLM success rate, coverage, latency)

---

## Epic 7: Evaluation & Testing

**Goal:** Metrics harness + comprehensive test suite

### Tasks

#### 7.1 Core Metrics Implementation
- [ ] Coverage metric
  - % of users with assigned persona
  - % of users with ≥3 detected behaviors
  - Target: 100%
- [ ] Explainability metric
  - % of recommendations with plain-language rationales
  - % with data citations
  - Target: 100%
- [ ] Latency benchmarking
  - Time to generate recommendations per user
  - 30d vs 180d window computation time
  - Target: <5 seconds
- [ ] Auditability metric
  - % of recommendations with decision traces
  - Completeness of audit logs
  - Target: 100%

#### 7.2 Additional Metrics
- [ ] LLM performance tracking
  - Success rate (validation pass)
  - Failure breakdown by type
  - Template fallback rate
- [ ] Fairness analysis
  - Demographic parity (if synthetic data includes demographics)
  - Offer distribution across personas
  - No discriminatory patterns

#### 7.3 Test Suite Completion
- [ ] Achieve ≥10 unit/integration tests
- [ ] Edge case testing
  - Users with no clear persona
  - Users matching multiple personas
  - Users with minimal transaction history
- [ ] Adversarial testing
  - Try to trick LLM into prohibited content
  - Attempt consent bypass
  - Ineligible offer edge cases
- [ ] End-to-end integration tests
  - Full pipeline: data → signals → persona → recommendations
  - API endpoint testing
  - Database operations

#### 7.4 Metrics Output
- [ ] Generate JSON metrics file
- [ ] Summary report (1-2 pages)
  - All metrics with pass/fail
  - LLM vs template comparison
  - Fairness analysis results
  - System limitations documented
- [ ] Per-user decision traces exported

### Done When
- All metrics hit target thresholds (100% coverage, <5s latency, etc.)
- ≥10 tests passing
- Metrics report generated (JSON + summary doc)
- Fairness analysis complete
- System limitations documented

---

## Epic 8: Documentation & Polish

**Goal:** Complete project deliverables and polish

### Tasks

#### 8.1 Decision Log
- [ ] Document key architectural decisions
  - Why Python + FastAPI?
  - Why LLM with template fallbacks?
  - Persona prioritization rationale
  - Custom persona justification
- [ ] Limitations documentation
  - Synthetic data constraints
  - LLM validation edge cases
  - Scalability boundaries
- [ ] Future improvements list

#### 8.2 Schema Documentation
- [ ] Plaid schema reference
- [ ] Database schema with relationships
- [ ] API endpoint documentation
  - Request/response formats
  - Error codes
  - Rate limits (if any)

#### 8.3 End-User Experience Mock
- [ ] Choose format (Figma, screenshots, simple React demo, email template)
- [ ] Show personalized dashboard concept
  - User's persona
  - Top 3 recommendations with rationales
  - Education content preview
  - Partner offers
- [ ] Demonstrate consent flow
- [ ] Mobile-friendly design (optional)

#### 8.4 README Polish
- [ ] Architecture diagram
- [ ] Setup instructions
  - Prerequisites
  - Installation steps
  - Data generation
  - Running the system
- [ ] Demo walkthrough
  - How to view operator dashboard
  - How to generate new users
  - How to test different personas
- [ ] Testing instructions
- [ ] Troubleshooting section

#### 8.5 Code Cleanup
- [ ] Remove commented-out code
- [ ] Add docstrings to key functions
- [ ] Type hints throughout
- [ ] Consistent code formatting (black, prettier)
- [ ] Remove debug print statements

### Done When
- Decision log complete with rationale for key choices
- Schema fully documented
- End-user experience mock created
- README has clear setup and demo instructions
- Code is clean, well-commented, and formatted
- Project ready for review/demo

---

## Testing Strategy Summary

**Map tests early (during Epics 1-5), implement alongside features:**

### Epic 1 Tests (4 tests)
- Synthetic data validation
- Schema compliance
- Deterministic generation
- Diverse scenarios

### Epic 2 Tests (5 tests)
- Signal detection accuracy
- Window calculations
- Feature engineering correctness

### Epic 3 Tests (6 tests)
- Persona assignment logic
- Prioritization rules
- Multi-persona handling

### Epic 4 Tests (8 tests)
- Template generation
- LLM validation
- Fallback logic
- Eligibility filtering

### Epic 5 Tests (6 tests)
- Consent enforcement
- Eligibility rules
- Tone validation
- Harmful product blocking

**Total: 29 tests (exceeds ≥10 requirement)**

---

## Key Principles

Throughout implementation, adhere to these core principles:

1. **Compliance First:** No recommendation ships without passing strict validation
2. **Transparency over Sophistication:** Simple, explainable logic beats black-box complexity
3. **User Control:** Consent required, easily revocable
4. **Education over Sales:** Focus on learning, not product pushing
5. **Fairness Built In:** No discriminatory patterns, equal treatment
6. **Auditability:** Every decision logged with clear rationale
7. **Safe Defaults:** Template fallbacks ensure quality even if LLM fails

---

## Risk Mitigation

### Legal/Regulatory Risks
- **Mitigation:** Strict validation, prohibited content lists, required disclaimers, no guarantees
- **Testing:** Adversarial tests for prohibited content

### LLM Unreliability
- **Mitigation:** Template fallbacks for all personas, validation pipeline
- **Testing:** Track LLM success rate, ensure templates cover 100%

### Data Quality
- **Mitigation:** Synthetic data generator with diverse scenarios, schema validation
- **Testing:** Validate generated data against Plaid schema

### Performance
- **Mitigation:** Pre-compute signals, cache results, optimize queries
- **Testing:** Latency benchmarking (<5s target)

---

## Success Metrics Recap

At project completion, verify:

- ✅ 100% of users have assigned persona + ≥3 detected behaviors
- ✅ 100% of recommendations have plain-language rationales
- ✅ <5 seconds to generate recommendations per user
- ✅ 100% of recommendations have decision traces
- ✅ ≥10 unit/integration tests passing
- ✅ Complete schema and decision log documentation
- ✅ No harmful suggestions pass validation
- ✅ LLM validation + template fallbacks working

---

## Notes

- This is a **demo/prototype project**, not production software
- Focus on **architecture and principles** over scale
- **Explainability** is more important than sophistication
- Every recommendation must be **auditable and defensible**
- The system should **fail safe** (templates) rather than fail open


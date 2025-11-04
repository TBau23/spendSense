# SpendSense - Decision Log

**Format**: Each decision includes Epic, Decision, Rationale, Alternatives Considered, and Impact. Additions should be kept minimal and concise. Only add decisions that are critical to the project.

---

## Pre-Epic: Roadmap Clarifications

### Decision: LLM Scope Limited to Content Generation
**Epic**: Roadmap Planning  
**Decision**: Use LLM only for generating educational content text. All logic (persona assignment, eligibility checks, signal detection) is rules-based.  
**Rationale**: Ensures explainability, auditability, and deterministic behavior required for financial applications.  
**Alternatives Considered**: 
- ML-based persona assignment: Rejected due to black-box nature
- LLM-generated rationales: Rejected to ensure factual accuracy from real data
**Impact**: Epic 4 (Recommendation Engine) design, evaluation metrics

### Decision: Generic Templates as Universal Fallback
**Epic**: Roadmap Planning  
**Decision**: Generic templates are universal per persona, pre-approved, used when no operator-approved personalized recs exist. New users without approved recs see nothing (demo scope).  
**Rationale**: Ensures safe fallback without compromising on consent-first principles. Simplifies demo scope.  
**Alternatives Considered**:
- User-specific templates: Rejected due to operator approval overhead
- Always show something to new users: Rejected to maintain consent-first purity
**Impact**: Epic 4 (template generation), Epic 5 (operator workflow)

### Decision: Simplified Context Management
**Epic**: Roadmap Planning  
**Decision**: Context handoffs between epics require only: (1) Decision Log updates, (2) Next Epic Prerequisites documentation. Task list completion tracks implementation progress.  
**Rationale**: Minimizes overhead while ensuring critical architectural decisions and dependencies are captured.  
**Alternatives Considered**:
- Full State of Implementation docs: Rejected as redundant with task lists
- API contract freezes: Deferred to per-epic needs
**Impact**: All epics, agent workflow efficiency

### Decision: Relevance and Fairness Implicit
**Epic**: Roadmap Planning  
**Decision**: Relevance and fairness metrics are implicitly covered by consent management and rules-based persona assignment. No additional tracking needed.  
**Rationale**: Consent ensures only willing users processed. Rules-based logic is transparent and auditable by design.  
**Alternatives Considered**:
- Explicit fairness metrics: Rejected as redundant for synthetic demo data
- Manual relevance scoring: Rejected as covered by operator review process
**Impact**: Epic 6 (Evaluation)

### Decision: Persona 5 Changed to Cash Flow Stressed
**Epic**: Epic 1 Planning  
**Decision**: Persona 5 is "Cash Flow Stressed" (checking balance frequently near zero + high volatility) instead of "Fee Accumulator". No fees table needed.  
**Rationale**: Avoids adding extra table just for one persona. Cash flow stress is detectable from existing account balance + transaction data. Captures paycheck-to-paycheck users distinct from other personas.  
**Alternatives Considered**:
- Fee Accumulator with dedicated fees table: Rejected as over-engineered
- Lifestyle Inflator (spending > income): Considered but harder to measure income accurately
**Impact**: Epic 1 (schema simplified), Epic 2 (cash flow signals instead of fee tracking)

---

## Epic 1: Data Foundation

### Decision: PII Masking with Faker Library
**Epic**: Epic 1  
**Decision**: Use `Faker` library for generating synthetic names and PII.  
**Rationale**: Standard approach, well-maintained, generates realistic data without privacy concerns.  
**Impact**: Data generation module dependencies

### Decision: Plaid Format Where It Adds Value
**Epic**: Epic 1  
**Decision**: Match Plaid format (e.g., `acc_xxxxx`, `txn_xxxxx`) only where it adds realism value.  
**Rationale**: Provides familiarity without over-engineering. Focus on data quality over perfect format matching.  
**Impact**: Account and transaction ID generation

### Decision: Minimal Pending Transactions
**Epic**: Epic 1  
**Decision**: Only include pending transactions if they impact persona classification (likely not needed for demo).  
**Rationale**: Simplifies generation. Most personas rely on completed transaction patterns.  
**Impact**: Transaction generation logic

### Decision: Chronological Transaction Generation with Running Balances
**Epic**: Epic 1  
**Decision**: Generate transactions chronologically while maintaining running balances, especially for Cash Flow Stressed archetype validation.  
**Rationale**: Ensures Cash Flow Stressed users actually hit low balance thresholds realistically. Critical for archetype validity.  
**Impact**: Transaction generation complexity, but guarantees good data quality

### Epic 1 Complete ✓

**Completed**: November 4, 2025  
**Duration**: ~1 hour  
**Tests**: 10/10 passing  
**Data Generated**: 75 users, 204 accounts, 11,624 transactions, 80 liabilities

### Next Epic Prerequisites
- [x] SQLite schema finalized and documented (4 tables: users, accounts, transactions, liabilities)
- [x] Synthetic data generation produces 50-100 users (75 users generated)
- [x] 90% consent=true, 10% consent=false distribution achieved (89.3% actual, within tolerance)
- [x] All 5 persona types represented in user archetypes (all archetypes represented)
- [x] Data validation pipeline working (validation report generated)

### Decision: Transaction Generation Expense Fixes (Post-Epic 2 Discovery)
**Epic**: Epic 1 Refinement  
**Decision**: Fixed transaction generation to produce realistic balances through: (1) Mandatory monthly rent (was 50% chance), (2) 60% daily expense frequency (up from 30%), (3) Archetype-specific expense targets (95% for stressed, 75% normal, 60% for savers), (4) Aggressive balance management for cash flow stressed users (large expenses when balance >$1000).  
**Rationale**: Original generation had income consistently exceeding expenses, causing unbounded balance growth ($45k-$69k). This prevented Cash Flow Stressed and Variable Income personas from being detectable by Epic 2 features.  
**Alternatives Considered**:
- Budget-based generation: Too complex, less organic patterns
- Post-generation adjustment: Hacky, breaks chronological integrity
**Impact**: Epic 1 transaction generation quality (11,624 → 17,130 transactions). Fixed Cash Flow Stressed (0→20 users) and Variable Income (0→6 users) detection.

### Decision: Savings Net Inflow Sign Correction
**Epic**: Epic 2 Feature Engineering  
**Decision**: Negate savings transaction sum to convert Plaid convention to semantic meaning: `net_inflow = -savings_txns['amount'].sum()`  
**Rationale**: Plaid convention stores deposits as negative, withdrawals as positive. For user-facing features, positive net_inflow should mean "money coming in". Without negation, all savings accounts showed negative growth rates despite receiving transfers.  
**Alternatives Considered**:
- Filter by transaction type: More code, same result
- Change Plaid convention throughout: Would break everything else
**Impact**: Fixed Savings Builder detection (0→32 users). All 6/6 persona validations now pass.

---

## Epic 2: Feature Engineering

### Decision: Rolling Windows with as_of_date Parameter
**Epic**: Epic 2  
**Decision**: Implement rolling windows using dynamic `as_of_date` parameter (defaults to current date). Features computed for date ranges relative to as_of_date (30d and 180d windows).  
**Rationale**: Data generation is already date-aware. Enables fresh demo runs with different dates while maintaining seed reproducibility.  
**Alternatives Considered**:
- Fixed windows from static demo date: Rejected, limits demo flexibility
**Impact**: Feature computation module accepts as_of_date, Parquet includes computed_date column

### Decision: Reconstruct Daily Balances On-the-Fly
**Epic**: Epic 2  
**Decision**: Compute daily balances by chronologically replaying transactions during feature computation. Don't store balance snapshots separately.  
**Rationale**: One-time computation cached in Parquet (~15k operations for 75 users negligible). Avoids Epic 1 schema changes and storage overhead.  
**Alternatives Considered**:
- Store daily balance snapshots: Rejected as over-engineered for demo
**Impact**: cash_flow.py includes chronological replay logic

### Decision: Subscription Cadence Detection Tolerance
**Epic**: Epic 2  
**Decision**: Recurring merchant detected if ≥3 occurrences in 90 days AND ≥70% of payment gaps match monthly (28-32 days) OR weekly (5-9 days) cadence.  
**Rationale**: ±2 day tolerance handles billing date drift. 70% threshold filters one-off purchases while allowing normal variation.  
**Impact**: subscriptions.py gap analysis logic

### Decision: Compute Features for All Users
**Epic**: Epic 2  
**Decision**: Compute features for both consented and non-consented users. Consent filtering deferred to Epic 5 operator view.  
**Rationale**: Simplifies Epic 2 implementation, clean separation of concerns, enables full testing. Operator never sees non-consented data (Epic 5 enforcement).  
**Alternatives Considered**:
- Skip non-consented users: Rejected, adds Epic 2 complexity
**Impact**: Epic 5 must filter features by consent_status before display

### Decision: Plaid Schema Alignment
**Epic**: Epic 2  
**Decision**: Use Plaid-style schema with `account_type='depository'/'credit'` and `account_subtype='checking'/'savings'/'credit_card'` instead of flat account_type values.  
**Rationale**: Matches actual Epic 1 implementation and Plaid API structure. Discovered during feature computation when all features initially returned 0.0.  
**Impact**: Required updates to all feature modules (credit.py, savings.py, utils.py) and tests

### Decision: Plaid Transaction Sign Convention
**Epic**: Epic 2  
**Decision**: Correctly implement Plaid's transaction sign convention: POSITIVE = expenses (money out), NEGATIVE = income (money in).  
**Rationale**: Epic 1 correctly follows Plaid API convention where amounts are from account holder's perspective. Initial Epic 2 implementation incorrectly assumed opposite convention (expenses negative). Fixed by changing all feature modules to filter `amount > 0` for expenses and `amount < 0` for income.  
**Alternatives Considered**:
- Keep incorrect assumption: Rejected, would miss all subscription detection
**Impact**: Fixed subscription detection (0 → 75 users), all signal types now correctly interpreting transaction amounts per Plaid convention

### Epic 2 Complete ✓

**Completed**: November 4, 2025  
**Tests**: 14/14 passing  
**Features Computed**: 5 signal types × 2 windows × 75 users = 750 feature rows

**Validation Results**:
- ✓ 100% coverage: All 75 users have features for both windows
- ✓ High utilization: 17 users detected with ≥50% credit utilization
- ✓ Subscription Heavy: **ALL 75 users** detected with ≥3 recurring merchants (fixed after sign convention correction)
- ⚠ Savings Builder: 0 users (growth rates ≤0 in Epic 1 data)
- ⚠ Variable Income: 0 users (cash buffers too high, pay gaps too regular)
- ⚠ Cash Flow Stressed: 0 users (checking balances $45k-$69k too high)

**Known Limitations**:
- Epic 1 checking balances very high ($45k-$69k) - acknowledged by Epic 1 as "not enough expenses"
- Savings growth rates negative/zero - needs investigation of savings transfer generation in Epic 1
- Variable income gaps not meeting >45 day threshold - payroll generation too regular
- Feature computation working correctly after sign convention fix

### Next Epic Prerequisites
- [x] All signal types compute successfully (subscriptions, savings, credit, income, cash_flow)
- [x] 30-day and 180-day windows implemented
- [x] Feature outputs stored in Parquet
- [x] Feature validation tests passing (14/14)
- [⚠] Feature values partially align with Epic 1 archetypes (credit works, others limited by data)

---

## Epic 3: Persona System

### Next Epic Prerequisites
- [ ] All 5 personas assign correctly based on criteria
- [ ] Prioritization logic working (CRITICAL > HIGH > MEDIUM > LOW)
- [ ] Multi-persona handling (primary + secondary tracking)
- [ ] Edge case tests passing

*(Decisions to be added during Epic 3 implementation)*

---

## Epic 4: Recommendation Engine

### Next Epic Prerequisites
- [ ] LLM content generation operational
- [ ] Rules-based rationale generation citing user data
- [ ] Educational content catalog organized by persona
- [ ] Partner offer eligibility rules implemented
- [ ] Generic templates pre-generated and approved

*(Decisions to be added during Epic 4 implementation)*

---

## Epic 5: Guardrails & Operator View

### Next Epic Prerequisites
- [ ] Consent grant/revoke workflow functional
- [ ] Operator dashboard UI operational
- [ ] Approve/flag/override mechanisms working
- [ ] Decision trace viewer implemented

*(Decisions to be added during Epic 5 implementation)*

---

## Epic 6: Evaluation & Polish

*(Decisions to be added during Epic 6 implementation)*

---

## Template for New Decisions

### Decision: [Short Title]
**Epic**: [Epic Number/Name]  
**Decision**: [What was chosen]  
**Rationale**: [Why this approach]  
**Alternatives Considered**: [What was rejected and why]  
**Impact**: [Which modules/epics affected]


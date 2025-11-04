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

---

## Epic 2: Feature Engineering

### Next Epic Prerequisites
- [ ] All signal types compute successfully (subscriptions, savings, credit, income, cash_flow)
- [ ] 30-day and 180-day windows implemented
- [ ] Feature outputs stored in Parquet
- [ ] Feature validation tests passing

*(Decisions to be added during Epic 2 implementation)*

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


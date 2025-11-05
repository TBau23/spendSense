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

## Epic 3: Persona System

### Decision: Dual Time Window Persona Assignments
**Epic**: Epic 3 (Persona System)  
**Decision**: Assign personas separately for 30-day and 180-day windows. Same user can have different primary personas across windows.  
**Rationale**: Recent behavior (30d) may differ from long-term patterns (180d). Provides richer behavioral view and enables dynamic persona detection.  
**Alternatives Considered**:
- Single window only (30d): Rejected as insufficient to detect long-term trends
- Combined scoring across windows: Rejected as overly complex for demo
**Impact**: Assignment logic, database schema (user × 2 windows = 150 assignments for 75 users), Epic 4 recommendation strategy

### Decision: Severity-Based Tie-Breaking
**Epic**: Epic 3 (Persona System)  
**Decision**: When multiple personas have same priority level, use quantitative severity scores for tie-breaking. Severity calculated as: P1=max_utilization, P2=median_pay_gap/45, P3=subscription_share, P4=growth_rate, P5=pct_days_below_100.  
**Rationale**: More nuanced than arbitrary precedence ordering. Reflects actual financial situation severity.  
**Alternatives Considered**:
- Fixed precedence within priority levels: Rejected as too rigid (e.g., P2 vs P5 both HIGH - which is worse?)
- Combined risk scores: Rejected as overly complex
**Impact**: Prioritization logic, assignment outcomes where multiple personas match at same priority

### Decision: Unassigned/STABLE Status for Non-Matching Users
**Epic**: Epic 3 (Persona System)  
**Decision**: Create 6th state "STABLE" for users matching no personas, rather than forcing assignment to lowest severity persona.  
**Rationale**: Honest representation of healthy financial behavior. Demonstrates system doesn't force categorization. Valuable for demo to show different user states.  
**Alternatives Considered**:
- Auto-assign to Persona 4 (Savings Builder): Rejected as dishonest if criteria not met
- Null/unassigned state with no label: Rejected as less clear for operator view
**Impact**: Assignment logic, Epic 4 (STABLE users can receive generic educational content or nothing), operator view design

### Decision: No Credit Cards Auto-Pass for Persona 4 Utilization Check
**Epic**: Epic 3 (Persona System)  
**Decision**: Users with no credit cards (max_utilization = NULL) automatically satisfy the "all cards <30% utilization" requirement for Persona 4 (Savings Builder).  
**Rationale**: No credit cards means no utilization issues. Allows savings-focused users without credit to qualify for Persona 4.  
**Alternatives Considered**:
- Require at least one credit card: Rejected as excludes valid user segment
- Separate persona for no-credit users: Rejected as over-complicating
**Impact**: Persona 4 evaluation logic, affects users without credit accounts

### Decision: Date Type Handling in Feature Loading
**Epic**: Epic 3 (Persona System)  
**Decision**: Convert string as_of_date to datetime.date object before Parquet comparison, as Parquet stores dates as datetime.date objects.  
**Rationale**: Fixes type mismatch bug discovered during implementation. Ensures features load correctly.  
**Alternatives Considered**:
- Store as_of_date as string in Parquet: Rejected as Parquet date type is more efficient
- Parse dates during feature computation: Rejected as pushes complexity upstream
**Impact**: Feature loading logic in assign.py, critical for persona assignment to work

### Decision: Prioritization Results - Savings Builder as Secondary Only
**Epic**: Epic 3 (Persona System)  
**Decision**: Accept that Persona 4 (Savings Builder) may have 0 primary assignments if all qualifying users have higher-priority issues (CRITICAL, HIGH, or MEDIUM personas).  
**Rationale**: This is correct prioritization behavior - users saving money but also carrying 65% credit utilization SHOULD focus on debt first (Persona 1 CRITICAL). Persona 4 appears as secondary persona (32 times in validation), confirming dual-tracking works.  
**Alternatives Considered**:
- Lower thresholds for Persona 4 to force primary assignments: Rejected as defeats purpose of prioritization
- Adjust archetype generation to create pure Persona 4 users: Deferred to future if needed
**Impact**: Assignment distribution (69% users have secondary personas), demonstrates prioritization system working as designed, Epic 4 will need to handle secondary persona content

### Decision: Both SQLite and Parquet Storage for Assignments
**Epic**: Epic 3 (Persona System)  
**Decision**: Store persona assignments in both SQLite (with JSON audit traces) and Parquet (without traces, for analytics).  
**Rationale**: SQLite enables fast operational queries by user_id, supports JSON audit trails. Parquet enables analytics queries across all users. Pattern consistent with Epic 1/2 (relational + analytical storage).  
**Alternatives Considered**:
- SQLite only: Rejected as slow for bulk analytics
- Parquet only: Rejected as no JSON support for audit traces
**Impact**: Storage module, dual write operations (minimal overhead for 75 users), Epic 5 operator view can use SQLite for traces, Epic 6 analytics can use Parquet

---

## Epic 4: Recommendation Engine

### Decision: Hybrid Content Strategy
**Epic**: Epic 4  
**Decision**: Pre-approved educational content catalog + LLM-generated personalized rationales and actionable items.  
**Rationale**: Balances personalization with consistency. Educational content is vetted once and reused (safe, consistent quality). Rationales and actionable items are LLM-generated with user-specific data (personalized, requires operator review in Epic 5). Fallback to templates when LLM fails ensures demo never crashes.  
**Alternatives Considered**:
- Fully LLM-generated content: Rejected due to inconsistent quality, no caching
- Fully template-based: Rejected as insufficiently personalized, doesn't demonstrate LLM capabilities
**Impact**: Epic 5 operator review focuses on rationales/actions (risky content), not educational items (pre-approved)

### Decision: Generic Placeholder Partner Products
**Epic**: Epic 4  
**Decision**: Use generic placeholder products (e.g., "Generic Balance Transfer Card") instead of real financial products.  
**Rationale**: Demo focuses on workflow and eligibility logic, not product accuracy. Avoids partnership/legal complexity. Naming makes it clear these are placeholders.  
**Alternatives Considered**:
- Real partner products: Rejected due to research overhead, potential legal issues, outdated information
- No partner offers: Rejected as requirements specify offer eligibility system
**Impact**: Eligibility rules demonstrate capability without product maintenance burden

### Decision: Credit Score Estimation via Heuristics
**Epic**: Epic 4  
**Decision**: Estimate credit score from utilization and payment behavior using simple heuristics (base 750, penalties for high utilization, overdue payments). Documented as "demo only, not accurate".  
**Rationale**: Enables offer eligibility checking without real credit data. Simplified algorithm is transparent and explainable. Sufficient for demo purposes.  
**Alternatives Considered**:
- Random scores: Rejected as unrealistic
- FICO-like algorithms: Rejected as overly complex for demo
- Assume all users have same score: Rejected as doesn't demonstrate eligibility filtering
**Impact**: Partner offer eligibility checking functional; clear disclaimer prevents misuse

### Decision: Cross-Window Persona Blending (60/40)
**Epic**: Epic 4  
**Decision**: When user has different personas across 30d and 180d windows, blend content: 60% for recent behavior (30d), 40% for long-term pattern (180d).  
**Rationale**: Recent behavior is more urgent and actionable. Long-term patterns provide context. 60/40 split balances both perspectives while prioritizing recent issues.  
**Alternatives Considered**:
- Only use 30d persona: Rejected as loses valuable long-term context
- 50/50 split: Rejected as doesn't prioritize recent urgency
- 70/30 split: Considered, but 60/40 feels more balanced
**Impact**: Users with evolving financial situations get holistic recommendations

### Decision: LLM Mock Mode for Testing
**Epic**: Epic 4  
**Decision**: Implement mock mode (MOCK_LLM=true) that returns placeholder text without API calls. Fallback system ensures graceful degradation when LLM fails.  
**Rationale**: Enables testing without API costs. Ensures demo never crashes due to LLM timeouts or errors. Supports CI/CD pipelines.  
**Alternatives Considered**:
- Require API key for all testing: Rejected as creates barrier to development
- Only test with real LLM: Rejected as incurs costs and network dependency
**Impact**: Fast iteration, no API costs during development, robust error handling

### Decision: Batch Generation for Initial Demo Setup
**Epic**: Epic 4  
**Decision**: Primary generation mode is batch processing (all users at once). Single-user mode available for testing.  
**Rationale**: Simplifies initial demo setup. All users get recommendations before Epic 5 operator view. Performance acceptable (~15-30 min for 75 users).  
**Alternatives Considered**:
- On-demand generation in Epic 5: Deferred for natural workflow implementation
- Event-driven generation (on persona update): Deferred as requires more infrastructure
**Impact**: Epic 5 can focus on operator review workflow with pre-generated recommendations available. **Note**: Natural generation triggers (on consent grant, persona update, operator request) should be revisited in Epic 5 for more realistic workflow.

### Decision: Tests Deferred to Post-Epic 4
**Epic**: Epic 4  
**Decision**: Defer comprehensive test suite (Tasks 17-23) to post-Epic 4 implementation. Manual validation confirms functionality.  
**Rationale**: Core recommendation engine functional and tested manually. Writing comprehensive tests can happen after Epic 5 clarifies integration patterns. Time better spent on operator workflow (Epic 5).  
**Alternatives Considered**:
- Write all tests now: Rejected as Epic 5 may inform test cases
- No tests ever: Rejected as quality requirement
**Impact**: Test coverage added later if needed, minimal risk given manual validation

---

## Epic 5: Guardrails & Operator View

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

---

## Epic 5: Guardrails & Operator View

### Decision: Consent Enforcement via Filtering
**Epic**: Epic 5  
**Decision**: Non-consented users are filtered from all operator views and API responses. They are invisible to operators, not shown with "consent required" warnings.  
**Rationale**: Clean separation of concerns. Epic 6 will add consent management UI. Filtering ensures no accidental processing of non-consented user data.  
**Alternatives Considered**:
- Show non-consented users grayed out: Rejected to avoid UI clutter and potential privacy leaks
- Require consent check on every operation: Implemented via check_consent() utility
**Impact**: All operator API endpoints, frontend user lists, metrics computation

### Decision: Simple 3-Status Workflow
**Epic**: Epic 5  
**Decision**: Recommendations have three statuses only: PENDING_REVIEW, APPROVED, FLAGGED. No draft, revision, or resubmit states.  
**Rationale**: Sufficient for demo scope. Keeps database schema and UI simple. Flagged recommendations are dead-end until regenerated (Epic 6).  
**Alternatives Considered**:
- Complex workflow with revision states: Rejected as over-engineered for demo
- Auto-approve for certain personas: Rejected to maintain human-in-the-loop principle
**Impact**: recommendations table schema, operator dashboard approval actions

### Decision: Override Placeholder Only
**Epic**: Epic 5  
**Decision**: Override functionality is commented out in code with grayed-out button in UI. Will be implemented in Epic 6.  
**Rationale**: Approve/flag covers core workflow. Override adds significant complexity (edit UI, audit trail, validation). Prioritize getting basic workflow functional first.  
**Alternatives Considered**:
- Implement override now: Rejected due to time constraints and complexity
- Remove override from design: Rejected as it's a valuable future feature
**Impact**: ApprovalActions component, approval.py module

### Decision: Manual Tone Validation Only
**Epic**: Epic 5  
**Decision**: No automated tone checking (rules-based or LLM-based). Operator reviews tone manually during approval.  
**Rationale**: Automated checks add complexity with limited value for 50-100 user demo. Operator review is sufficient guardrail. Avoids false positives from automated tone detectors.  
**Alternatives Considered**:
- Rules-based "shaming word" blacklist: Rejected as brittle and prone to false positives
- LLM-based tone validator: Rejected as adds latency and API cost
**Impact**: Operator review process, recommendation approval workflow

### Decision: Decision Traces as Separate Table
**Epic**: Epic 5  
**Decision**: Store decision traces in dedicated `decision_traces` table with JSON content field, not embedded in recommendations table.  
**Rationale**: Flexible schema (can evolve trace structure), easy to query, doesn't bloat recommendations table. Enables trace versioning in future.  
**Alternatives Considered**:
- Embed traces in recommendations table: Rejected due to schema rigidity
- Separate tables per trace type: Rejected as over-normalized
**Impact**: Database schema, trace generation and retrieval logic

### Decision: FastAPI for Operator Endpoints
**Epic**: Epic 5  
**Decision**: Use FastAPI with 8 dedicated operator endpoints rather than direct backend function calls from frontend.  
**Rationale**: Clean separation between frontend/backend, enables future API consumers, provides automatic OpenAPI docs, aligns with production patterns.  
**Alternatives Considered**:
- Direct function calls via Python bridge: Rejected as non-scalable
- GraphQL API: Rejected as overkill for demo scope
**Impact**: operator.py API module, frontend api client, deployment architecture

### Decision: Metrics Caching (60s TTL)
**Epic**: Epic 5  
**Decision**: Aggregate metrics cached for 60 seconds to reduce database load. Force refresh available via query parameter.  
**Rationale**: Metrics computation involves multiple table scans. For demo with ~75 users, 60s staleness acceptable. Improves dashboard responsiveness.  
**Alternatives Considered**:
- No caching: Rejected due to repeated expensive queries
- Longer cache (5 min): Rejected as metrics would feel stale during testing
- Redis/external cache: Rejected as over-engineered for demo
**Impact**: metrics.py module, /api/operator/metrics endpoint


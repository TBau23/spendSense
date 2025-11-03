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

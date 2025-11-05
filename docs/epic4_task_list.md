# Epic 4: Recommendation Engine - Task List

**Status**: Ready for Implementation  
**Design Doc**: `epic4_technical_design.md`  
**Core Problem**: Generate personalized recommendation packages with LLM-powered rationales while maintaining pre-approved educational content catalog

---

## Implementation Tasks

### 1. Recommendation Module Setup
**Task**: Create recommendation module structure and database schema  
**Output**: Module skeleton with SQLite tables and storage utilities  
**Key Files**: 
- `backend/recommend/__init__.py`
- `backend/recommend/storage.py` (SQLite + Parquet utilities)
**Critical**: 
- Create `recommendations` table (user_id, personas, metadata)
- Create `recommendation_items` table (educational, actionable, partner_offer types)
- Create `content_catalog` table (educational content library)
- Create `partner_offers` table (product catalog)
- Create `generic_templates` table (pre-approved fallback content)
- Add indexes for efficient querying
**Estimated Time**: 2-3 hours

---

### 2. Educational Content Catalog
**Task**: Build educational content library with persona mapping  
**Output**: JSON catalog with 15-20 educational items, loaded into SQLite  
**Key Files**: 
- `backend/recommend/content_catalog.json`
- `backend/recommend/content_loader.py`
**Critical**: 
- **Persona 1** (High Utilization): 4-5 items on credit utilization, debt payoff, minimum payments, autopay
- **Persona 2** (Variable Income): 3-4 items on variable income budgeting, emergency funds, cash flow smoothing
- **Persona 3** (Subscription-Heavy): 3-4 items on subscription audits, negotiation, alerts
- **Persona 4** (Savings Builder): 3-4 items on savings goals, HYSA, automation, CDs
- **Persona 5** (Cash Flow Stressed): 3-4 items on paycheck-to-paycheck strategies, buffer building, expense timing
- **Stable**: 1-2 items on financial optimization
- Each item needs: content_id, title, snippet, persona_tags, topics, estimated_read_time
- Content can be placeholder text/lorem ipsum for demo
**Estimated Time**: 3-4 hours

---

### 3. Partner Offer Catalog
**Task**: Build partner product library with eligibility rules  
**Output**: JSON catalog with 8-10 generic placeholder products  
**Key Files**: 
- `backend/recommend/partner_offers.json`
- `backend/recommend/offer_loader.py`
**Critical**: 
- **Persona 1**: Balance Transfer Card (0% APR 18mo), Debt Consolidation Loan
- **Persona 2**: Budgeting App, Income Smoothing Tool
- **Persona 3**: Subscription Management Service, Budgeting App
- **Persona 4**: High-Yield Savings Account (4.5% APY), Certificate of Deposit
- **Persona 5**: Overdraft Protection Service, Low-Fee Checking Account
- Each offer needs: offer_id, product_type, product_name, description, persona_relevance, eligibility_rules (JSON), benefits
- Use generic names like "Generic Balance Transfer Card"
**Estimated Time**: 2-3 hours

---

### 4. Generic Template System
**Task**: Create pre-approved fallback templates for each persona  
**Output**: JSON templates with safe, generic content per persona  
**Key Files**: 
- `backend/recommend/generic_templates.json`
- `backend/recommend/templates.py`
**Critical**: 
- One template per persona (5 templates) + 1 for stable users
- Each template includes: 3-5 educational content references, 1-3 generic actionable items (no user-specific data), 0-2 partner offers
- Actionable items use general language: "Review your statements" not "Pay $150 toward card ending in 4523"
- Mark all items as `generic=true`, `status='PRE_APPROVED'`
**Estimated Time**: 2-3 hours

---

### 5. LLM Client Integration
**Task**: Set up OpenAI API client with error handling  
**Output**: Reusable LLM client with retry logic and fallbacks  
**Key Files**: 
- `backend/recommend/llm_client.py`
**Critical**: 
- OpenAI API key from environment variable `OPENAI_API_KEY`
- Use `gpt-4o-mini` or `gpt-3.5-turbo` for cost efficiency
- Temperature: 0.7, max_tokens: 200
- Timeout: 10 seconds with 2 retry attempts
- Handle API errors gracefully (log warning, return fallback)
- Handle timeout errors (fall back to template-based rationales)
- Handle invalid JSON responses (parse and sanitize)
- Support mock mode for testing (no real API calls)
**Estimated Time**: 2-3 hours

---

### 6. Prompt Templates
**Task**: Design and implement prompt templates for LLM generation  
**Output**: Modular prompt system for different generation tasks  
**Key Files**: 
- `backend/recommend/prompts.py`
**Critical**: 
- **Rationale prompt**: Generate "because" explanations for educational content relevance
  - Input: user metrics, persona, content title
  - Output: <100 word rationale citing specific data
- **Actionable item prompt**: Generate 1-3 specific next steps
  - Input: user metrics, persona, features
  - Output: Specific, measurable actions with rationales
- **Offer relevance prompt**: Explain why partner offer is relevant
  - Input: user metrics, persona, offer details
  - Output: <80 word relevance explanation
- All prompts emphasize: empowering language, cite specific data, avoid jargon, no "you should" (use "you might consider")
- Include persona-specific guidelines in prompts
**Estimated Time**: 3-4 hours

---

### 7. Content Selection Logic
**Task**: Implement educational content selection based on persona(s)  
**Output**: Function that selects 3-5 relevant items from catalog  
**Key Files**: 
- `backend/recommend/content_selector.py`
**Critical**: 
- Load content catalog from SQLite
- Filter by persona_tags matching target personas
- If single persona: select 5 items
- If cross-window personas (30d ≠ 180d): select 3 items from primary (30d) + 2 from secondary (180d)
- Prioritize exact persona matches over secondary tags
- Ensure variety (don't pick 5 articles if videos/tools available)
- Shuffle results for variety across runs (optional)
**Estimated Time**: 2-3 hours

---

### 8. Eligibility Checker
**Task**: Implement rules-based eligibility checking for partner offers  
**Output**: Function that evaluates user against offer criteria  
**Key Files**: 
- `backend/recommend/eligibility.py`
**Critical**: 
- **Credit score estimation**: Heuristic based on utilization, payment behavior, overdue status
  - Base: 750, penalties for high utilization (-100 for ≥80%), overdue (-80), min payment only (-30)
  - Clamp to 300-850 range
  - Document as "demo only, not accurate"
- **Eligibility checks**:
  - Min/max credit score
  - Min/max credit utilization
  - Min credit card balance (for balance transfer offers)
  - Min monthly income (estimate from payroll transactions)
  - Exclude if user already has account type (e.g., don't offer HYSA if they have one)
- Return: (eligible: bool, criteria_details: dict) for transparency
**Estimated Time**: 3-4 hours

---

### 9. Cross-Window Persona Handler
**Task**: Implement logic to determine target personas from 30d/180d assignments  
**Output**: Function that decides which persona(s) to target  
**Key Files**: 
- `backend/recommend/generator.py`
**Critical**: 
- Load persona assignments for both 30d and 180d windows
- If same persona both windows: target that persona only
- If different personas: target both, prioritize 30d (recent behavior) over 180d (long-term)
- If one window is STABLE and other is ASSIGNED: use the assigned persona
- If both windows are STABLE: route to stable user handler
- Return list of persona IDs ordered by priority [primary, secondary]
**Estimated Time**: 1-2 hours

---

### 10. Educational Rationale Generation (LLM)
**Task**: Generate personalized rationales for why educational content is relevant  
**Output**: LLM-powered rationale text citing user metrics  
**Key Files**: 
- `backend/recommend/generator.py`
**Critical**: 
- For each selected educational item, call LLM with:
  - User's key metrics (persona-specific features)
  - Content title and snippet
  - Persona name
- Use rationale prompt template
- Parse LLM response (expected: plain text, <100 words)
- If LLM fails: fall back to template rationale (e.g., "Based on your {persona_name} profile, this content may be helpful")
- Cite specific numbers (utilization %, balance amounts, days below $100, etc.)
**Estimated Time**: 2-3 hours

---

### 11. Actionable Item Generation (LLM)
**Task**: Generate 1-3 specific, measurable action steps for user  
**Output**: LLM-powered actionable items with rationales  
**Key Files**: 
- `backend/recommend/generator.py`
**Critical**: 
- Call LLM once with user metrics and persona to generate 1-3 actions
- Use actionable item prompt template
- Parse LLM response (expected: list of {text, rationale} objects)
- Each action must be:
  - Specific and measurable ("Pay $150 toward..." not "Pay more")
  - Cite user data in rationale
  - Achievable (small steps)
  - Empowering language
- If LLM fails: fall back to persona-specific template actions
- Store `data_cited` JSON with referenced metrics
- Mark as `generated_by='llm'`, `requires_review=true` (for Epic 5)
**Estimated Time**: 2-3 hours

---

### 12. Partner Offer Selection & Relevance
**Task**: Select eligible offers and generate relevance explanations  
**Output**: 0-2 partner offers with eligibility checks and LLM rationales  
**Key Files**: 
- `backend/recommend/generator.py`
**Critical**: 
- Load partner offers relevant to target personas
- For each offer, check eligibility using `eligibility.py`
- Keep only eligible offers
- Limit to max 2 offers
- For each eligible offer, generate relevance explanation with LLM:
  - Input: user metrics, persona, offer details
  - Output: <80 word "why_relevant" text
- Store eligibility_details JSON for transparency
- If LLM fails for relevance: use template ("This {product_type} may help with your {persona_focus}")
**Estimated Time**: 2-3 hours

---

### 13. Recommendation Package Assembly
**Task**: Orchestrate full recommendation generation workflow  
**Output**: Complete recommendation package per user  
**Key Files**: 
- `backend/recommend/generator.py` (main `generate_recommendation` function)
**Critical**: 
- **Workflow**:
  1. Load persona assignments (30d, 180d)
  2. Handle stable users (route to generic template)
  3. Determine target personas (cross-window logic)
  4. Load all features for user
  5. Select educational content (3-5 items)
  6. Generate educational rationales (LLM)
  7. Generate actionable items (LLM)
  8. Select and check partner offers (eligibility)
  9. Generate offer relevance (LLM)
  10. Assemble complete package
  11. Track generation metadata (timestamp, model, latency)
- Return structured JSON matching schema from technical design
- Handle errors at each step without crashing entire generation
**Estimated Time**: 3-4 hours

---

### 14. Stable User Handler
**Task**: Generate appropriate content for users with STABLE status  
**Output**: Minimal "you're doing well" content or generic template  
**Key Files**: 
- `backend/recommend/generator.py`
**Critical**: 
- Detect when both 30d and 180d assignments are STABLE
- Return simple recommendation package:
  - 1-2 educational items on financial optimization
  - 1 actionable item: "Keep up the great work, consider exploring {next_level_topic}"
  - 0 partner offers (no products needed)
- OR return generic stable template
- Decision: Confirm with user if stable users should get content at all (open question from requirements)
**Estimated Time**: 1-2 hours

---

### 15. Storage Operations
**Task**: Implement write operations for SQLite and Parquet  
**Output**: Functions to persist recommendations  
**Key Files**: 
- `backend/recommend/storage.py`
**Critical**: 
- **SQLite writes**:
  - Insert into `recommendations` table (parent record)
  - Insert into `recommendation_items` table (one row per educational/actionable/offer item)
  - Use transactions for atomicity
- **Parquet writes**:
  - Flatten recommendation data for analytics
  - Append to `data/features/recommendations.parquet`
  - Schema: user_id, recommendation_id, generated_at, personas, counts, latency
- Handle duplicate recommendations (upsert or skip?)
- Track generation metrics (latency, LLM calls, success/failure)
**Estimated Time**: 2-3 hours

---

### 16. Generation Script
**Task**: Create CLI script to generate recommendations for all users  
**Output**: Runnable script `scripts/generate_recommendations.py`  
**Key Files**: 
- `scripts/generate_recommendations.py`
**Critical**: 
- Load all users from SQLite
- Option to filter by consent status (generate for all, filter in Epic 5)
- Generate recommendations for each user
- Progress bar (e.g., using `tqdm`)
- Summary report: total generated, failures, average latency, LLM call count
- Configurable: `--user-id` for single user, `--as-of-date` for reproducible demos
- Handle errors gracefully (log and continue to next user)
**Estimated Time**: 2 hours

---

### 17. Unit Tests - Content Selection
**Task**: Test educational content selection logic  
**Output**: ≥2 unit tests  
**Key Files**: `backend/tests/test_recommendations.py`  
**Tests**:
1. Given Persona 1, select 5 items with persona_tag=1
2. Given cross-window personas [5, 1], select 3 items for P5 + 2 for P1
**Critical**: 
- Mock content catalog with known items
- Verify counts and persona relevance
**Estimated Time**: 1 hour

---

### 18. Unit Tests - Eligibility Checking
**Task**: Test partner offer eligibility rules  
**Output**: ≥3 unit tests  
**Key Files**: `backend/tests/test_recommendations.py`  
**Tests**:
1. User with 68% utilization passes balance transfer card eligibility
2. User with 92% utilization fails balance transfer card (too high)
3. User with no credit cards fails balance transfer card (no balance to transfer)
4. Credit score estimation: high utilization → score <700
**Critical**: 
- Mock feature data with specific values
- Verify eligibility pass/fail and criteria details
**Estimated Time**: 1-2 hours

---

### 19. Unit Tests - LLM Integration
**Task**: Test LLM client and fallback logic  
**Output**: ≥2 unit tests  
**Key Files**: `backend/tests/test_recommendations.py`  
**Tests**:
1. Mock LLM success: returns properly formatted rationale
2. Mock LLM timeout: falls back to template rationale
3. Mock LLM invalid JSON: sanitizes and logs warning
**Critical**: 
- Use mock LLM responses (no real API calls in tests)
- Verify fallback behavior
**Estimated Time**: 1-2 hours

---

### 20. Unit Tests - Cross-Window Logic
**Task**: Test persona targeting for different window scenarios  
**Output**: ≥2 unit tests  
**Key Files**: `backend/tests/test_recommendations.py`  
**Tests**:
1. Same persona both windows → target single persona
2. Different personas (30d=P5, 180d=P1) → target both [P5, P1]
3. One STABLE, one ASSIGNED → target assigned persona
4. Both STABLE → route to stable handler
**Critical**: 
- Mock persona assignments
- Verify target_personas list output
**Estimated Time**: 1 hour

---

### 21. Integration Test - Full Generation
**Task**: End-to-end recommendation generation for real user  
**Output**: ≥1 integration test  
**Key Files**: `backend/tests/test_recommendations.py`  
**Tests**:
1. Load persona assignment → generate recommendation → verify structure → store in SQLite + Parquet
**Critical**: 
- Use real Epic 3 persona assignments
- Use real Epic 2 features
- Mock LLM calls (no API costs)
- Verify all package components present (educational, actionable, offers)
- Verify storage success
**Estimated Time**: 2-3 hours

---

### 22. Integration Test - Batch Generation
**Task**: Generate recommendations for multiple users  
**Output**: ≥1 integration test  
**Key Files**: `backend/tests/test_recommendations.py`  
**Tests**:
1. Generate for 10 users with different personas, verify all succeed
**Critical**: 
- Mix of persona types
- Mock LLM
- Verify coverage (all users get recommendations)
- Verify no crashes on edge cases
**Estimated Time**: 1-2 hours

---

### 23. Manual Validation - Quality Review
**Task**: Manual review of generated recommendations for quality  
**Output**: Validation notes in decision log  
**Tests**:
- Generate recommendations for 5 sample users (one per persona)
- Review rationales: Do they cite actual user data? Is language empowering?
- Review actionable items: Are they specific and measurable?
- Review offer relevance: Does it make sense for persona?
- Note any issues with tone, accuracy, or relevance
**Estimated Time**: 1-2 hours

---

### 24. Configuration & Documentation
**Task**: Update config.json and document design decisions  
**Output**: Updated config, decision log entries  
**Key Files**: 
- `config.json`
- `docs/decision_log.md`
**Critical**: 
- Add `recommendations` section to config (content paths, LLM settings, selection rules)
- Add `llm` section (provider, model, API key env var, temperature, timeouts)
- Document in decision_log.md:
  - Hybrid content strategy rationale
  - Generic placeholder product approach
  - Credit score estimation method
  - Cross-window persona blending strategy
  - LLM fallback logic
**Estimated Time**: 1-2 hours

---

## Task Checklist

### Phase 1: Setup & Catalogs (Tasks 1-4)
- [ ] 1. Recommendation Module Setup
- [ ] 2. Educational Content Catalog
- [ ] 3. Partner Offer Catalog
- [ ] 4. Generic Template System

### Phase 2: LLM Integration (Tasks 5-6)
- [ ] 5. LLM Client Integration
- [ ] 6. Prompt Templates

### Phase 3: Core Logic (Tasks 7-9)
- [ ] 7. Content Selection Logic
- [ ] 8. Eligibility Checker
- [ ] 9. Cross-Window Persona Handler

### Phase 4: Generation Components (Tasks 10-14)
- [ ] 10. Educational Rationale Generation (LLM)
- [ ] 11. Actionable Item Generation (LLM)
- [ ] 12. Partner Offer Selection & Relevance
- [ ] 13. Recommendation Package Assembly
- [ ] 14. Stable User Handler

### Phase 5: Storage & CLI (Tasks 15-16)
- [ ] 15. Storage Operations
- [ ] 16. Generation Script

### Phase 6: Testing (Tasks 17-23)
- [ ] 17. Unit Tests - Content Selection
- [ ] 18. Unit Tests - Eligibility Checking
- [ ] 19. Unit Tests - LLM Integration
- [ ] 20. Unit Tests - Cross-Window Logic
- [ ] 21. Integration Test - Full Generation
- [ ] 22. Integration Test - Batch Generation
- [ ] 23. Manual Validation - Quality Review

### Phase 7: Documentation (Task 24)
- [ ] 24. Configuration & Documentation

---

## Dependencies

**Before Starting Epic 4**:
- ✅ Epic 3 complete: Persona assignments in SQLite and Parquet
- ✅ Epic 2 complete: Feature signals available for all users
- ✅ Epic 1 complete: Synthetic data with 75 users

**External Dependencies**:
- OpenAI API key (or other LLM provider)
- Python packages: `openai`, `pandas`, `sqlite3`

---

## Success Criteria

Epic 4 is **DONE** when:

**Functional Requirements**:
- [ ] Educational content catalog with ≥15 items created and loaded
- [ ] Partner offer catalog with ≥8 products created and loaded
- [ ] Generic templates for all 5 personas + stable created
- [ ] LLM generates rationales citing specific user data
- [ ] LLM generates actionable items that are specific and measurable
- [ ] Eligibility checker filters offers appropriately based on rules
- [ ] Cross-window persona handling works (different personas get blended content)
- [ ] All ASSIGNED users have generated recommendations
- [ ] Stable users have appropriate content
- [ ] Recommendations stored in both SQLite and Parquet

**Quality Requirements**:
- [ ] Manual review confirms rationales are empowering (no shaming language)
- [ ] Actionable items cite actual user data (card ending in XXXX, utilization %)
- [ ] LLM fallbacks work when API fails

**Testing Requirements**:
- [ ] ≥11 unit tests passing (content selection, eligibility, LLM, cross-window)
- [ ] ≥2 integration tests passing (full generation, batch)
- [ ] Manual validation completed for 5 sample users

**Documentation Requirements**:
- [ ] config.json updated with LLM settings
- [ ] Decision log updated with key design decisions
- [ ] Generation script runnable via `python scripts/generate_recommendations.py`

---

## Time Estimate

**Total Estimated Time**: 40-52 hours (5-7 days for one developer)

**Breakdown**:
- Setup & Catalogs: 9-13 hours
- LLM Integration: 5-7 hours
- Core Logic: 6-9 hours
- Generation Components: 10-13 hours
- Storage & CLI: 4-5 hours
- Testing: 7-11 hours
- Documentation: 1-2 hours

---

## Notes

- **LLM Costs**: Using gpt-4o-mini, ~75 users × 8 LLM calls per user × $0.0001 per call ≈ $0.06 per full generation run. Very affordable for demo.
- **Fallback Strategy**: Always have template-based fallbacks for LLM failures to ensure demo never crashes.
- **Epic 5 Handoff**: Epic 4 generates all recommendations; Epic 5 adds approval workflow and operator UI. Clean separation of concerns.
- **Stable Users**: Still TBD if they should appear in final product; implement generic template for now, easy to disable later.

---


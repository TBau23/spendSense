# Polish Epic: UI & Content Refinement - Task List

**Status**: Ready  
**Goal**: Reduce redundancy, enhance decision traces, improve content presentation  
**Est. Time**: 4-6 hours

---

## Backend Tasks

### Task 1: Add User Snapshot Generation
**File**: `backend/recommend/generator.py`

- [ ] Create `generate_user_snapshot()` function
  - [ ] Accept persona_context and features as input
  - [ ] Return dict with 3-5 persona-specific metrics
  - [ ] Implement metric selection for Persona 1 (High Utilization)
  - [ ] Implement metric selection for Persona 2 (Variable Income)
  - [ ] Implement metric selection for Persona 3 (Subscription-Heavy)
  - [ ] Implement metric selection for Persona 4 (Savings Builder)
  - [ ] Implement metric selection for Persona 5 (Cash Flow Stressed)

- [ ] Integrate snapshot generation into `generate_recommendation()`
  - [ ] Call after persona context loaded
  - [ ] Store in recommendation dict as `user_snapshot` field
  - [ ] Ensure it's saved to database

**Acceptance**: Recommendations contain persona-specific snapshot with 3-5 metrics

---

### Task 2: Remove "Why" Generation from Educational Content
**File**: `backend/recommend/generator.py`

- [ ] Locate `generate_educational_rationales()` function call
- [ ] Comment out or remove the function call
- [ ] Verify educational items no longer have `why` or `rationale` field
- [ ] Update any downstream code that expects these fields

**File**: `backend/recommend/llm_client.py` (if needed)
- [ ] Remove or disable `generate_rationale()` calls

**Acceptance**: Educational content items contain only title and content, no "why"

---

### Task 3: Enhance Decision Traces with Criteria Details
**File**: `backend/recommend/traces.py`

- [ ] Create `get_threshold_for_criterion()` helper function
  - [ ] Map criterion names to human-readable thresholds
  - [ ] Example: "utilization_high" → "Utilization ≥50%"

- [ ] Update `generate_persona_trace()` function
  - [ ] Parse `criteria_met` dict to extract matched criteria
  - [ ] Look up actual values from `feature_values_cited`
  - [ ] Build structured criteria list with threshold + actual value
  - [ ] Replace simple string rationale with structured dict
  - [ ] Format: `{'summary': '...', 'criteria_details': [...]}`

- [ ] Test with multiple personas to verify correct criteria display

**Acceptance**: Decision traces contain list of criteria with thresholds and actual values

---

## Frontend Tasks

### Task 4: Create UserSnapshot Component
**New File**: `frontend/src/components/UserSnapshot.jsx`

- [ ] Create functional component accepting `snapshot` prop
- [ ] Render snapshot.metrics as list
- [ ] Display label, value, and optional detail for each metric
- [ ] Add appropriate styling (card layout)

**File**: `frontend/src/components/UserSnapshot.css` (or inline styles)
- [ ] Style as card with subtle border/background
- [ ] Metrics displayed clearly with good spacing
- [ ] Responsive design

**File**: `frontend/src/components/RecommendationCard.jsx`
- [ ] Import UserSnapshot component
- [ ] Add at top of recommendation content section
- [ ] Pass `recommendation.user_snapshot` as prop

**Acceptance**: User snapshot card displays at top of recommendations with clean styling

---

### Task 5: Remove "Why" Rendering from UI
**File**: `frontend/src/components/RecommendationCard.jsx`

- [ ] Locate rendering of educational content items
- [ ] Remove any display of `item.why`, `item.rationale`, or similar
- [ ] Ensure only title and content are displayed
- [ ] Remove related CSS classes if no longer needed

**File**: `frontend/src/App.css` or component styles
- [ ] Clean up unused "why" or "rationale" CSS classes

**Acceptance**: Educational content displays only title and content, no "why" sections

---

### Task 6: Enhance DecisionTrace Component
**File**: `frontend/src/components/DecisionTrace.jsx`

- [ ] Update `renderPersonaTrace()` function
  - [ ] Check if `content.rationale.criteria_details` exists
  - [ ] If yes, render as formatted checklist:
    - [ ] Show "Criteria Met:" header
    - [ ] Map over criteria_details array
    - [ ] Display: "✓ {criterion}: {threshold} (Actual: {actual})"
  - [ ] Keep existing collapsible feature values section

- [ ] Add CSS styling for criteria checklist
  - [ ] Checkmark icon/character
  - [ ] Indented list format
  - [ ] Clear visual hierarchy

**Acceptance**: Decision traces show detailed criteria with actual values in clean format

---

### Task 7: Update User Detail Header to Show Name
**File**: `frontend/src/pages/UserDetailView.jsx`

- [ ] Fetch user's full name from user data
- [ ] Update page header format from "User: user_bdd640fb" to "Crystal Robinson (***640fb)"
  - [ ] Display full name
  - [ ] Show last 5 characters of user_id with *** prefix in parentheses
- [ ] Ensure consistent styling with operator dashboard

**File**: `backend/api/operator.py` (if needed)
- [ ] Verify user endpoint returns full name
- [ ] Add name field to response if not present

**Acceptance**: User detail page shows "Name (***id_suffix)" format instead of raw user_id

---

## Testing & Validation

### Task 8: Regenerate Test Recommendations
- [ ] Select 3 test users from different personas
  - [ ] User with Persona 1 (High Utilization)
  - [ ] User with Persona 3 (Subscription-Heavy)
  - [ ] User with Persona 4 or 5

- [ ] Regenerate recommendations for each:
  ```bash
  python scripts/generate_recommendations.py --user-id <user_id>
  ```

- [ ] Verify for each:
  - [ ] User snapshot appears with correct persona-specific metrics
  - [ ] Educational content has no "Why" sections
  - [ ] Decision traces show criteria details with values

**Acceptance**: All test users show improved content presentation

---

### Task 9: Visual Polish & Responsiveness
- [ ] Review overall layout on desktop
  - [ ] Proper spacing between sections
  - [ ] Snapshot card is visually distinct but not overwhelming
  - [ ] Decision traces are scannable

- [ ] Test on mobile/tablet viewport
  - [ ] Snapshot metrics stack appropriately
  - [ ] Text remains readable
  - [ ] No horizontal overflow

- [ ] Compare before/after screen space usage
  - [ ] Measure scroll height reduction
  - [ ] Aim for 40-60% reduction

**Acceptance**: Layout is clean, responsive, and uses significantly less space

---

## Definition of Done

- [x] Bug fix: Persona IDs display as names in decision traces ✓
- [ ] User snapshot component created and integrated
- [ ] Educational content "Why" sections removed
- [ ] Decision traces show criteria with actual values
- [ ] User detail page shows "Name (***id)" format instead of raw user_id
- [ ] Test recommendations regenerated and verified
- [ ] Visual polish complete
- [ ] No linter errors
- [ ] Screen space reduced by 40-60%

---

## Notes

- Start with backend changes (Tasks 1-4) before frontend
- Test incrementally with single user regenerations
- Keep original recommendation structure intact (backwards compatible)
- Can be implemented incrementally (one task at a time)


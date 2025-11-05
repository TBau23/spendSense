# Epic 5: Guardrails & Operator View - Task List

**Status**: Ready for Implementation  
**Epic Goal**: Consent enforcement + operator dashboard for review/approval  
**Dependencies**: Epic 4 complete (Recommendations generated)

---

## Phase 1: Database Schema Updates

### Task 1.1: Add Status Fields to Recommendations Table
- [ ] Write migration script to add columns:
  - `status TEXT DEFAULT 'PENDING_REVIEW'`
  - `reviewed_at TIMESTAMP NULL`
  - `reviewer_notes TEXT NULL`
- [ ] Run migration on existing database
- [ ] Update `backend/storage/schemas.py` to reflect new fields
- [ ] Verify existing recommendations default to PENDING_REVIEW

**Estimated Time**: 30 minutes

---

### Task 1.2: Create Decision Traces Table
- [ ] Create `decision_traces` table in SQLite:
  ```sql
  CREATE TABLE decision_traces (
      trace_id TEXT PRIMARY KEY,
      user_id TEXT NOT NULL,
      recommendation_id TEXT,
      trace_type TEXT NOT NULL,
      trace_content TEXT NOT NULL,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES users(user_id),
      FOREIGN KEY (recommendation_id) REFERENCES recommendations(recommendation_id)
  );
  ```
- [ ] Create indexes on `user_id` and `recommendation_id`
- [ ] Update schema documentation

**Estimated Time**: 20 minutes

---

## Phase 2: Backend - Guardrails Module

### Task 2.1: Consent Enforcement Utilities
- [ ] Create `backend/guardrails/consent.py`
- [ ] Implement `check_consent(user_id) -> bool`
- [ ] Implement `get_consented_users() -> List[dict]`
- [ ] Implement `ConsentError` exception class
- [ ] Add logging for consent checks

**Estimated Time**: 30 minutes

---

### Task 2.2: Metrics Computation
- [ ] Create `backend/guardrails/metrics.py`
- [ ] Implement `compute_operator_metrics()` for aggregate metrics:
  - Total consented users
  - Pending/approved/flagged counts
  - Approval rate
  - Coverage percentage
- [ ] Implement `get_user_metrics(user_id)` for per-user metrics:
  - Persona assignments (30d/180d)
  - Account counts
  - Recommendation counts by status
- [ ] Add caching logic (60-second TTL for aggregate metrics)

**Estimated Time**: 1 hour

---

### Task 2.3: Recommendation Status Management
- [ ] Create `backend/recommend/approval.py`
- [ ] Implement `approve_recommendation(rec_id, reviewer_notes)`
- [ ] Implement `flag_recommendation(rec_id, reviewer_notes)` (notes required)
- [ ] Implement `get_recommendations_by_status(status) -> List[dict]`
- [ ] Implement `get_user_recommendations(user_id, status=None) -> List[dict]`
- [ ] Add timestamp tracking for reviewed_at

**Estimated Time**: 45 minutes

---

### Task 2.4: Decision Trace Generation
- [ ] Create `backend/recommend/traces.py`
- [ ] Implement `generate_persona_trace(user_id, recommendation)`:
  - Extract persona assignment rationale
  - Cite feature values used
  - Store criteria met
- [ ] Implement `generate_content_trace(recommendation)`:
  - Explain why educational items selected
  - Show eligibility check results for offers
- [ ] Implement `store_traces(user_id, traces)`
- [ ] Update `backend/recommend/generator.py` to call trace generation
- [ ] Implement `get_traces(user_id, recommendation_id=None) -> List[dict]`

**Estimated Time**: 1.5 hours

---

## Phase 3: Backend - FastAPI Endpoints

### Task 3.1: FastAPI Setup
- [ ] Create `backend/api/__init__.py`
- [ ] Create `backend/api/main.py` with FastAPI app initialization
- [ ] Configure CORS for frontend (localhost:5173)
- [ ] Set up error handlers (404, 403, 500)
- [ ] Add health check endpoint: `GET /api/health`

**Estimated Time**: 30 minutes

---

### Task 3.2: Operator User Endpoints
- [ ] Create `backend/api/operator.py`
- [ ] Implement `GET /api/operator/users`:
  - Query params: persona, status, sort
  - Filter for consented users only
  - Return: user_id, name, persona, has_pending_recs, rec_count, last_rec_date
- [ ] Implement `GET /api/operator/users/{user_id}`:
  - Check consent, return 403 if not consented
  - Return: full user profile with features and personas
- [ ] Implement `GET /api/operator/users/{user_id}/recommendations`:
  - Return all recommendations (all statuses)

**Estimated Time**: 1.5 hours

---

### Task 3.3: Operator Recommendation Endpoints
- [ ] Implement `GET /api/operator/recommendations/{rec_id}`:
  - Return full recommendation package with items
- [ ] Implement `POST /api/operator/recommendations/{rec_id}/approve`:
  - Body: `{ "reviewer_notes": "optional" }`
  - Call approval.py function
  - Return updated recommendation
- [ ] Implement `POST /api/operator/recommendations/{rec_id}/flag`:
  - Body: `{ "reviewer_notes": "required" }`
  - Validate notes present
  - Call approval.py function
  - Return updated recommendation

**Estimated Time**: 1 hour

---

### Task 3.4: Traces and Metrics Endpoints
- [ ] Implement `GET /api/operator/traces/{user_id}`:
  - Optional query param: recommendation_id
  - Return decision traces as JSON
- [ ] Implement `GET /api/operator/metrics`:
  - Return cached aggregate metrics
  - Cache TTL: 60 seconds
- [ ] Add Pydantic models for request/response validation

**Estimated Time**: 45 minutes

---

## Phase 4: Frontend - Setup & API Client

### Task 4.1: Frontend Dependencies & Routing
- [ ] Verify React Router installed (`npm install react-router-dom`)
- [ ] Update `frontend/src/main.jsx` to include Router:
  ```jsx
  <BrowserRouter>
    <App />
  </BrowserRouter>
  ```
- [ ] Create route structure in `App.jsx`:
  - `/operator` → OperatorDashboard
  - `/operator/users/:userId` → UserDetailView

**Estimated Time**: 20 minutes

---

### Task 4.2: API Client
- [ ] Create `frontend/src/api/operator.js`
- [ ] Implement API functions:
  - `fetchUsers(filters)`
  - `fetchUserDetail(userId)`
  - `fetchUserRecommendations(userId)`
  - `fetchRecommendation(recId)`
  - `approveRecommendation(recId, notes)`
  - `flagRecommendation(recId, notes)`
  - `fetchTraces(userId, recId)`
  - `fetchMetrics()`
- [ ] Add error handling and response parsing
- [ ] Configure base URL from environment variable

**Estimated Time**: 1 hour

---

## Phase 5: Frontend - Operator Dashboard (Main Page)

### Task 5.1: MetricsPanel Component
- [ ] Create `frontend/src/components/MetricsPanel.jsx`
- [ ] Display aggregate metrics in card layout:
  - Total consented users
  - Pending recommendations count
  - Approval rate
  - Coverage percentage
- [ ] Style with Tailwind CSS (grid layout, cards with borders)

**Estimated Time**: 45 minutes

---

### Task 5.2: UserList Component
- [ ] Create `frontend/src/components/UserList.jsx`
- [ ] Implement table with columns:
  - Name
  - User ID (masked)
  - Primary Persona
  - Status badge (pending/approved/flagged)
  - Recommendation count
  - Last activity date
  - View Details button
- [ ] Implement filter bar with dropdowns:
  - Persona filter
  - Status filter
  - Sort order
- [ ] Add visual indicators for pending recommendations (badge/icon)
- [ ] Implement click to navigate to user detail

**Estimated Time**: 2 hours

---

### Task 5.3: OperatorDashboard Page
- [ ] Create `frontend/src/pages/OperatorDashboard.jsx`
- [ ] Compose MetricsPanel + UserList
- [ ] Add header: "SpendSense Operator View"
- [ ] Implement data fetching on mount
- [ ] Handle loading and error states
- [ ] Apply responsive layout

**Estimated Time**: 1 hour

---

## Phase 6: Frontend - User Detail View

### Task 6.1: UserMetrics Component
- [ ] Create `frontend/src/components/UserMetrics.jsx`
- [ ] Display persona assignments (30d & 180d windows)
- [ ] Display key feature metrics:
  - Credit utilization
  - Savings rate
  - Cash flow status
- [ ] Display account summary (checking, savings, credit card counts)
- [ ] Style as sidebar panel

**Estimated Time**: 1 hour

---

### Task 6.2: RecommendationCard Component
- [ ] Create `frontend/src/components/RecommendationCard.jsx`
- [ ] Implement collapsible card with:
  - Status badge (color-coded)
  - Generated date
  - Educational items list with rationales
  - Actionable items list with data citations
  - Partner offers with eligibility details
- [ ] Create nested `RecommendationItem.jsx` for individual items
- [ ] Add expand/collapse functionality

**Estimated Time**: 2 hours

---

### Task 6.3: DecisionTrace Component
- [ ] Create `frontend/src/components/DecisionTrace.jsx`
- [ ] Implement expandable sections:
  - "Why was this persona assigned?"
  - "Why was this content selected?"
- [ ] Display feature values cited
- [ ] Display eligibility check results
- [ ] Style with JSON tree viewer or accordion

**Estimated Time**: 1 hour

---

### Task 6.4: ApprovalActions Component
- [ ] Create `frontend/src/components/ApprovalActions.jsx`
- [ ] Implement Approve button (green, primary action)
- [ ] Implement Flag button (red, requires confirmation modal)
- [ ] Create confirmation modal for Flag action with notes textarea
- [ ] Add Override button (grayed out, disabled, tooltip "Coming Soon")
- [ ] Show success/error messages after actions
- [ ] Refresh recommendation after action

**Estimated Time**: 1.5 hours

---

### Task 6.5: UserDetailView Page
- [ ] Create `frontend/src/pages/UserDetailView.jsx`
- [ ] Implement 3-column layout:
  - Left (30%): UserMetrics
  - Center (50%): RecommendationCard list
  - Right (20%): DecisionTrace
- [ ] Add breadcrumb navigation: "Operator → User {name}"
- [ ] Fetch user data, recommendations, and traces on mount
- [ ] Handle loading and error states
- [ ] Make responsive (stack columns on mobile)

**Estimated Time**: 1.5 hours

---

## Phase 7: Integration & Testing

### Task 7.1: Backend Unit Tests
- [ ] Create `backend/tests/test_guardrails.py`
- [ ] Test consent filtering: `get_consented_users()` excludes non-consented
- [ ] Test approve action: Status updates to APPROVED
- [ ] Test flag action: Status updates to FLAGGED, notes required
- [ ] Test metrics computation: Aggregate counts correct
- [ ] Test decision trace generation: Traces stored correctly
- [ ] Test API consent check: Returns 403 for non-consented users

**Estimated Time**: 2 hours

---

### Task 7.2: Backend Integration Testing
- [ ] Run FastAPI server: `uvicorn backend.api.main:app --reload`
- [ ] Test all operator endpoints with curl/Postman
- [ ] Verify CORS headers allow frontend origin
- [ ] Test error handling (404, 403, 500)
- [ ] Verify recommendation status transitions work
- [ ] Verify metrics cache works

**Estimated Time**: 1 hour

---

### Task 7.3: Frontend Integration Testing
- [ ] Run frontend dev server: `npm run dev`
- [ ] Test main dashboard:
  - Metrics panel displays correct counts
  - User list loads and displays users
  - Filtering works (persona, status, sort)
  - Visual indicators show for pending recommendations
  - Navigation to user detail works
- [ ] Test user detail view:
  - User metrics load correctly
  - Recommendations display with items
  - Decision traces display
  - Approve action updates status
  - Flag action requires notes and updates status
  - Override button is disabled
- [ ] Test edge cases:
  - User with no recommendations
  - User with only flagged recommendations
  - Non-consented user (should 403)

**Estimated Time**: 2 hours

---

### Task 7.4: End-to-End Workflow Test
- [ ] Generate recommendations for test users (Epic 4 script)
- [ ] Open operator dashboard, verify pending count
- [ ] Click into user with pending recommendation
- [ ] Review recommendation content
- [ ] View decision traces
- [ ] Approve recommendation
- [ ] Verify status updated in database
- [ ] Verify metrics updated on dashboard
- [ ] Test flag workflow with notes

**Estimated Time**: 1 hour

---

## Phase 8: Documentation & Polish

### Task 8.1: Update Decision Log
- [ ] Document consent enforcement approach
- [ ] Document status workflow design
- [ ] Document override placeholder rationale
- [ ] Document frontend architecture choices
- [ ] Document any challenges encountered

**Estimated Time**: 30 minutes

---

### Task 8.2: Update README
- [ ] Add instructions for running FastAPI server
- [ ] Add instructions for running frontend dev server
- [ ] Document operator dashboard access URL
- [ ] Update environment variable requirements

**Estimated Time**: 20 minutes

---

### Task 8.3: Code Cleanup
- [ ] Remove any debug console.logs
- [ ] Format code with prettier (frontend) and black (backend)
- [ ] Add docstrings to all new backend functions
- [ ] Add comments for override placeholder
- [ ] Verify all imports are used

**Estimated Time**: 30 minutes

---

## Task Summary

**Total Tasks**: 33  
**Estimated Total Time**: ~25 hours

**Critical Path**:
1. Schema updates (Phase 1)
2. Backend guardrails & API (Phases 2-3)
3. Frontend dashboard (Phases 4-6)
4. Testing (Phase 7)

**Quick Start**: Complete Phase 1 first (schema updates) to unblock all other work.

---

## Success Checklist

- [ ] Status field added to recommendations table
- [ ] Decision traces table created and populated
- [ ] Consent enforcement working (non-consented users filtered)
- [ ] 8 FastAPI endpoints operational
- [ ] Operator dashboard renders with metrics and user list
- [ ] User detail page shows recommendations, traces, and actions
- [ ] Approve/flag actions update database and UI
- [ ] Override placeholder visible (grayed out)
- [ ] ≥6 backend tests passing
- [ ] Manual frontend testing complete
- [ ] Documentation updated

---


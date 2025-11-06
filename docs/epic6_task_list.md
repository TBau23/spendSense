# Epic 6: Consent Management & End User Experience - Task List

**Status**: Ready for Implementation  
**Epic Goal**: Enable consent workflows + end user portal + operator enhancements for demo  
**Dependencies**: Epic 5 complete

---

## Phase 1: Backend - Consent & Recommendation Management

### Task 1.1: Extend Consent Module
**File**: `backend/guardrails/consent.py`

- [ ] Add `grant_consent(user_id: str)` function
  - [ ] Update `users.consent = true` in database
  - [ ] Return success status
- [ ] Add `revoke_consent(user_id: str)` function
  - [ ] Update `users.consent = false` in database
  - [ ] Soft delete all user recommendations (status = 'DELETED')
  - [ ] Return success status
- [ ] Add logging for consent changes

**Estimated Time**: 30 minutes

---

### Task 1.2: Create Recommendation Management Module
**New File**: `backend/recommend/management.py`

- [ ] Implement `generate_recommendation_for_user(user_id: str) -> dict`
  - [ ] Call existing `generator.generate_recommendation()`
  - [ ] Ensure recommendation has status = 'PENDING_REVIEW'
  - [ ] Store in database
  - [ ] Return recommendation dict
- [ ] Implement `soft_delete_recommendation(rec_id: str) -> bool`
  - [ ] Update recommendation status to 'DELETED'
  - [ ] Add timestamp for deletion
  - [ ] Return success status
- [ ] Add error handling for invalid user_id or rec_id

**Estimated Time**: 45 minutes

---

### Task 1.3: Update Query Filters for Soft Delete
**Files**: `backend/api/operator.py`, `backend/guardrails/metrics.py`, `backend/recommend/storage.py`

- [ ] Update all recommendation queries to filter `status != 'DELETED'`
  - [ ] `get_user_recommendations()` 
  - [ ] `get_recommendations_by_status()`
  - [ ] `compute_operator_metrics()`
  - [ ] Any other functions that query recommendations table
- [ ] Test that DELETED recommendations don't appear in results

**Estimated Time**: 30 minutes

---

### Task 1.4: Add Consent Management Endpoints
**File**: `backend/api/operator.py` (or new `backend/api/consent.py`)

- [ ] Implement `POST /api/consent/grant`
  - [ ] Body: `{ "user_id": "..." }`
  - [ ] Call `grant_consent()`
  - [ ] Trigger `generate_recommendation_for_user()` in background
  - [ ] Return 202 Accepted
- [ ] Implement `POST /api/consent/revoke`
  - [ ] Body: `{ "user_id": "..." }`
  - [ ] Call `revoke_consent()`
  - [ ] Return 200 OK
- [ ] Add request validation (user_id required)

**Estimated Time**: 45 minutes

---

### Task 1.5: Add Recommendation Management Endpoints
**File**: `backend/api/operator.py`

- [ ] Implement `POST /api/operator/users/{user_id}/generate`
  - [ ] Call `generate_recommendation_for_user()`
  - [ ] Return created recommendation
  - [ ] Return 201 Created
- [ ] Implement `DELETE /api/operator/recommendations/{rec_id}`
  - [ ] Call `soft_delete_recommendation()`
  - [ ] Return 204 No Content
- [ ] Add error handling (user not found, rec not found)

**Estimated Time**: 30 minutes

---

### Task 1.6: Update Operator User List Endpoint
**File**: `backend/api/operator.py`

- [ ] Modify `GET /api/operator/users` to return ALL users (remove consent filter)
- [ ] Add `consent` field to response
- [ ] Add `has_approved_recs` boolean to response
- [ ] Test that non-consented users appear in list

**Estimated Time**: 20 minutes

---

## Phase 2: Backend - End User API

### Task 2.1: Create User API Module
**New File**: `backend/api/user.py`

- [ ] Implement `GET /api/users`
  - [ ] Return all users with: user_id, full_name, consent, has_approved_recs
  - [ ] Order by name
- [ ] Implement `GET /api/users/{user_id}`
  - [ ] Return user info: user_id, full_name, consent
  - [ ] No sensitive data (public endpoint)
- [ ] Implement `GET /api/users/{user_id}/recommendations`
  - [ ] Return APPROVED recommendations only
  - [ ] Include user_snapshot and all items
  - [ ] Return empty array if none
- [ ] Register routes in `backend/api/main.py`

**Estimated Time**: 1 hour

---

### Task 2.2: Create User Insights Endpoint
**File**: `backend/api/user.py`

- [ ] Implement `GET /api/users/{user_id}/insights`
  - [ ] Query transactions table for last 30 days
  - [ ] Aggregate by merchant (top 5 by spend)
  - [ ] Aggregate by category (top 5 by spend)
  - [ ] Calculate total spend
  - [ ] Return structured JSON
- [ ] Add caching if needed (optional)
- [ ] Test with sample user data

**Estimated Time**: 1 hour

---

## Phase 3: Frontend - Operator Enhancements

### Task 3.1: Show Non-Consented Users in List
**File**: `frontend/src/api/operator.js`

- [ ] Update `fetchUsers()` to not filter by consent on frontend
  - [ ] Backend now returns all users

**File**: `frontend/src/components/UserList.jsx`

- [ ] Add visual styling for non-consented users:
  - [ ] Gray out row (reduce opacity)
  - [ ] Add badge "Consent Required" (red/orange)
- [ ] Disable "View Details" button for non-consented users
  - [ ] Show disabled state
  - [ ] Add tooltip: "User has not granted consent"
- [ ] Update CSS for new styles

**Estimated Time**: 1 hour

---

### Task 3.2: Add Generate Recommendation Button
**File**: `frontend/src/api/operator.js`

- [ ] Add `generateRecommendation(userId)` function
  - [ ] POST to `/api/operator/users/{userId}/generate`
  - [ ] Return new recommendation

**File**: `frontend/src/pages/UserDetailView.jsx`

- [ ] Add "Generate New Recommendation" button near page header
  - [ ] Primary button styling
  - [ ] Disable if already generating (loading state)
- [ ] Implement click handler:
  - [ ] Call `generateRecommendation()`
  - [ ] Show loading spinner
  - [ ] On success: refresh recommendations list
  - [ ] On error: show error message
- [ ] Add success toast/notification

**Estimated Time**: 1 hour

---

### Task 3.3: Add Delete Recommendation Action
**File**: `frontend/src/api/operator.js`

- [ ] Add `deleteRecommendation(recId)` function
  - [ ] DELETE to `/api/operator/recommendations/{recId}`

**File**: `frontend/src/components/RecommendationCard.jsx`

- [ ] Add delete button to card header (icon button, trash can)
- [ ] Implement confirmation modal:
  - [ ] "Are you sure you want to delete this recommendation?"
  - [ ] Confirm / Cancel buttons
- [ ] Implement delete handler:
  - [ ] Call `deleteRecommendation()`
  - [ ] On success: remove card from view (or refresh parent)
  - [ ] On error: show error message
- [ ] Style delete button (subtle, secondary action)

**Estimated Time**: 1.5 hours

---

## Phase 4: Frontend - End User Portal

### Task 4.1: Create User API Client
**New File**: `frontend/src/api/user.js`

- [ ] Implement `fetchAllUsers()` - GET /api/users
- [ ] Implement `fetchUser(userId)` - GET /api/users/{userId}
- [ ] Implement `fetchUserRecommendations(userId)` - GET /api/users/{userId}/recommendations
- [ ] Implement `fetchUserInsights(userId)` - GET /api/users/{userId}/insights
- [ ] Implement `grantConsent(userId)` - POST /api/consent/grant
- [ ] Implement `revokeConsent(userId)` - POST /api/consent/revoke
- [ ] Add error handling for all functions

**Estimated Time**: 45 minutes

---

### Task 4.2: Create User Landing Page
**New File**: `frontend/src/pages/UserLanding.jsx`

- [ ] Create component with centered layout
- [ ] Add SpendSense branding/logo
- [ ] Implement user selection dropdown:
  - [ ] Fetch all users on mount
  - [ ] Display as "Name (***id_suffix)"
  - [ ] Order by name
- [ ] On selection, navigate to `/user/{userId}`
- [ ] Add basic styling (centered card layout)
- [ ] Handle loading and error states

**Estimated Time**: 1 hour

---

### Task 4.3: Create User Insights Component
**New File**: `frontend/src/components/UserInsights.jsx`

- [ ] Accept `insights` prop
- [ ] Display top merchants section:
  - [ ] List top 5 merchants with spend amounts
  - [ ] Bar chart or simple list
- [ ] Display spending by category section:
  - [ ] Top 5 categories with percentages
  - [ ] Bar representation or pie chart (simple)
- [ ] Display total spend (30 days)
- [ ] Card-based layout with clear sections
- [ ] Style with Tailwind CSS

**Estimated Time**: 1.5 hours

---

### Task 4.4: Create User Recommendation Card
**New File**: `frontend/src/components/UserRecommendationCard.jsx`

- [ ] Simplified version of operator's RecommendationCard
- [ ] Display user_snapshot (if present)
  - [ ] Reuse or adapt UserSnapshot component from polish epic
- [ ] Display educational items:
  - [ ] Title + content only
  - [ ] No "why" sections
- [ ] Display actionable items:
  - [ ] Title + because + action
- [ ] Display partner offers:
  - [ ] Offer details with eligibility context
- [ ] NO status badges, NO decision traces, NO approval actions
- [ ] Clean, user-friendly styling

**Estimated Time**: 1.5 hours

---

### Task 4.5: Create Consent Toggle Component
**New File**: `frontend/src/components/ConsentToggle.jsx`

- [ ] Accept `userId`, `currentConsent`, `onConsentChange` props
- [ ] If consent = false:
  - [ ] Show "Grant Consent" button (primary, green)
  - [ ] Explain briefly what they'll get
- [ ] If consent = true:
  - [ ] Show "Revoke Consent" button (secondary, red)
- [ ] Implement grant handler:
  - [ ] Call `grantConsent(userId)`
  - [ ] Show loading state
  - [ ] On success: call `onConsentChange()`
- [ ] Implement revoke handler:
  - [ ] Show confirmation modal
  - [ ] "Are you sure? This will remove your recommendations."
  - [ ] Call `revokeConsent(userId)`
  - [ ] On success: call `onConsentChange()`
- [ ] Style buttons clearly with colors

**Estimated Time**: 1 hour

---

### Task 4.6: Create User Portal Page
**New File**: `frontend/src/pages/UserPortal.jsx`

- [ ] Fetch user data, recommendations, and insights on mount
- [ ] Determine state based on consent + recommendations:
  - [ ] State A: Non-consented → Show grant consent view
  - [ ] State B: Consented, no approved recs → Show "check back soon"
  - [ ] State C: Consented, has approved recs → Show full portal
- [ ] Implement State A layout:
  - [ ] Welcome message
  - [ ] Brief explanation
  - [ ] Grant consent button (ConsentToggle)
- [ ] Implement State B layout:
  - [ ] Welcome message
  - [ ] "Your recommendations are being prepared"
  - [ ] Revoke consent button (ConsentToggle)
- [ ] Implement State C layout:
  - [ ] Welcome message with user name
  - [ ] UserInsights component
  - [ ] List of UserRecommendationCard components
  - [ ] Revoke consent button at bottom (ConsentToggle)
- [ ] Handle loading and error states
- [ ] Make responsive (mobile-friendly)

**Estimated Time**: 2 hours

---

### Task 4.7: Update App Routing
**File**: `frontend/src/App.jsx`

- [ ] Import new pages: UserLanding, UserPortal
- [ ] Add routes:
  - [ ] `/user` → UserLanding
  - [ ] `/user/:userId` → UserPortal
  - [ ] `/` → Navigate to `/user` (or home page)
- [ ] Ensure existing operator routes still work
- [ ] Test navigation between all routes

**Estimated Time**: 20 minutes

---

## Phase 5: Integration & Testing

### Task 5.1: Backend Unit Tests
**File**: `backend/tests/test_consent.py` (new) or extend existing

- [ ] Test `grant_consent()` updates database correctly
- [ ] Test `revoke_consent()` soft deletes recommendations
- [ ] Test `generate_recommendation_for_user()` creates PENDING_REVIEW rec
- [ ] Test `soft_delete_recommendation()` updates status
- [ ] Test recommendation queries filter DELETED status
- [ ] Test user insights endpoint returns correct aggregations

**Estimated Time**: 1.5 hours

---

### Task 5.2: Backend Integration Testing

- [ ] Start FastAPI server
- [ ] Test consent grant endpoint → verify rec generation triggered
- [ ] Test consent revoke endpoint → verify recs marked DELETED
- [ ] Test generate recommendation endpoint → verify new rec created
- [ ] Test delete recommendation endpoint → verify soft delete
- [ ] Test user endpoints return correct data
- [ ] Test insights endpoint with sample user
- [ ] Verify operator endpoints still work with query filters

**Estimated Time**: 1 hour

---

### Task 5.3: Frontend Integration Testing - Operator

- [ ] Test non-consented users appear in list:
  - [ ] Grayed out correctly
  - [ ] Badge shows "Consent Required"
  - [ ] View Details button disabled
- [ ] Test generate recommendation button:
  - [ ] Button appears on user detail page
  - [ ] Clicking triggers generation
  - [ ] Loading state shows
  - [ ] New rec appears in list
- [ ] Test delete recommendation button:
  - [ ] Button appears on rec card
  - [ ] Confirmation modal shows
  - [ ] Deleting removes rec from view
- [ ] Test with different user states

**Estimated Time**: 1 hour

---

### Task 5.4: Frontend Integration Testing - End User

- [ ] Test user landing page:
  - [ ] Dropdown loads all users
  - [ ] Selection navigates to user portal
- [ ] Test user portal State A (non-consented):
  - [ ] Shows grant consent view
  - [ ] Grant consent button works
  - [ ] Transitions to State B after granting
- [ ] Test user portal State B (waiting for recs):
  - [ ] Shows "check back soon" message
  - [ ] Revoke consent button works
  - [ ] Transitions to State A after revoking
- [ ] Test user portal State C (has recs):
  - [ ] Insights display correctly
  - [ ] Recommendations display correctly
  - [ ] Revoke consent prompts confirmation
  - [ ] Transitions to State A after revoking
- [ ] Test navigation between users (dropdown to portal back to dropdown)

**Estimated Time**: 1.5 hours

---

### Task 5.5: End-to-End Demo Flow Testing

- [ ] Demo Scenario 1: Operator reviews and approves rec for consented user
  - [ ] User in State B sees recs after approval
- [ ] Demo Scenario 2: Non-consented user grants consent
  - [ ] Appears in operator view
  - [ ] Operator can generate rec
  - [ ] User eventually sees approved rec
- [ ] Demo Scenario 3: Consented user revokes consent
  - [ ] Recs disappear from user view
  - [ ] Operator sees user as non-consented
  - [ ] User can re-grant consent
- [ ] Demo Scenario 4: Operator flags rec, generates new one
  - [ ] Delete old rec
  - [ ] Generate new rec
  - [ ] Approve new rec
  - [ ] User sees new rec

**Estimated Time**: 1.5 hours

---

## Phase 6: Documentation & Polish

### Task 6.1: Update Decision Log
**File**: `docs/decision_log.md`

- [ ] Document soft delete implementation choice
- [ ] Document async rec generation on consent grant
- [ ] Document no localStorage persistence choice
- [ ] Document separate user portal route structure
- [ ] Document any challenges encountered

**Estimated Time**: 30 minutes

---

### Task 6.2: Update README
**File**: `README.md`

- [ ] Add instructions for accessing end user portal (`/user`)
- [ ] Add instructions for demo flow scenarios
- [ ] Document consent management workflow
- [ ] Update API endpoint documentation

**Estimated Time**: 30 minutes

---

### Task 6.3: Update Roadmap
**File**: `agentPlanning/roadmap.md`

- [ ] Mark Epic 6 as complete
- [ ] Update Epic 7 (formerly Epic 6) description
- [ ] Document key outputs from Epic 6
- [ ] Update success criteria if needed

**Estimated Time**: 20 minutes

---

### Task 6.4: Code Cleanup

- [ ] Remove debug console.logs
- [ ] Format code (prettier frontend, black backend)
- [ ] Add docstrings to new backend functions
- [ ] Add comments for complex logic
- [ ] Verify all imports are used
- [ ] Check for any TODOs or FIXMEs

**Estimated Time**: 30 minutes

---

## Task Summary

**Total Tasks**: 37 across 6 phases  
**Estimated Total Time**: ~24 hours

**Critical Path**:
1. Backend consent + recommendation management (Phase 1)
2. Backend end user API (Phase 2)
3. Frontend operator enhancements (Phase 3)
4. Frontend end user portal (Phase 4)
5. Testing (Phase 5)

**Quick Start**: Complete Phase 1 first to unblock frontend work

---

## Success Checklist

- [ ] Consent grant triggers recommendation generation
- [ ] Consent revoke soft deletes recommendations
- [ ] All queries filter DELETED recommendations
- [ ] Operator view shows non-consented users (grayed out)
- [ ] Operator can generate new recommendations
- [ ] Operator can delete recommendations
- [ ] End user landing has user selection dropdown
- [ ] End user portal shows three states correctly
- [ ] End user can grant/revoke consent
- [ ] User insights display transaction data
- [ ] No localStorage persistence (always dropdown)
- [ ] Demo flow scenarios work end-to-end
- [ ] Documentation updated

---


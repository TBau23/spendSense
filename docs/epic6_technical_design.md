# Epic 6: Consent Management & End User Experience - Technical Design

**Status**: Ready for Implementation  
**Epic Goal**: Enable consent workflows + end user portal + operator enhancements for demo  
**Dependencies**: Epic 5 complete (Operator dashboard functional)

---

## Overview

This epic adds three major pieces:
1. **Consent management**: Grant/revoke flows that trigger processing
2. **End user portal**: Simple view for users to see recs and manage consent
3. **Operator enhancements**: Generate/delete recommendations, show non-consented users

**Out of Scope**: Mobile optimization, real authentication, user data editing

---

## Backend Changes

### 1. Consent Management

**New Module**: `backend/guardrails/consent.py` (extend existing)

Add endpoints:
```python
POST /api/consent/grant
Body: { "user_id": "user_123" }
Actions:
  1. Update users.consent = true
  2. Trigger async recommendation generation (call recommend/generator.py)
  3. Return immediately with 202 Accepted

POST /api/consent/revoke
Body: { "user_id": "user_123" }
Actions:
  1. Update users.consent = false
  2. Soft delete recommendations (status = 'DELETED')
  3. Return 200 OK
```

**Implementation Notes**:
- Use existing `generate_recommendation()` from `backend/recommend/generator.py`
- Run generation in background thread or accept that it blocks (demo scope)
- Soft delete: `UPDATE recommendations SET status = 'DELETED' WHERE user_id = ?`

### 2. Recommendation Management

**New Module**: `backend/recommend/management.py`

```python
def generate_recommendation_for_user(user_id: str) -> dict:
    """Trigger full recommendation pipeline, returns rec with PENDING_REVIEW status"""
    # Reuse existing generator.generate_recommendation()
    # Store in database
    # Return recommendation dict

def soft_delete_recommendation(rec_id: str) -> bool:
    """Set recommendation status to DELETED"""
    # UPDATE recommendations SET status = 'DELETED' WHERE recommendation_id = ?
```

Add endpoints:
```python
POST /api/operator/users/{user_id}/generate
  - Calls generate_recommendation_for_user()
  - Returns new recommendation

DELETE /api/operator/recommendations/{rec_id}
  - Calls soft_delete_recommendation()
  - Returns 204 No Content
```

**Query Updates**: All existing recommendation queries must filter `status != 'DELETED'`
- Affected files: `backend/api/operator.py`, `backend/guardrails/metrics.py`

### 3. End User API

**New Module**: `backend/api/user.py`

```python
GET /api/users
  - Returns list of all users (name, user_id, consent status, has_approved_recs)
  - For user selection dropdown

GET /api/users/{user_id}
  - Returns basic user info (name, consent status)
  - Public endpoint (no sensitive data)

GET /api/users/{user_id}/recommendations
  - Returns APPROVED recommendations only
  - Includes user_snapshot and recommendation items
  - Returns empty array if none approved

GET /api/users/{user_id}/insights
  - NEW: Returns transaction-based insights for end user view
  - Top merchants (by spend)
  - Spending by category (top 5)
  - Recent activity summary
  - Query transactions table, aggregate by merchant/category
```

---

## Database Changes

**No schema changes required**. Use existing tables:
- Add `'DELETED'` as valid status value for recommendations (soft delete)
- Consent field already exists in users table

**Migration**: None needed, just update query filters

---

## Frontend: Operator Enhancements

### 1. Show Non-Consented Users

**File**: `frontend/src/components/UserList.jsx`

**Changes**:
- Remove consent filter from API call
- Add visual indicator for non-consented users:
  - Gray out row (opacity: 0.6)
  - Badge: "Consent Required" (red/orange)
- Disable "View Details" button for non-consented users
- Add tooltip: "User has not granted consent"

**File**: `frontend/src/api/operator.js`

Update `fetchUsers()` to not filter by consent (backend returns all)

### 2. Generate & Delete Actions

**File**: `frontend/src/pages/UserDetailView.jsx`

Add buttons near page header:
- "Generate New Recommendation" button (primary action)
- Calls `POST /api/operator/users/{user_id}/generate`
- Shows loading spinner during generation
- Refreshes recommendation list on success

**File**: `frontend/src/components/RecommendationCard.jsx`

Add delete button to card header:
- Icon button (trash can) next to status badge
- Confirmation modal: "Delete this recommendation?"
- Calls `DELETE /api/operator/recommendations/{rec_id}`
- Removes card from view on success

**New API Functions** (`frontend/src/api/operator.js`):
```javascript
export const generateRecommendation = async (userId) => { ... }
export const deleteRecommendation = async (recId) => { ... }
```

---

## Frontend: End User Portal

### Route Structure

**File**: `frontend/src/App.jsx`

Add routes:
```jsx
<Routes>
  <Route path="/operator" element={<OperatorDashboard />} />
  <Route path="/operator/users/:userId" element={<UserDetailView />} />
  <Route path="/user" element={<UserLanding />} />
  <Route path="/user/:userId" element={<UserPortal />} />
  <Route path="/" element={<Navigate to="/user" />} />
</Routes>
```

### Components

**1. UserLanding.jsx** (NEW)
- Dropdown to select user (shows name + masked ID)
- On selection, navigate to `/user/:userId`
- Simple centered layout with SpendSense branding

**2. UserPortal.jsx** (NEW)
- Main end user view
- Fetches user data, recommendations, insights
- Shows different content based on state:

**State A: Non-Consented User**
```
┌─────────────────────────────────────┐
│  Welcome, [Name]                     │
│                                      │
│  Grant consent to get personalized   │
│  financial education                 │
│                                      │
│  [Grant Consent Button]              │
└─────────────────────────────────────┘
```

**State B: Consented, No Approved Recs**
```
┌─────────────────────────────────────┐
│  Welcome, [Name]                     │
│                                      │
│  Your personalized recommendations   │
│  are being prepared. Check back soon!│
│                                      │
│  [Revoke Consent Button]             │
└─────────────────────────────────────┘
```

**State C: Consented, Has Approved Recs**
```
┌─────────────────────────────────────┐
│  Welcome, [Name]                     │
│  [Financial Insights Panel]          │
│  [Recommendations List]              │
│  [Revoke Consent Button]             │
└─────────────────────────────────────┘
```

**3. UserInsights.jsx** (NEW)
- Shows transaction-based insights
- Top merchants (top 3-5 by spend)
- Spending by category (pie chart or bar representation)
- Total spend last 30 days
- Uses data from `/api/users/{user_id}/insights`

**4. UserRecommendationCard.jsx** (NEW)
- Simplified version of operator's RecommendationCard
- Shows user_snapshot (if present)
- Shows educational items (title + content)
- Shows actionable items (title + because + action)
- Shows partner offers (if any)
- NO status badges, NO decision traces, NO approval actions

**5. ConsentToggle.jsx** (NEW)
- Grant button: Calls `/api/consent/grant`, shows loading, navigates to "check back soon" state
- Revoke button: Shows confirmation modal, calls `/api/consent/revoke`, navigates to non-consented state

### API Client

**New File**: `frontend/src/api/user.js`

```javascript
export const fetchAllUsers = async () => { ... }
export const fetchUser = async (userId) => { ... }
export const fetchUserRecommendations = async (userId) => { ... }
export const fetchUserInsights = async (userId) => { ... }
export const grantConsent = async (userId) => { ... }
export const revokeConsent = async (userId) => { ... }
```

---

## Styling Approach

**Reference**: Follow existing patterns from `frontend/src/index.css` and component styles

**New Components**: Use Tailwind utility classes consistent with existing components

**Key Visual Elements**:
- Non-consented users: Gray + badge (reuse existing badge styles)
- Consent buttons: Primary action styling (green for grant, red for revoke)
- User portal: Clean, centered, card-based layout
- Loading states: Spinner component (reuse from operator view if exists)

---

## Testing Strategy

### Backend
1. Test consent grant → triggers rec generation
2. Test consent revoke → soft deletes recommendations
3. Test generate endpoint → creates new PENDING_REVIEW rec
4. Test delete endpoint → marks rec as DELETED
5. Test user insights endpoint → returns correct aggregations
6. Test recommendation queries filter DELETED status

### Frontend
1. Operator: Non-consented users appear grayed out, can't click
2. Operator: Generate button creates new rec
3. Operator: Delete button removes rec from view
4. User portal: Dropdown selects user, navigates correctly
5. User portal: Grant consent shows loading, then "check back soon"
6. User portal: Approved recs display correctly
7. User portal: Revoke consent prompts confirmation, returns to non-consented view

---

## Configuration

**File**: `config.json` (if needed)

```json
{
  "user_portal": {
    "insights_top_merchants_count": 5,
    "insights_top_categories_count": 5,
    "insights_window_days": 30
  }
}
```

---

## Success Criteria

- [ ] Consent grant endpoint triggers recommendation generation
- [ ] Consent revoke endpoint soft deletes recommendations
- [ ] Operator view shows non-consented users (grayed out, can't click)
- [ ] Operator can generate new recommendations from user detail page
- [ ] Operator can delete recommendations
- [ ] End user landing page has user selection dropdown
- [ ] End user portal shows different states (non-consented, waiting, recs available)
- [ ] End user can grant/revoke consent
- [ ] User insights display transaction data
- [ ] All queries filter out DELETED recommendations
- [ ] No localStorage persistence (always starts at dropdown)

---

## Design Decisions

**1. Soft Delete vs Hard Delete**
- **Decision**: Soft delete (status = 'DELETED')
- **Rationale**: Preserves audit trail, can recover if needed, simpler rollback
- **Impact**: Must update all queries to filter DELETED status

**2. Async Recommendation Generation**
- **Decision**: Trigger in background, return immediately (202 Accepted)
- **Rationale**: Don't block consent grant API call, better UX
- **Impact**: User sees "check back soon" state until generation completes

**3. No localStorage Persistence**
- **Decision**: User selection doesn't persist across refreshes
- **Rationale**: Demo scenario requires jumping between users quickly
- **Impact**: Always returns to user dropdown on page load

**4. Separate User Routes**
- **Decision**: `/user/:userId` separate from `/operator`
- **Rationale**: Clear separation of concerns, different access patterns
- **Impact**: Two distinct frontend experiences

**5. Simplified End User View**
- **Decision**: No personas, no decision traces, no status badges
- **Rationale**: End users don't need operator debugging tools
- **Impact**: Cleaner, education-focused experience

---

## References

- Existing consent utilities: `backend/guardrails/consent.py`
- Recommendation generation: `backend/recommend/generator.py`
- Operator API patterns: `backend/api/operator.py`
- Frontend API client: `frontend/src/api/operator.js`
- Component styling: `frontend/src/index.css`


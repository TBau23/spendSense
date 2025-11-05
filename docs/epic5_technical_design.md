# Epic 5: Guardrails & Operator View - Technical Design

**Status**: Ready for Implementation  
**Epic Goal**: Consent enforcement + operator dashboard for review/approval  
**Dependencies**: Epic 4 complete (Recommendations generated)

---

## Overview

Build operator dashboard for reviewing and approving recommendations. Focus on consent enforcement (filtering non-consented users), approval workflow, decision trace visibility, and metrics. User-facing views deferred to Epic 6.

---

## Scope

**IN SCOPE**:
- ✅ Consent enforcement (filter non-consented users from operator view)
- ✅ Recommendation status workflow (PENDING_REVIEW → APPROVED/FLAGGED)
- ✅ React operator dashboard:
  - Main page: User list with filtering, aggregate metrics
  - User detail page: Recommendations, decision traces, approve/flag actions, user metrics
- ✅ FastAPI endpoints for operator actions
- ✅ Decision trace viewer
- ✅ Metrics computation (coverage, pending count, approval rate)

**OUT OF SCOPE** (Future Epics):
- ❌ Override mechanism (comment placeholder only)
- ❌ Automated tone validation (manual review only)
- ❌ User-facing dashboard (Epic 6)
- ❌ Consent grant/revoke UI (Epic 6)
- ❌ Enhanced eligibility guardrails (Epic 4 sufficient)

---

## Recommendation Status Workflow

### Status Field Addition

Add `status` field to `recommendations` table:

```sql
ALTER TABLE recommendations ADD COLUMN status TEXT DEFAULT 'PENDING_REVIEW';
ALTER TABLE recommendations ADD COLUMN reviewed_at TIMESTAMP NULL;
ALTER TABLE recommendations ADD COLUMN reviewer_notes TEXT NULL;
```

**Status Values**:
- `PENDING_REVIEW`: Generated, awaiting operator approval
- `APPROVED`: Operator approved, deliverable to user (Epic 6)
- `FLAGGED`: Operator flagged for issues, blocked from delivery

### Approval Actions

**Approve**: Mark recommendation as deliverable
```python
def approve_recommendation(rec_id: str, reviewer_notes: Optional[str] = None):
    update_status(rec_id, 'APPROVED', reviewer_notes)
```

**Flag**: Block recommendation from delivery
```python
def flag_recommendation(rec_id: str, reviewer_notes: str):
    update_status(rec_id, 'FLAGGED', reviewer_notes)
```

**Override** (placeholder for Epic 6+):
```python
# def override_recommendation(rec_id: str, overrides: dict):
#     # Allow operator to edit content before approving
#     pass
```

---

## API Endpoints

### Operator Endpoints

**GET /api/operator/users**
- Returns list of all consented users with metadata
- Query params: `?persona={id}&status={pending|approved|flagged}&sort={name|date}`
- Response includes: `user_id`, `name`, `primary_persona`, `has_pending_recs`, `rec_count`, `last_rec_date`

**GET /api/operator/users/{user_id}**
- Returns detailed user profile
- Includes: persona assignments (30d/180d), all features, recommendation history
- Consent check: Returns 403 if user has not consented

**GET /api/operator/users/{user_id}/recommendations**
- Returns all recommendations for user (all statuses)
- Includes full recommendation packages with items

**GET /api/operator/recommendations/{rec_id}**
- Returns single recommendation with all items

**POST /api/operator/recommendations/{rec_id}/approve**
- Body: `{ "reviewer_notes": "optional" }`
- Marks recommendation as APPROVED

**POST /api/operator/recommendations/{rec_id}/flag**
- Body: `{ "reviewer_notes": "required" }`
- Marks recommendation as FLAGGED

**GET /api/operator/traces/{user_id}**
- Returns decision traces (why persona assigned, why content selected)
- Includes: persona assignment rationale, feature values, eligibility checks

**GET /api/operator/metrics**
- Returns aggregate metrics:
  - Total consented users
  - Users with pending recommendations
  - Approval rate (approved / total reviewed)
  - Avg recommendations per user
  - Coverage (% users with ≥3 detected behaviors)

---

## Frontend Architecture

### Tech Stack
- **React 18** with Vite
- **React Router** for navigation
- **Tailwind CSS** for styling
- **Fetch API** for backend calls

### Routes

```
/operator                    → OperatorDashboard (main page)
/operator/users/:userId      → UserDetailView
```

### Components

```
frontend/src/
├── pages/
│   ├── OperatorDashboard.jsx      # Main page: user list + metrics
│   └── UserDetailView.jsx         # Individual user: recs + traces
├── components/
│   ├── UserList.jsx               # Filterable user table
│   ├── UserListItem.jsx           # Single user row
│   ├── MetricsPanel.jsx           # Aggregate metrics display
│   ├── RecommendationCard.jsx     # Single recommendation package
│   ├── RecommendationItem.jsx     # Educational/actionable/offer item
│   ├── DecisionTrace.jsx          # Decision trace viewer
│   ├── UserMetrics.jsx            # Per-user metrics panel
│   └── ApprovalActions.jsx        # Approve/Flag buttons
└── api/
    └── operator.js                # API client functions
```

---

## Dashboard Views

### Main Page: Operator Dashboard

**Layout**:
- Header with "SpendSense Operator View" title
- Metrics panel (top): Cards showing aggregate metrics
- Filter bar: Dropdowns for persona, status, sort order
- User list: Table with columns:
  - Name
  - User ID (masked, last 4 digits)
  - Primary Persona (30d)
  - Status badge (Pending/Approved/Flagged)
  - Recommendation count
  - Last recommendation date
  - Action button (View Details)

**Visual Indicators**:
- Users with pending recommendations: Yellow/orange badge or icon
- Users with flagged recommendations: Red badge
- Users with only approved recommendations: Green badge

**Filtering**:
- Persona dropdown: All, Persona 1, Persona 2, etc.
- Status dropdown: All, Pending Review, Approved, Flagged
- Sort: Name (A-Z), Recent activity, Most pending

### User Detail Page

**Layout**:
- Breadcrumb: Operator → User {name}
- User header: Name, ID, consent status
- 3-column layout:
  - **Left column (30%)**: User metrics panel
    - Persona assignments (30d & 180d)
    - Key feature metrics (credit utilization, savings rate, etc.)
    - Account summary (checking, savings, credit cards)
  - **Center column (50%)**: Recommendations list
    - Each recommendation in collapsible card
    - Status badge (pending/approved/flagged)
    - Generated date
    - Educational items, actionable items, partner offers
    - Rationales visible
    - Approve/Flag buttons at bottom (if pending)
  - **Right column (20%)**: Decision traces
    - "Why Persona 1?" expandable section
    - "Why this content?" expandable section
    - Feature values cited

**Approval Actions**:
- Approve button: Green, primary action
- Flag button: Red, requires confirmation modal with notes field
- (Override button: Grayed out, tooltip "Coming soon")

---

## Decision Traces

### Trace Structure

Decision traces explain **why** recommendations were generated.

**Persona Assignment Trace**:
```json
{
  "trace_type": "persona_assignment",
  "user_id": "user_123",
  "window_days": 30,
  "primary_persona_id": 1,
  "primary_persona_name": "High Utilization",
  "rationale": "User met criteria for Persona 1 due to credit utilization ≥50%",
  "criteria_met": {
    "max_utilization": 0.68,
    "threshold": 0.50,
    "rule": "Any card utilization ≥50%"
  },
  "feature_values_cited": {
    "credit.max_utilization": 0.68,
    "credit.total_balance": 3400,
    "credit.interest_charges_present": true
  }
}
```

**Content Selection Trace**:
```json
{
  "trace_type": "content_selection",
  "recommendation_id": "rec_abc123",
  "educational_items": [
    {
      "content_id": "edu_credit_utilization_101",
      "selected_reason": "Primary relevance to Persona 1 (High Utilization)",
      "persona_tags": [1]
    }
  ],
  "partner_offers": [
    {
      "offer_id": "offer_bt_card_001",
      "selected_reason": "Eligible based on credit score ≥670 and utilization ≤85%",
      "eligibility_passed": true,
      "eligibility_details": {
        "estimated_credit_score": 680,
        "min_required": 670
      }
    }
  ]
}
```

### Trace Generation

Generate traces at recommendation creation time (Epic 4 code):
```python
def generate_traces(user_id: str, recommendation: dict):
    traces = []
    
    # Persona assignment trace
    traces.append(generate_persona_trace(user_id, recommendation))
    
    # Content selection trace
    traces.append(generate_content_trace(recommendation))
    
    store_traces(user_id, traces)
```

Store in new table:
```sql
CREATE TABLE decision_traces (
    trace_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    recommendation_id TEXT,
    trace_type TEXT NOT NULL,
    trace_content TEXT NOT NULL,  -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (recommendation_id) REFERENCES recommendations(recommendation_id)
);
```

---

## Consent Enforcement

### Filtering Strategy

**Backend enforcement**:
```python
def get_consented_users() -> List[dict]:
    """Only return users with consent=true"""
    return db.query("SELECT * FROM users WHERE consent = true")

def check_consent(user_id: str) -> bool:
    """Verify user has consented before processing"""
    user = db.get_user(user_id)
    if not user or not user['consent']:
        raise ConsentError(f"User {user_id} has not consented")
    return True
```

**Operator view behavior**:
- User list only shows consented users
- API returns 403 for non-consented user detail requests
- Non-consented users are invisible to operator (Epic 6 will add consent management)

---

## Metrics

### Aggregate Metrics (Main Dashboard)

Computed on-demand or cached:

```python
def compute_operator_metrics():
    return {
        "total_consented_users": count_users(consent=True),
        "users_with_pending_recs": count_users_with_status('PENDING_REVIEW'),
        "total_recommendations_generated": count_recommendations(),
        "pending_count": count_recommendations('PENDING_REVIEW'),
        "approved_count": count_recommendations('APPROVED'),
        "flagged_count": count_recommendations('FLAGGED'),
        "approval_rate": approved / (approved + flagged) if (approved + flagged) > 0 else 0,
        "avg_recs_per_user": total_recs / total_users,
        "coverage_pct": count_users_with_persona() / total_consented_users
    }
```

### Per-User Metrics (User Detail Page)

```python
def get_user_metrics(user_id: str):
    return {
        "personas": {
            "window_30d": get_persona_assignment(user_id, 30),
            "window_180d": get_persona_assignment(user_id, 180)
        },
        "features": get_all_features(user_id),  # From Epic 2
        "accounts": {
            "checking_count": count_accounts(user_id, 'checking'),
            "savings_count": count_accounts(user_id, 'savings'),
            "credit_card_count": count_accounts(user_id, 'credit_card')
        },
        "recommendations": {
            "total_generated": count_user_recommendations(user_id),
            "pending": count_user_recommendations(user_id, 'PENDING_REVIEW'),
            "approved": count_user_recommendations(user_id, 'APPROVED'),
            "flagged": count_user_recommendations(user_id, 'FLAGGED')
        }
    }
```

---

## Module Structure

```
backend/
├── api/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   └── operator.py          # Operator endpoints
├── guardrails/
│   ├── __init__.py
│   ├── consent.py           # Consent checking utilities
│   └── metrics.py           # Metrics computation
└── recommend/
    └── traces.py            # Decision trace generation (add to Epic 4 module)

frontend/src/
├── pages/
│   ├── OperatorDashboard.jsx
│   └── UserDetailView.jsx
├── components/
│   ├── UserList.jsx
│   ├── MetricsPanel.jsx
│   ├── RecommendationCard.jsx
│   ├── DecisionTrace.jsx
│   └── ApprovalActions.jsx
└── api/
    └── operator.js
```

---

## Testing Strategy

### Backend Tests (≥6)
1. Consent filtering: Non-consented users excluded from operator user list
2. Approve recommendation: Status updates to APPROVED with timestamp
3. Flag recommendation: Status updates to FLAGGED, requires notes
4. Metrics computation: Aggregate metrics return correct counts
5. Decision trace generation: Traces stored for recommendations
6. API consent check: Returns 403 for non-consented user detail request

### Frontend Tests (Manual/Optional)
- User list renders with filtering
- User detail page loads recommendations
- Approve action updates status and shows confirmation
- Flag action requires notes input

---

## Configuration

Extend `config.json`:
```json
{
  "api": {
    "host": "localhost",
    "port": 8000,
    "cors_origins": ["http://localhost:5173"]
  },
  "operator": {
    "metrics_cache_ttl_seconds": 60,
    "default_page_size": 50,
    "max_page_size": 200
  }
}
```

---

## Success Criteria

Epic 5 complete when:
- [ ] Status field added to recommendations table
- [ ] FastAPI endpoints operational (8 endpoints)
- [ ] Consent enforcement working (non-consented users filtered)
- [ ] React operator dashboard renders user list with filtering
- [ ] User detail page shows recommendations + traces
- [ ] Approve/flag actions work and update database
- [ ] Metrics display on main dashboard (aggregate) and user detail (per-user)
- [ ] Decision traces generated and viewable
- [ ] ≥6 backend tests passing
- [ ] Override placeholder commented out for future

---

## Design Decisions

### 1. Consent Enforcement via Filtering
**Decision**: Filter non-consented users from operator view (invisible)  
**Rationale**: Simplifies Epic 5 scope; Epic 6 will add consent management  
**Impact**: Operator never sees non-consented users, aligns with privacy principles

### 2. Simple Status Workflow
**Decision**: Three statuses only (PENDING_REVIEW, APPROVED, FLAGGED)  
**Rationale**: Sufficient for demo; avoids complexity of draft/revision/resubmit states  
**Impact**: Flagged recommendations are dead-end until operator regenerates (Epic 6+)

### 3. No Override Yet
**Decision**: Comment out override functionality, implement in Epic 6  
**Rationale**: Approval/flag covers core workflow; override adds complexity  
**Impact**: Placeholder in UI (grayed out button) and API (commented function)

### 4. Manual Tone Validation Only
**Decision**: No automated tone checking, operator reviews manually  
**Rationale**: Automated checks add complexity with limited value for 50-100 user demo  
**Impact**: Operator responsible for catching judgmental language during review

### 5. Decision Traces as Separate Table
**Decision**: Store traces in dedicated `decision_traces` table with JSON content  
**Rationale**: Flexible schema, easy to query, avoids bloating recommendations table  
**Impact**: Traces generated at recommendation creation (Epic 4 code addition)

---

## Next Epic Prerequisites

**What Epic 6 Needs from Epic 5**:
- [ ] Status workflow operational (recommendations have APPROVED/FLAGGED status)
- [ ] Operator dashboard functional and tested
- [ ] Consent enforcement working
- [ ] FastAPI endpoints documented and operational
- [ ] Metrics computation functions available
- [ ] Decision traces stored and retrievable
- [ ] Override placeholder identified for implementation

---


# Polish Epic: UI & Content Refinement - Technical Design

**Status**: Ready for Implementation  
**Epic Goal**: Reduce content redundancy, improve decision trace usefulness, enhance visual presentation  
**Dependencies**: Epic 5 complete (Operator dashboard functional)

---

## Overview

After completing Epics 1-5, the system is functional but has content quality issues:
- Repetitive "Why" sections in educational content
- Generic, unhelpful decision traces
- Verbose recommendation presentation
- Excessive screen space usage

This polish epic focuses on **content efficiency and trace clarity** without major architectural changes.

---

## Problems Identified

### 1. Redundant "Why" Sections
Every educational item repeats the same user data with slight variations:
```
Item 1 Why: "We noticed your utilization is 65%..."
Item 2 Why: "We noticed your utilization is 65%..."
Item 3 Why: "We noticed your utilization is 65%..."
```
**Impact**: Wastes 60% of screen space, poor UX

### 2. Generic Decision Traces
Persona traces provide no actionable detail:
```
"User met criteria for High Utilization based on detected financial behaviors."
```
**Impact**: Useless for operator auditing, debugging, or understanding

### 3. Verbose Actionable Items
"Because" sections are helpful but could be more concise and action-focused

---

## Solution: Hybrid Approach (Option 3)

### Component 1: User Financial Snapshot Card
**Add** a single metrics summary at the top of recommendations showing key triggers:

```
┌─ Your Financial Snapshot ─────────────────────┐
│ Credit Utilization: 65% on Visa ****4523      │
│   ($3,400 of $5,000 limit)                    │
│ Monthly Interest: $87                          │
│ Payment Pattern: Minimum payments only        │
└────────────────────────────────────────────────┘
```

**Rules**:
- Show 3-5 most relevant metrics for the persona
- Persona-specific (different metrics for Subscription-Heavy vs High Utilization)
- Generated once, displayed at top

### Component 2: Clean Educational Content
**Remove** "Why" sections from educational items entirely:

**Before**:
```
Understanding Credit Utilization and Your Credit Score
[Content...]

Why: We noticed your credit utilization is currently at 65%...
     [3-4 lines of repetitive explanation]
```

**After**:
```
Understanding Credit Utilization and Your Credit Score
[Content only - no "Why"]
```

### Component 3: Data-Rich Decision Traces
**Replace** generic text with actual criteria and values:

**Before**:
```
Persona: High Utilization
Status: ASSIGNED
User met criteria for High Utilization based on detected financial behaviors.
```

**After**:
```
Persona: High Utilization
Status: ASSIGNED

Criteria Met:
  ✓ Credit utilization ≥50% (Actual: 65% on card ****4523)
  ✓ Interest charges present (Actual: $87/month)
  ✓ Minimum payment only detected (Yes)

Feature Values:
  • Total credit limit: $5,000
  • Current balance: $3,400
  • Last payment: $25 (minimum)
```

**Note**: Actionable item "Because" sections are already well-written and varied, so no changes needed there.

---

## Technical Implementation

### Backend Changes

#### 1. Generate User Snapshot Context
**New Function**: `backend/recommend/generator.py::generate_user_snapshot()`

```python
def generate_user_snapshot(
    persona_context: Dict,
    features: Dict
) -> Dict[str, Any]:
    """
    Generate 3-5 key metrics for user's financial snapshot
    Returns persona-specific metrics
    """
    persona_id = persona_context['primary_persona_id']
    
    # Different metrics per persona
    if persona_id == 1:  # High Utilization
        return {
            'metrics': [
                {
                    'label': 'Credit Utilization',
                    'value': '65% on Visa ****4523',
                    'detail': '$3,400 of $5,000 limit'
                },
                # ... 2-4 more metrics
            ]
        }
    # ... other personas
```

**Storage**: Add `user_snapshot` field to recommendations table as JSON

#### 2. Remove "Why" Generation
**File**: `backend/recommend/generator.py`

- Remove `generate_educational_rationales()` function call
- Strip "Why" field from educational content items
- Keep content text only

#### 3. Enhance Decision Traces
**File**: `backend/recommend/traces.py::generate_persona_trace()`

**Current** (line 56-63):
```python
if trace['status'] == 'STABLE':
    trace['rationale'] = "User did not meet criteria..."
elif trace['primary_persona_id']:
    persona_name = trace['primary_persona_name']
    trace['rationale'] = f"User met criteria for {persona_name}..."
```

**New**:
```python
# Parse criteria_met and feature_values to build detailed rationale
criteria_list = []
for criterion, met in trace['criteria_met'].items():
    if met:
        # Get actual value from feature_values_cited
        actual_value = trace['feature_values_cited'].get(criterion, 'N/A')
        criteria_list.append({
            'criterion': criterion,
            'threshold': get_threshold_for_criterion(criterion),
            'actual': actual_value
        })

trace['rationale'] = {
    'summary': f"Met {len(criteria_list)} criteria for {persona_name}",
    'criteria_details': criteria_list
}
```

**Helper Function**: `get_threshold_for_criterion()` to map criteria to human-readable thresholds

---

### Frontend Changes

#### 1. Add User Snapshot Component
**New File**: `frontend/src/components/UserSnapshot.jsx`

```jsx
const UserSnapshot = ({ snapshot }) => {
  if (!snapshot || !snapshot.metrics) return null;
  
  return (
    <div className="user-snapshot-card">
      <h4>Your Financial Snapshot</h4>
      {snapshot.metrics.map((metric, idx) => (
        <div key={idx} className="snapshot-metric">
          <span className="label">{metric.label}:</span>
          <span className="value">{metric.value}</span>
          {metric.detail && <span className="detail">{metric.detail}</span>}
        </div>
      ))}
    </div>
  );
};
```

**Integration**: Add to `RecommendationCard.jsx` at top of content section

#### 2. Add User Detail Header with Name
**File**: `frontend/src/pages/UserDetailView.jsx`

Update page header to display user's name with masked ID:
```jsx
// Format: "Crystal Robinson (***640fb)"
const displayName = `${user.full_name} (***${user.user_id.slice(-5)})`;
```

#### 3. Remove "Why" Display
**File**: `frontend/src/components/RecommendationCard.jsx`

Remove rendering of `item.why` or `item.rationale` from educational content display

#### 4. Enhance Decision Trace Display
**File**: `frontend/src/components/DecisionTrace.jsx::renderPersonaTrace()`

**Current** (line 46-66):
```jsx
return (
  <div className="trace-details">
    <p><strong>Persona:</strong> {content.primary_persona_name}</p>
    <p><strong>Status:</strong> {content.status}</p>
    <p className="rationale">{content.rationale}</p>
    ...
  </div>
);
```

**New**:
```jsx
return (
  <div className="trace-details">
    <p><strong>Persona:</strong> {content.primary_persona_name}</p>
    <p><strong>Status:</strong> {content.status}</p>
    
    {content.rationale?.criteria_details && (
      <div className="criteria-met">
        <h5>Criteria Met:</h5>
        {content.rationale.criteria_details.map((c, idx) => (
          <div key={idx} className="criterion">
            ✓ {c.criterion}: {c.threshold} (Actual: {c.actual})
          </div>
        ))}
      </div>
    )}
    
    {/* Keep existing collapsible feature values */}
  </div>
);
```

---

## Task Breakdown

### Backend Tasks
1. **Add user snapshot generation** (generator.py)
   - Implement `generate_user_snapshot()` function
   - Add persona-specific metric selection logic
   - Store in recommendations table

2. **Remove "Why" generation** (generator.py)
   - Remove `generate_educational_rationales()` call
   - Update educational item structure

3. **Enhance decision traces** (traces.py)
   - Parse criteria_met into detailed list
   - Add threshold mapping helper
   - Format rationale as structured data

### Frontend Tasks
4. **Create UserSnapshot component**
   - Build component with styling
   - Integrate into RecommendationCard

5. **Remove "Why" rendering**
   - Update RecommendationCard.jsx
   - Clean up related CSS

6. **Enhance DecisionTrace component**
   - Add criteria details rendering
   - Style as checklist with actual values
   - Keep collapsible feature details

7. **Update user detail header**
   - Display user name with masked ID
   - Format: "Name (***id_suffix)"

### Testing & Validation
8. **Regenerate test recommendations**
   - Generate for 2-3 users across different personas
   - Verify snapshot shows correct metrics
   - Verify traces show criteria details

9. **Visual polish**
   - Adjust spacing/padding
   - Ensure mobile responsiveness
   - Test with long/short content

---

## Success Criteria

✅ Recommendations display user snapshot card with 3-5 key metrics  
✅ Educational content has no "Why" sections  
✅ Decision traces show specific criteria with actual values  
✅ User detail page shows "Name (***id)" format instead of raw user_id  
✅ Screen space reduced by ~40-60%  
✅ Decision traces are useful for operator auditing  
✅ No information loss (data moved to snapshot card)

---

## Estimated Impact

- **Screen space reduction**: 40-60% less scrolling
- **Content clarity**: Higher signal-to-noise ratio
- **Operator utility**: Decision traces now debuggable
- **UX improvement**: User names instead of technical IDs
- **Implementation time**: 4-6 hours (9 lightweight tasks)

---

## Notes

- This is a **content/presentation polish** epic, not a feature epic
- No schema changes required (use existing JSON fields)
- Can regenerate recommendations incrementally (per user) for testing
- Maintains all information, just reorganizes presentation
- Improves both user-facing and operator-facing views


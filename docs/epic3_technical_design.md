# Epic 3: Persona System - Technical Design

**Status**: Ready for Implementation  
**Epic Goal**: Assign personas with severity-based prioritization  
**Dependencies**: Epic 2 complete (Feature computation operational)

---

## Overview

Assign personas to users based on computed behavioral signals from Epic 2. Support dual time windows (30d and 180d), multi-persona tracking (primary + secondary), and severity-based prioritization. Include clear audit trails for transparency and operator review.

---

## Requirements Summary

From `project_requirements.md` and `roadmap.md`:
- **5 Personas**: High Utilization, Variable Income Budgeter, Subscription-Heavy, Savings Builder, Cash Flow Stressed
- **Priority Levels**: CRITICAL > HIGH > MEDIUM > LOW
- **Time Windows**: 30-day and 180-day (separate assignments)
- **Multi-Persona**: Primary + 1 secondary persona per window
- **Tie-Breaking**: Severity scores (quantitative measures)
- **Audit Trail**: Clear quantitative reasoning for assignments
- **Unmatched Users**: "Unassigned/Stable" status (6th state)

---

## Persona Specifications

### Priority Hierarchy

Based on financial urgency (roadmap lines 59-68):

| Priority | Persona | Key Risk |
|----------|---------|----------|
| **CRITICAL** | Persona 1: High Utilization | Debt spiral, credit damage, high interest |
| **HIGH** | Persona 5: Cash Flow Stressed | Overdraft risk, liquidity crisis |
| **HIGH** | Persona 2: Variable Income Budgeter | Income uncertainty + low buffer |
| **MEDIUM** | Persona 3: Subscription-Heavy | Money leak, optimization opportunity |
| **LOW** | Persona 4: Savings Builder | Positive trajectory, enrichment only |
| **NONE** | Unassigned/Stable | No intervention needed |

---

### Persona 1: High Utilization

**Criteria** (requirements lines 67-71):
```
ANY of:
- Any card utilization ≥50%
- Interest charges present (interest_charges_present = TRUE)
- Minimum-payment-only detected (minimum_payment_only = TRUE)
- Any card overdue (is_overdue = TRUE)
```

**Feature Dependencies**:
- `credit.parquet`: `max_utilization`, `interest_charges_present`, `minimum_payment_only`, `is_overdue`

**Severity Score**:
```python
severity = max_utilization  # 0.0 to 1.0+
```
Higher utilization = more severe

---

### Persona 2: Variable Income Budgeter

**Criteria** (requirements lines 72-76):
```
ALL of:
- Median pay gap > 45 days
- Cash-flow buffer < 1 month
```

**Feature Dependencies**:
- `income.parquet`: `median_pay_gap_days`, `cash_flow_buffer_months`

**Severity Score**:
```python
severity = median_pay_gap_days / 45.0  # normalized to threshold
```
Longer gaps = more severe

---

### Persona 3: Subscription-Heavy

**Criteria** (requirements lines 77-81):
```
ALL of:
- Recurring merchants ≥3
- At least ONE of:
  - Monthly recurring spend ≥$50 (in 30d window)
  - Subscription spend share ≥10%
```

**Feature Dependencies**:
- `subscriptions.parquet`: `recurring_merchant_count`, `monthly_recurring_spend`, `subscription_share`

**Severity Score**:
```python
severity = subscription_share  # 0.0 to 1.0
```
Higher share of spend = more severe

---

### Persona 4: Savings Builder

**Criteria** (requirements lines 82-86):
```
ALL of:
- (Savings growth rate ≥2% over window OR net savings inflow ≥$200/month)
- ALL card utilizations < 30% (strict: every single card, or no credit cards)
```

**Feature Dependencies**:
- `savings.parquet`: `growth_rate`, `net_inflow`
- `credit.parquet`: `max_utilization` (must be <0.30 or NULL if no cards)

**Severity Score**:
```python
severity = growth_rate  # Higher growth = more positive trajectory
```
Note: For Persona 4, higher severity is actually *better* (not financial risk)

**Edge Case**:
- If user has **no credit cards**, they automatically satisfy the utilization requirement

---

### Persona 5: Cash Flow Stressed

**Criteria** (roadmap lines 50-56):
```
ALL of:
- Checking balance <$100 on ≥30% of days in window
- Balance volatility > 1.0 (std_dev > mean)
```

**Feature Dependencies**:
- `cash_flow.parquet`: `pct_days_below_100`, `balance_volatility`

**Severity Score**:
```python
severity = pct_days_below_100  # 0.0 to 1.0
```
More days below threshold = more severe

---

### Unassigned/Stable Status

**Criteria**:
```
User does not match any of the 5 persona criteria
```

**Interpretation**: Healthy financial behavior, no immediate intervention needed

**Treatment in Epic 4**: Generic educational content or no recommendations

---

## Assignment Logic

### Assignment Algorithm

For each user, for each time window (30d, 180d):

```python
def assign_personas(user_id, window_days):
    # 1. Load features for this user + window
    features = load_features(user_id, window_days)
    
    # 2. Evaluate all 5 personas
    matched_personas = []
    
    if evaluate_persona_1(features):
        matched_personas.append({
            'persona_id': 1,
            'priority': 'CRITICAL',
            'severity': features['credit']['max_utilization']
        })
    
    if evaluate_persona_2(features):
        matched_personas.append({
            'persona_id': 2,
            'priority': 'HIGH',
            'severity': features['income']['median_pay_gap_days'] / 45.0
        })
    
    # ... continue for personas 3, 4, 5
    
    # 3. Handle no matches
    if len(matched_personas) == 0:
        return {
            'primary': None,
            'secondary': None,
            'status': 'STABLE'
        }
    
    # 4. Sort by priority, then severity
    priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
    matched_personas.sort(
        key=lambda p: (priority_order[p['priority']], -p['severity'])
    )
    
    # 5. Assign primary and secondary
    primary = matched_personas[0]
    secondary = matched_personas[1] if len(matched_personas) > 1 else None
    
    return {
        'primary': primary,
        'secondary': secondary,
        'status': 'ASSIGNED'
    }
```

### Tie-Breaking Rules

Within same priority level (e.g., Persona 2 vs Persona 5, both HIGH):
1. **Compare severity scores** (higher = primary)
2. If severity scores are equal (unlikely with float precision), use **persona_id** as stable tie-breaker (lower ID wins)

---

## Data Schema

### SQLite Table: `persona_assignments`

```sql
CREATE TABLE persona_assignments (
    assignment_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    window_days INTEGER NOT NULL,
    as_of_date DATE NOT NULL,
    
    -- Primary persona
    primary_persona_id INTEGER,          -- 1-5, NULL if unassigned
    primary_persona_name TEXT,
    primary_priority TEXT,                -- CRITICAL, HIGH, MEDIUM, LOW
    primary_severity REAL,
    
    -- Secondary persona
    secondary_persona_id INTEGER,        -- 1-5, NULL if none
    secondary_persona_name TEXT,
    secondary_priority TEXT,
    secondary_severity REAL,
    
    -- Status
    status TEXT NOT NULL,                 -- ASSIGNED, STABLE
    
    -- Audit trail (JSON)
    assignment_trace TEXT,                -- JSON with detailed reasoning
    
    -- Metadata
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE(user_id, window_days, as_of_date)
)
```

**Indexes**:
```sql
CREATE INDEX idx_persona_user_window ON persona_assignments(user_id, window_days);
CREATE INDEX idx_persona_primary ON persona_assignments(primary_persona_id);
```

---

### Parquet Schema: `persona_assignments.parquet`

```
user_id | window_days | as_of_date | primary_persona_id | primary_persona_name | primary_priority | primary_severity | secondary_persona_id | secondary_persona_name | secondary_priority | secondary_severity | status | computed_at
```

**Note**: Audit trace JSON stored in SQLite only (not in Parquet for cleaner analytics)

---

## Assignment Trace Structure

For transparency, store JSON audit trail:

```json
{
    "user_id": "user_abc123",
    "window_days": 30,
    "as_of_date": "2025-11-04",
    "evaluations": {
        "persona_1": {
            "matched": true,
            "criteria": {
                "max_utilization": 0.68,
                "threshold": 0.50,
                "interest_charges": true,
                "minimum_payment_only": false,
                "is_overdue": false
            },
            "triggered_by": ["max_utilization", "interest_charges"],
            "severity": 0.68,
            "priority": "CRITICAL"
        },
        "persona_2": {
            "matched": false,
            "criteria": {
                "median_pay_gap_days": 32,
                "threshold": 45,
                "cash_flow_buffer_months": 1.5,
                "threshold": 1.0
            },
            "triggered_by": []
        },
        "persona_3": {
            "matched": true,
            "criteria": {
                "recurring_merchant_count": 5,
                "threshold": 3,
                "monthly_recurring_spend": 75.00,
                "threshold": 50.00,
                "subscription_share": 0.12,
                "threshold": 0.10
            },
            "triggered_by": ["recurring_merchant_count", "monthly_recurring_spend", "subscription_share"],
            "severity": 0.12,
            "priority": "MEDIUM"
        },
        "persona_4": {
            "matched": false,
            "criteria": {
                "growth_rate": 0.01,
                "threshold": 0.02,
                "max_utilization": 0.68,
                "threshold": 0.30
            },
            "triggered_by": []
        },
        "persona_5": {
            "matched": false,
            "criteria": {
                "pct_days_below_100": 0.15,
                "threshold": 0.30,
                "balance_volatility": 0.85,
                "threshold": 1.0
            },
            "triggered_by": []
        }
    },
    "result": {
        "primary_persona_id": 1,
        "primary_persona_name": "High Utilization",
        "primary_reasoning": "Matched on max_utilization (68% vs 50% threshold) and interest_charges. Severity: 0.68. Priority: CRITICAL.",
        "secondary_persona_id": 3,
        "secondary_persona_name": "Subscription-Heavy",
        "secondary_reasoning": "Matched on 5 recurring merchants (vs 3 threshold), $75 monthly spend (vs $50 threshold), 12% subscription share (vs 10% threshold). Severity: 0.12. Priority: MEDIUM.",
        "status": "ASSIGNED"
    }
}
```

**Trace Purpose**:
- Operator can see exact values that triggered persona
- Debugging and validation
- User transparency (Epic 5)

---

## Module Structure

```
backend/
└── personas/
    ├── __init__.py
    ├── assign.py           # Main orchestrator
    ├── evaluators.py       # Persona evaluation logic (one function per persona)
    ├── prioritize.py       # Sorting and tie-breaking
    ├── trace.py            # Audit trail generation
    └── storage.py          # SQLite + Parquet write utilities

scripts/
└── assign_personas.py     # CLI entry point
```

---

## Persona Assignment Workflow

1. **Load Features**: Read all 5 Parquet files for specified window
2. **For Each User**:
   - Evaluate all 5 personas
   - Collect matched personas with severity scores
   - Sort by priority, then severity
   - Assign primary and secondary (or STABLE status)
   - Generate audit trace JSON
3. **Write to SQLite**: Insert into `persona_assignments` table
4. **Write to Parquet**: Export assignments for analytics
5. **Validation**: Check coverage, ensure all consented users have assignments

---

## Implementation Details

### Persona Evaluator Functions

Each persona has a dedicated evaluation function:

```python
def evaluate_persona_1(features: dict) -> tuple[bool, float]:
    """
    Persona 1: High Utilization
    Returns: (matched, severity_score)
    """
    credit = features.get('credit', {})
    
    max_util = credit.get('max_utilization', 0.0)
    interest_charges = credit.get('interest_charges_present', False)
    min_payment_only = credit.get('minimum_payment_only', False)
    is_overdue = credit.get('is_overdue', False)
    
    matched = (
        max_util >= 0.50 or
        interest_charges or
        min_payment_only or
        is_overdue
    )
    
    severity = max_util  # Use max utilization as severity score
    
    return matched, severity
```

Similar structure for Personas 2-5.

---

### Edge Cases Handling

**No Credit Cards (Persona 4)**:
```python
def evaluate_persona_4(features: dict) -> tuple[bool, float]:
    savings = features.get('savings', {})
    credit = features.get('credit', {})
    
    # Savings criteria
    growth_rate = savings.get('growth_rate', 0.0)
    net_inflow_monthly = savings.get('net_inflow', 0.0) / (window_days / 30.0)
    
    savings_ok = (growth_rate >= 0.02) or (net_inflow_monthly >= 200.0)
    
    # Credit criteria
    max_util = credit.get('max_utilization')
    
    # If max_utilization is NULL/None, user has no credit cards -> auto-pass
    credit_ok = (max_util is None) or (max_util < 0.30)
    
    matched = savings_ok and credit_ok
    severity = growth_rate
    
    return matched, severity
```

**Missing Features**:
- If a feature file doesn't have data for a user/window, treat as 0/NULL
- Log warning but continue processing

---

## Testing Strategy

### Unit Tests (≥6 for Epic 3)

1. **Persona 1 evaluation**: User with 68% utilization matches
2. **Persona 2 evaluation**: User with 60-day pay gap + 0.5 month buffer matches
3. **Persona 3 evaluation**: User with 5 recurring merchants, $75/month matches
4. **Persona 4 evaluation**: User with 3% growth rate, 15% utilization matches
5. **Persona 5 evaluation**: User with 45% low balance days, 1.2 volatility matches
6. **Tie-breaking logic**: Two HIGH priority personas, higher severity wins
7. **No credit cards**: User with no cards satisfies Persona 4 credit requirement
8. **Unassigned status**: User matching no personas gets STABLE status

### Integration Tests (≥2 for Epic 3)

1. **End-to-end assignment**: Load features → assign personas → write SQLite + Parquet
2. **Multi-window assignment**: Same user gets different personas for 30d vs 180d windows

### Validation Against Epic 1 Archetypes

Verify assignments match expected archetypes:
- High Utilizer archetype → Persona 1 (primary)
- Variable Income archetype → Persona 2 (primary)
- Subscription Heavy archetype → Persona 3 (primary)
- Savings Builder archetype → Persona 4 (primary)
- Cash Flow Stressed archetype → Persona 5 (primary)
- Stable archetype → Unassigned/STABLE status

---

## Configuration

Extend `config.json`:
```json
{
    "personas": {
        "output_db": "data/spendsense.db",
        "output_parquet": "data/features/persona_assignments.parquet",
        "windows": [30, 180],
        "as_of_date": null,
        "thresholds": {
            "persona_1": {
                "utilization_threshold": 0.50
            },
            "persona_2": {
                "pay_gap_days_threshold": 45,
                "buffer_months_threshold": 1.0
            },
            "persona_3": {
                "recurring_merchant_count_threshold": 3,
                "monthly_spend_threshold": 50.0,
                "subscription_share_threshold": 0.10
            },
            "persona_4": {
                "growth_rate_threshold": 0.02,
                "net_inflow_monthly_threshold": 200.0,
                "max_utilization_threshold": 0.30
            },
            "persona_5": {
                "pct_days_below_100_threshold": 0.30,
                "balance_volatility_threshold": 1.0
            }
        }
    }
}
```

**Note**: Thresholds configurable for tuning, but default to requirements specs.

---

## Persona Metadata Reference

For Epic 4 (recommendation engine), create lookup table:

```python
PERSONA_METADATA = {
    1: {
        "name": "High Utilization",
        "priority": "CRITICAL",
        "focus": "Reduce utilization and interest; payment planning and autopay education",
        "risk": "Debt spiral, credit damage, high interest charges"
    },
    2: {
        "name": "Variable Income Budgeter",
        "priority": "HIGH",
        "focus": "Percent-based budgets, emergency fund basics, smoothing strategies",
        "risk": "Income uncertainty plus low buffer leads to payment timing issues"
    },
    3: {
        "name": "Subscription-Heavy",
        "priority": "MEDIUM",
        "focus": "Subscription audit, cancellation/negotiation tips, bill alerts",
        "risk": "Money leak, optimization opportunity"
    },
    4: {
        "name": "Savings Builder",
        "priority": "LOW",
        "focus": "Goal setting, automation, APY optimization (HYSA/CD basics)",
        "risk": "None - positive trajectory, enrichment only"
    },
    5: {
        "name": "Cash Flow Stressed",
        "priority": "HIGH",
        "focus": "Paycheck-to-paycheck budgeting, buffer building, expense smoothing, timing strategies",
        "risk": "Overdraft risk, immediate liquidity crisis"
    }
}
```

Store in `backend/personas/metadata.py` for reference by Epic 4.

---

## Next Epic Prerequisites

**What Epic 4 Needs from Epic 3**:
- [ ] SQLite `persona_assignments` table populated with all users × 2 windows
- [ ] Parquet file `persona_assignments.parquet` exported
- [ ] Validation confirms archetype-persona alignment
- [ ] Audit traces stored in SQLite for transparency
- [ ] Persona metadata lookup available
- [ ] Assignment script runnable via `python scripts/assign_personas.py`
- [ ] Tests passing (≥8 tests)

---

## Success Criteria

Epic 3 complete when:
- [ ] All 5 personas have evaluation logic implemented
- [ ] Multi-persona tracking (primary + secondary) functional
- [ ] Severity-based tie-breaking works correctly
- [ ] Unassigned/STABLE status handles edge case users
- [ ] Both SQLite and Parquet storage operational
- [ ] Audit traces provide clear reasoning
- [ ] 100% coverage: All users have assignments (ASSIGNED or STABLE)
- [ ] ≥8 tests passing
- [ ] Decision log updated
- [ ] One-command execution: `python scripts/assign_personas.py`

---

## Design Decisions

### 1. Dual Time Windows
**Decision**: Assign personas separately for 30d and 180d  
**Rationale**: Recent behavior (30d) may differ from long-term patterns (180d), gives richer view  
**Impact**: Users can have different primary personas per window (e.g., recent stress but long-term stable)

### 2. Severity Score as Tie-Breaker
**Decision**: Use quantitative severity scores rather than fixed precedence order  
**Rationale**: More nuanced than arbitrary ordering, reflects actual financial situation  
**Impact**: Within same priority level, user with 70% utilization beats user with 55% for Persona 1

### 3. Unassigned/STABLE Status
**Decision**: Create 6th state for users matching no personas, rather than forcing assignment  
**Rationale**: Honest representation of healthy financial behavior, demonstrates system intelligence  
**Impact**: Epic 4 can send generic content or no recommendations to STABLE users

### 4. Strict "All Cards <30%" for Persona 4
**Decision**: ALL credit cards must be <30% utilization (not just average or max)  
**Rationale**: Follows requirements exactly, ensures Savings Builder has no credit concerns  
**Impact**: Users with mixed utilization (one card at 45%, others at 10%) don't qualify

### 5. Both SQLite + Parquet Storage
**Decision**: Store assignments in both formats  
**Rationale**: SQLite for fast operational lookups, Parquet for analytics/reporting  
**Impact**: Two write operations per batch, but enables flexible Epic 4/5 queries

### 6. JSON Audit Traces
**Decision**: Store detailed JSON trace in SQLite TEXT column  
**Rationale**: Flexible schema, easy to query/display, sufficient for demo scale  
**Impact**: Epic 5 operator view can parse and display reasoning

---

## Decision Log Updates Needed

After implementation, document:
- Final threshold tuning (if any deviations from defaults)
- Severity score formula refinements
- Any edge cases discovered during testing
- Secondary persona selection tie-breaking logic details

---

## Open Questions for Epic 4

1. Should recommendations prioritize **primary persona only**, or blend primary + secondary?
2. For users with different personas across windows, which window drives recommendation content?
3. Should STABLE users receive any content, or skip recommendation generation entirely?

These will be addressed in Epic 4 technical design.

---


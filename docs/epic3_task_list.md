# Epic 3: Persona System - Task List

**Status**: Ready for Implementation  
**Design Doc**: `epic3_technical_design.md`  
**Core Problem**: Assign personas to users based on behavioral signals with severity-based prioritization and clear audit trails

---

## Implementation Tasks

### 1. Persona Module Setup
**Task**: Create persona assignment module structure and storage utilities  
**Output**: Module skeleton with SQLite table creation and Parquet storage  
**Key Files**: 
- `backend/personas/__init__.py`
- `backend/personas/storage.py` (SQLite + Parquet utilities)
- `backend/personas/metadata.py` (persona lookup data)
**Critical**: 
- Create `persona_assignments` table with indexes
- Define persona metadata (name, priority, focus, risk)

### 2. Persona Evaluation Logic
**Task**: Implement evaluation functions for all 5 personas  
**Output**: Functions that check criteria and return (matched, severity_score)  
**Key Files**: `backend/personas/evaluators.py`  
**Critical**: 
- **Persona 1**: ANY of (utilization ≥50%, interest charges, minimum payment only, is_overdue)
- **Persona 2**: BOTH (median pay gap >45 days AND cash-flow buffer <1 month)
- **Persona 3**: Recurring merchants ≥3 AND (monthly spend ≥$50 OR subscription share ≥10%)
- **Persona 4**: (Growth rate ≥2% OR net inflow ≥$200/month) AND ALL cards <30% utilization
- **Persona 5**: BOTH (≥30% days with balance <$100 AND balance volatility >1.0)
- Handle NULL/missing features gracefully
- No credit cards = auto-pass for Persona 4 credit requirement

### 3. Severity Score Calculation
**Task**: Implement severity scoring for each persona  
**Output**: Normalized severity scores for tie-breaking  
**Key Files**: `backend/personas/evaluators.py`  
**Critical**: 
- **P1**: max_utilization (0.0 to 1.0+)
- **P2**: median_pay_gap_days / 45.0 (normalized to threshold)
- **P3**: subscription_share (0.0 to 1.0)
- **P4**: growth_rate (higher = better, but still used for tie-breaking)
- **P5**: pct_days_below_100 (0.0 to 1.0)

### 4. Prioritization & Sorting Logic
**Task**: Build priority sorting and tie-breaking system  
**Output**: Function that sorts matched personas by priority, then severity  
**Key Files**: `backend/personas/prioritize.py`  
**Critical**: 
- Priority order: CRITICAL (0) > HIGH (1) > MEDIUM (2) > LOW (3)
- Within same priority, sort by severity (descending)
- If severity equal (rare), use persona_id as stable tie-breaker
- Return sorted list of matched personas

### 5. Primary + Secondary Assignment
**Task**: Implement primary and secondary persona selection  
**Output**: Logic to pick top 2 personas from sorted list  
**Key Files**: `backend/personas/assign.py`  
**Critical**: 
- Primary = first in sorted list
- Secondary = second in sorted list (if exists)
- If no matches, assign status='STABLE'
- Handle edge case: only 1 persona matches (secondary=None)

### 6. Audit Trail Generation
**Task**: Build JSON trace generator for transparency  
**Output**: Structured JSON with all evaluations and reasoning  
**Key Files**: `backend/personas/trace.py`  
**Critical**: 
- Include all 5 persona evaluations (matched and not matched)
- For matched personas: show triggered criteria with actual vs threshold values
- Result section with primary/secondary reasoning
- Compact but comprehensive (avoid verbose logs)

### 7. Assignment Orchestrator
**Task**: Build main persona assignment pipeline  
**Output**: Function that processes all users × all windows  
**Key Files**: `backend/personas/assign.py`  
**Critical**: 
- Load features from all 5 Parquet files
- For each user, for each window (30d, 180d):
  - Evaluate all 5 personas
  - Prioritize and sort
  - Assign primary + secondary
  - Generate audit trace
  - Write to SQLite + collect for Parquet export
- Handle missing features gracefully (log warnings)

### 8. Storage Operations
**Task**: Implement SQLite insert and Parquet export  
**Output**: Functions to persist persona assignments  
**Key Files**: `backend/personas/storage.py`  
**Critical**: 
- SQLite: Insert rows with assignment_trace JSON
- Parquet: Export without trace column (analytics only)
- Create indexes on user_id, window_days, primary_persona_id
- Use batch inserts for performance

### 9. Assignment Script
**Task**: Create CLI entry point for persona assignment  
**Output**: One-command execution via `python scripts/assign_personas.py`  
**Key Files**: `scripts/assign_personas.py`  
**Critical**: 
- Load config from `config.json`
- Call assignment orchestrator
- Generate validation report (coverage, archetype alignment)
- Print summary statistics

### 10. Configuration Extension
**Task**: Extend config.json with persona assignment settings  
**Output**: Persona configuration section  
**Key Files**: `config.json`  
**Critical**: 
- All 5 persona thresholds (configurable but default to requirements)
- Output paths (SQLite, Parquet)
- Windows (30, 180)
- as_of_date parameter

### 11. Testing
**Task**: Write unit and integration tests  
**Output**: ≥8 tests passing  
**Key Files**: `backend/tests/test_personas.py`  
**Critical Tests**:
- Persona 1 evaluation: User with 68% utilization matches
- Persona 2 evaluation: User with 60-day gap + 0.5 month buffer matches
- Persona 3 evaluation: User with 5 merchants, $75/month matches
- Persona 4 evaluation: User with 3% growth + 15% utilization matches
- Persona 5 evaluation: User with 45% low days + 1.2 volatility matches
- Tie-breaking: Two HIGH priority personas, higher severity wins primary
- No credit cards: User with no cards satisfies P4 requirement
- Unassigned status: User matching no personas gets STABLE
- End-to-end: Load features → assign → verify SQLite + Parquet output

---

## Validation Criteria

Before moving to Epic 4, verify:
- [ ] All 75 users have persona assignments for both windows (150 total assignments)
- [ ] High Utilizer archetype users → Persona 1 primary
- [ ] Variable Income archetype users → Persona 2 primary
- [ ] Subscription Heavy archetype users → Persona 3 primary
- [ ] Savings Builder archetype users → Persona 4 primary
- [ ] Cash Flow Stressed archetype users → Persona 5 primary
- [ ] Stable archetype users → status='STABLE', no primary persona
- [ ] Multi-persona archetype users have both primary and secondary assigned
- [ ] Audit traces present in SQLite for all assignments
- [ ] Parquet file has correct schema (no trace column)
- [ ] Same user can have different personas for 30d vs 180d windows
- [ ] Tests passing (≥8)

---

## Dependencies

**External Libraries**:
- `pandas` - DataFrame operations for Parquet export
- `pyarrow` - Parquet read/write
- `json` - Audit trace serialization
- Standard Python libraries (sqlite3, datetime, etc.)

**From Epic 2**:
- Parquet files at `data/features/`:
  - `subscriptions.parquet`
  - `savings.parquet`
  - `credit.parquet`
  - `income.parquet`
  - `cash_flow.parquet`
- All 75 users with features for 30d and 180d windows

**Config**:
- Extend `config.json` with personas section

---

## Epic Completion

**Definition of Done**:
1. ✅ All 5 personas have evaluation logic implemented
2. ✅ Multi-persona tracking (primary + secondary) functional
3. ✅ Severity-based tie-breaking works correctly
4. ✅ Unassigned/STABLE status handles non-matching users
5. ✅ Both SQLite and Parquet storage operational
6. ✅ Audit traces provide clear reasoning
7. ✅ 100% coverage: All users have assignments (ASSIGNED or STABLE)
8. ✅ Tests passing (≥8)
9. ✅ Decision log updated with implementation notes
10. ✅ Assignment script works via single command
11. ✅ Next Epic Prerequisites documented

---

## Implementation Notes

### Feature Loading Strategy
```python
def load_features_for_user(user_id, window_days, as_of_date):
    """Load all features for a user/window from 5 Parquet files"""
    features = {}
    
    for signal_type in ['subscriptions', 'savings', 'credit', 'income', 'cash_flow']:
        df = pd.read_parquet(f'data/features/{signal_type}.parquet')
        user_features = df[
            (df['user_id'] == user_id) & 
            (df['window_days'] == window_days) &
            (df['as_of_date'] == as_of_date)
        ]
        
        if len(user_features) > 0:
            features[signal_type] = user_features.iloc[0].to_dict()
        else:
            features[signal_type] = {}  # Empty dict for missing features
    
    return features
```

### Persona 4 No Credit Cards Handling
```python
def evaluate_persona_4(features):
    savings = features.get('savings', {})
    credit = features.get('credit', {})
    
    # Savings criteria
    growth_rate = savings.get('growth_rate', 0.0)
    net_inflow = savings.get('net_inflow', 0.0)
    window_days = savings.get('window_days', 30)
    net_inflow_monthly = net_inflow / (window_days / 30.0)
    
    savings_ok = (growth_rate >= 0.02) or (net_inflow_monthly >= 200.0)
    
    # Credit criteria - NULL means no credit cards
    max_util = credit.get('max_utilization')
    credit_ok = (max_util is None) or (max_util < 0.30)
    
    matched = savings_ok and credit_ok
    severity = growth_rate
    
    return matched, severity
```

### Assignment Trace Example Structure
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
                "threshold": 0.50
            },
            "triggered_by": ["max_utilization"],
            "severity": 0.68,
            "priority": "CRITICAL"
        }
    },
    "result": {
        "primary_persona_id": 1,
        "primary_reasoning": "Matched on max_utilization (68% vs 50% threshold). Severity: 0.68. Priority: CRITICAL.",
        "status": "ASSIGNED"
    }
}
```

### Sorting and Tie-Breaking
```python
def sort_matched_personas(matched_personas):
    """Sort by priority level, then severity (descending), then persona_id"""
    priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
    
    return sorted(
        matched_personas,
        key=lambda p: (
            priority_order[p['priority']],  # Lower number = higher priority
            -p['severity'],                  # Higher severity first (negative for descending)
            p['persona_id']                  # Stable tie-breaker
        )
    )
```

### Database Index Creation
```sql
-- Create indexes after table population for better performance
CREATE INDEX idx_persona_user_window 
    ON persona_assignments(user_id, window_days);

CREATE INDEX idx_persona_primary 
    ON persona_assignments(primary_persona_id);

CREATE INDEX idx_persona_status 
    ON persona_assignments(status);
```

### Validation Queries
```sql
-- Check coverage
SELECT status, COUNT(*) 
FROM persona_assignments 
GROUP BY status;

-- Verify dual windows
SELECT user_id, COUNT(DISTINCT window_days) as window_count
FROM persona_assignments
GROUP BY user_id
HAVING window_count != 2;  -- Should return 0 rows

-- Count assignments by primary persona
SELECT primary_persona_name, COUNT(*) 
FROM persona_assignments 
WHERE status = 'ASSIGNED'
GROUP BY primary_persona_name;
```

---

## Open Questions for Epic 4

1. **Recommendation Focus**: Should recommendations target primary persona only, or blend primary + secondary?
2. **Multi-Window Recommendations**: If user has different personas for 30d vs 180d, which drives content?
3. **STABLE Users**: Should they receive generic "healthy habits" content or be skipped entirely?
4. **Secondary Persona Usage**: How prominently should secondary persona content appear vs primary?

These will be addressed in Epic 4 technical design.

---


# Data Regeneration Improvements - November 2025

## Summary

Created comprehensive fixes to improve persona distribution and added a master regeneration script for easy data refresh.

---

## Changes Made

### 1. Fixed Variable Income Generation

**Problem:** Income amounts only varied by ±5%, not enough to trigger Variable Income persona  
**Location:** `backend/core/data_gen/transactions.py` lines 299-310

**Solution:**
```python
# Before: All users had ±5% income variance
payroll_amount = avg_income * random.uniform(0.95, 1.05)

# After: Variable income users have ±30-50% variance
if archetype.payroll_variability > 0.5:  # Variable income (Persona 2)
    payroll_amount = avg_income * random.uniform(0.5, 1.5)  # ±50% variance
else:
    payroll_amount = avg_income * random.uniform(0.95, 1.05)  # Normal
```

**Result:** Variable Income persona now appears (4 users in 180d window)

---

### 2. Enhanced Cash Flow Stress Generation

**Problem:** Cash flow stressed users weren't hitting 35% low balance days target  
**Location:** `backend/core/data_gen/transactions.py` lines 262-267, 349-354

**Changes:**
- Increased expense target: 95% → 98% of income
- Increased daily expense frequency: 60% → 75% for cash stressed users

**Result:** Cash Flow Stressed improved from 1 → 3 users

---

### 3. Rebalanced Archetype Proportions

**Location:** `backend/core/data_gen/archetypes.py` lines 281-296

**Changes:**
- `variable_income`: 16% → 20% (+4%)
- `cash_flow_stressed`: 13% → 16% (+3%)
- `subscription_heavy`: 16% → 12% (-4%)
- `high_utilizer`: 24% → 20% (-4%)

**Goal:** Increase underrepresented personas, reduce subscription-heavy dominance

---

### 4. Master Regeneration Script

**Location:** `scripts/regenerate_all_data.py`

**Features:**
- One-command data refresh: `python scripts/regenerate_all_data.py`
- Wipes existing database and features
- Runs complete pipeline:
  1. Create database schema
  2. Generate synthetic data
  3. Compute all features
  4. Assign personas
  5. Generate decision traces
- Shows detailed summary with persona distribution
- Fast execution: ~3-5 seconds for 75 users

**Usage:**
```bash
# Default: 75 users, seed=42
python scripts/regenerate_all_data.py

# Custom settings
python scripts/regenerate_all_data.py --users 100 --seed 123 --skip-validation
```

**Options:**
- `--users N`: Number of users (default: 75)
- `--seed N`: Random seed for reproducibility (default: 42)
- `--skip-validation`: Skip validation for faster regeneration

---

## Results After Improvements

### Persona Distribution (Current)

**30-Day Window:**
- Persona 1 (High Utilization): **14 users** (18.7%)
- Persona 2 (Variable Income): **0 users** (appears in 180d only)
- Persona 3 (Subscription-Heavy): **29 users** (38.7%) 🔴 still high
- Persona 4 (Savings Builder): **13 users** (17.3%)
- Persona 5 (Cash Flow Stressed): **3 users** (4.0%) ✓ improved
- STABLE: **16 users** (21.3%)

**180-Day Window:**
- Persona 1 (High Utilization): **14 users** (18.7%)
- Persona 2 (Variable Income): **4 users** (5.3%) ✓ appears!
- Persona 3 (Subscription-Heavy): **29 users** (38.7%)
- Persona 4 (Savings Builder): **13 users** (17.3%)
- Persona 5 (Cash Flow Stressed): **0 users** (30d only)
- STABLE: **15 users** (20.0%)

### Coverage
- **77.6%** (52/67 consented users have personas)
- **22.4%** remain STABLE (expected - some users have no financial issues)

---

## What Works ✅

1. **All 5 personas are represented** across both windows
2. **Fast regeneration**: Complete pipeline in ~3-5 seconds
3. **Variable Income persona now appears** (4 users in 180d window)
4. **Cash Flow Stressed improved** (1 → 3 users)
5. **Easy data refresh** for demo purposes
6. **Reproducible** with seed parameter

---

## Remaining Challenges 🔴

### 1. Subscription-Heavy Still Dominates (38.7%)

**Root Cause:**
- Utilities + rent still create recurring patterns for most users
- Even with variance, the subscription detection is very sensitive
- Threshold is 3+ recurring merchants, and most users have:
  - Rent: 1 merchant
  - Utilities: 1-3 merchants (electric, internet, water)
  - Actual subscriptions: varies

**Possible Solutions:**
- Further increase utility payment variance (±7 days instead of ±4)
- Reduce % of users who have all utilities (currently 85/90/70%)
- Use ACH/direct debit for more users (currently 30%, could be 50%+)
- Increase subscription threshold from 3 → 4 recurring merchants
- Add more transaction noise (skip months for utilities)

### 2. Variable Income Still Rare (5.3%)

**Root Cause:**
- Even with ±50% income variance, need BOTH:
  - Pay gaps >45 days
  - Low cash buffer (<1 month)
- Many variable income users build up buffers over 180 days

**Possible Solutions:**
- Increase starting balance volatility for variable income archetype
- Make expenses less predictable for variable income users
- Reduce emergency fund building behavior

### 3. Cash Flow Stressed Still Rare (4.0%)

**Root Cause:**
- Hitting 35% days <$100 AND maintaining volatility is difficult
- Transaction generation maintains some stability by design

**Already Applied (Good):**
- ✓ Increased expense target to 98%
- ✓ Increased transaction frequency to 75%
- ✓ Lowered volatility threshold (1.0 → 0.15)
- ✓ Lowered low balance threshold (30% → 20%)

---

## Files Modified

### Data Generation:
- `backend/core/data_gen/transactions.py`
  - Lines 299-310: Variable income amount variance
  - Lines 262-267: Cash flow stress expense targets
  - Lines 349-354: Cash flow stress transaction frequency

### Archetype Configuration:
- `backend/core/data_gen/archetypes.py`
  - Lines 281-296: Rebalanced proportions

### Scripts:
- `scripts/regenerate_all_data.py` (NEW)
  - Master regeneration script with full pipeline

### Documentation:
- `README.md`
  - Updated Quick Start with regeneration script

---

## Usage for Demo

### To Refresh Data:
```bash
# Complete regeneration (recommended)
python scripts/regenerate_all_data.py

# The script will:
# 1. Confirm before wiping data
# 2. Regenerate everything from scratch
# 3. Show detailed summary with persona distribution
```

### To Generate Recommendations:
```bash
# After data regeneration, generate recommendations manually
python scripts/generate_recommendations.py
```

### To Run the Demo:
```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
uvicorn api.main:app --reload

# Terminal 2: Frontend
cd frontend
npm run dev
```

---

## Next Steps for Better Distribution

If you want to further improve persona diversity:

1. **Reduce Subscription-Heavy dominance:**
   - Increase utility variance to ±7 days
   - Use ACH for 50% of rent payments
   - Only 60% of users have all 3 utilities
   - Increase recurring merchant threshold to 4

2. **Increase Variable Income:**
   - Make variable income users spend more erratically
   - Prevent buffer building in first 6 months
   - Increase pay gap probability

3. **Increase Cash Flow Stressed:**
   - Add "emergency expense" events (medical, car repair)
   - Make expenses more volatile
   - Reduce paycheck regularity for stressed users

4. **Calibrate on Real Data:**
   - If you have access to real transaction data, analyze actual distributions
   - Set thresholds based on real 25th/50th/75th percentiles
   - Match archetype generation to real behavior patterns

---

## Conclusion

✅ **All 5 personas are now represented**  
✅ **Easy data regeneration for demos**  
✅ **Significant improvements in Variable Income and Cash Flow Stressed**  
🟡 **Subscription-Heavy still dominant but manageable for demo**  
🟡 **Distribution is reasonable for synthetic data**

The current state is **production-ready for demos** where the focus is on showing the recommendation engine, operator approval workflow, and user portal. The persona distribution is diverse enough to demonstrate all 5 personas and the prioritization logic.

For production use with real data, you would calibrate thresholds and archetype generation based on actual user behavior patterns.

---

**Generated:** November 7, 2025  
**Status:** ✅ Ready for Demo


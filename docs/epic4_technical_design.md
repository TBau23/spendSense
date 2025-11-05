# Epic 4: Recommendation Engine - Technical Design

**Status**: Ready for Implementation  
**Epic Goal**: Generate personalized recommendations with rationales  
**Dependencies**: Epic 3 complete (Persona assignments operational)

---

## Overview

Generate personalized recommendation packages for users based on their persona assignments. Each package includes pre-approved educational content, LLM-generated rationales and actionable items, and eligibility-checked partner offers. Epic 4 focuses on **generation logic only**—approval workflow and operator review will be handled in Epic 5.

---

## Requirements Summary

From `project_requirements.md` and `roadmap.md`:
- **3-5 educational items**: Persona-mapped articles/guides from pre-built content catalog
- **1-3 actionable items**: LLM-generated, user-specific next steps with data citations
- **0-2 partner offers**: Generic placeholder products with rules-based eligibility
- **Rationales**: LLM-generated "because" explanations citing concrete user metrics
- **Plain language**: No jargon, empowering tone
- **Generic templates**: Pre-approved fallback content per persona for users without approved recommendations

---

## Design Philosophy

### Hybrid Content Approach

**Educational Content**: Pre-generated, reusable, persona-mapped
- Consistent quality across all users
- Pre-approved educational material (articles, guides, tools)
- No user-specific data embedded
- Safe from compliance perspective

**Rationales & Actionable Items**: LLM-generated, situation-specific
- Personalized to user's actual financial data
- Cites specific metrics (utilization %, balance amounts, etc.)
- Requires operator review in Epic 5
- Demonstrates AI capabilities while maintaining control

**Why This Matters**: Balances personalization with efficiency. Educational content is vetted once and reused; risky content (rationales that could cross into advice) gets human review.

---

## Epic 4 Scope

**IN SCOPE**:
- ✅ Educational content catalog structure and persona mapping
- ✅ LLM integration for rationale and actionable item generation
- ✅ Partner offer catalog (generic placeholders)
- ✅ Rules-based eligibility checking
- ✅ Recommendation generation logic
- ✅ Storage schema design and basic write operations
- ✅ Handling cross-window personas (30d ≠ 180d)
- ✅ Generic template system for fallback content

**OUT OF SCOPE** (Epic 5):
- ❌ Operator approval workflow (PENDING → APPROVED/FLAGGED)
- ❌ Consent filtering (compute for all users, filter in Epic 5)
- ❌ Tone validation guardrails
- ❌ Override mechanism
- ❌ Operator UI

---

## Content Architecture

### 1. Educational Content Catalog

Pre-built library of educational resources, tagged by persona relevance.

**Structure**:
```json
{
  "content_id": "edu_credit_utilization_101",
  "title": "Understanding Credit Utilization and Your Credit Score",
  "type": "article",
  "persona_tags": [1],  // Primary relevance to Persona 1
  "secondary_tags": [4],  // May also be useful for Persona 4
  "snippet": "Credit utilization is the percentage of your available credit that you're currently using. Learn how it impacts your credit score and strategies to optimize it.",
  "content_source": "internal",  // or "external_url"
  "estimated_read_time_minutes": 5,
  "difficulty": "beginner",
  "topics": ["credit", "credit_score", "utilization"],
  "created_at": "2025-11-01"
}
```

**Catalog Organization** (`backend/recommend/content_catalog.json`):

Minimum 15-20 educational items covering all 5 personas:

**Persona 1 (High Utilization)** - 4-5 items:
- "Understanding Credit Utilization and Your Credit Score"
- "Debt Avalanche vs Debt Snowball: Which Strategy Is Right for You?"
- "How to Create a Debt Payoff Plan"
- "Credit Card Minimum Payments: The Hidden Cost"
- "Setting Up Automatic Payments to Avoid Late Fees"

**Persona 2 (Variable Income)** - 3-4 items:
- "Budgeting with Variable Income: The Percentage Method"
- "Building an Emergency Fund on Irregular Income"
- "Smoothing Cash Flow When Your Paychecks Vary"
- "Freelancer's Guide to Financial Stability"

**Persona 3 (Subscription-Heavy)** - 3-4 items:
- "The Subscription Audit: Finding and Eliminating Unused Subscriptions"
- "Negotiating Better Rates on Your Recurring Bills"
- "Setting Up Subscription Alerts and Reminders"
- "Annual vs Monthly Subscriptions: Which Saves More?"

**Persona 4 (Savings Builder)** - 3-4 items:
- "Setting SMART Savings Goals"
- "High-Yield Savings Accounts: Maximizing Your Returns"
- "Automating Your Savings for Success"
- "Understanding CDs and When to Use Them"

**Persona 5 (Cash Flow Stressed)** - 3-4 items:
- "Living Paycheck to Paycheck: Strategies for Building a Buffer"
- "Expense Timing Strategies to Avoid Overdrafts"
- "Creating a Bare-Bones Budget"
- "Small Steps to Break the Paycheck-to-Paycheck Cycle"

**Unassigned/Stable** - 1-2 items:
- "You're Doing Great: Tips to Stay on Track"
- "Optimizing Your Financial Health"

**Implementation**: Start with **titles and metadata only** for demo. Full article text can be placeholder lorem ipsum or brief summaries.

---

### 2. Partner Offer Catalog

Generic placeholder products with clear eligibility rules.

**Structure**:
```json
{
  "offer_id": "offer_bt_card_001",
  "product_type": "balance_transfer_card",
  "product_name": "Generic Balance Transfer Card",
  "short_description": "0% APR for 18 months on balance transfers",
  "persona_relevance": [1],  // Relevant to High Utilization
  "eligibility_rules": {
    "min_estimated_credit_score": 670,
    "max_credit_utilization": 0.85,  // Don't offer if utilization is too high (already maxed out)
    "min_credit_card_balance": 500,  // Must have debt to transfer
    "max_existing_cards": 6  // Too many cards already
  },
  "benefits": [
    "Save on interest charges during promotional period",
    "Consolidate multiple balances",
    "No annual fee (first year)"
  ],
  "disclaimer": "This is educational content, not financial advice. Consult a licensed advisor for personalized guidance."
}
```

**Catalog** (`backend/recommend/partner_offers.json`):

**Persona 1 (High Utilization)**:
- Balance Transfer Card (0% APR 18mo)
- Debt Consolidation Loan (generic)

**Persona 2 (Variable Income)**:
- Budgeting App (free tier)
- Income Smoothing Tool

**Persona 3 (Subscription-Heavy)**:
- Subscription Management Service
- Budgeting App (subscription tracker feature)

**Persona 4 (Savings Builder)**:
- High-Yield Savings Account (4.5% APY)
- Certificate of Deposit (generic)

**Persona 5 (Cash Flow Stressed)**:
- Overdraft Protection Service
- Low-Fee Checking Account

**Total**: 8-10 offers covering common use cases

---

### 3. Generic Templates (Pre-Approved Fallback)

For users who don't yet have operator-approved personalized recommendations (or flagged recommendations).

**Structure**: Same as recommendation package but without user-specific data citations.

```json
{
  "template_id": "generic_persona_1",
  "persona_id": 1,
  "persona_name": "High Utilization",
  "status": "PRE_APPROVED",
  "educational_content": [
    // References to content_catalog items
    "edu_credit_utilization_101",
    "edu_debt_payoff_strategies",
    "edu_minimum_payment_trap"
  ],
  "actionable_items": [
    {
      "text": "Review your credit card statements to identify which cards have the highest interest rates",
      "rationale": "Focusing on high-interest debt first can help you save the most money on interest charges.",
      "generic": true  // No user-specific data
    }
  ],
  "partner_offers": [
    "offer_bt_card_001"
  ],
  "disclaimer": "This is educational content, not financial advice. Consult a licensed advisor for personalized guidance."
}
```

**Storage**: `backend/recommend/generic_templates.json` (5 templates, one per persona)

**Note**: Epic 5 will implement logic to serve generic templates when no approved personalized recommendations exist.

---

## LLM Integration

### Use Cases

LLM generates **two types of content**:

1. **Rationales**: "Because" explanations for why educational content or offers are relevant
2. **Actionable Items**: Specific next steps based on user data

### Prompt Engineering

**Rationale Prompt Template**:
```
You are a financial education assistant. Generate a clear, empowering rationale for why the following recommendation is relevant to this user.

User Context:
- Primary Persona: {persona_name}
- Key Metrics: {metrics_json}

Recommendation:
- Type: {recommendation_type}
- Title: {recommendation_title}

Guidelines:
1. Cite specific user data (utilization %, balance amounts, transaction counts)
2. Use empowering, non-judgmental language
3. Focus on benefits and opportunities, not problems
4. Keep under 100 words
5. Avoid words like "overspending", "bad", "poor"
6. Use "we noticed", "you could", "this might help"

Generate the rationale:
```

**Actionable Item Prompt Template**:
```
You are a financial education assistant. Generate 1-3 specific, actionable next steps for a user with the following financial situation.

User Context:
- Primary Persona: {persona_name}
- Key Metrics: {metrics_json}

Guidelines:
1. Make actions specific and measurable (e.g., "Pay $150 extra toward...", not "Pay more")
2. Cite actual user data in rationale
3. Focus on small, achievable steps
4. Use empowering language
5. Keep each action under 50 words
6. Avoid financial advice (no "you should", use "you might consider")

Generate actionable items:
```

**Example Persona-Specific Metrics JSON** (Persona 1):
```json
{
  "persona": "High Utilization",
  "credit_cards": [
    {
      "last_4": "4523",
      "utilization": 0.68,
      "balance": 3400,
      "limit": 5000,
      "estimated_monthly_interest": 87
    }
  ],
  "max_utilization": 0.68,
  "total_credit_balance": 3400,
  "interest_charges_present": true
}
```

### LLM Configuration

**Provider**: OpenAI (gpt-4o-mini or gpt-3.5-turbo for cost efficiency)  
**Alternative**: Anthropic Claude, or any LLM API with JSON support

**Configuration** (`config.json`):
```json
{
  "llm": {
    "provider": "openai",
    "model": "gpt-4o-mini",
    "temperature": 0.7,
    "max_tokens": 200,
    "timeout_seconds": 10
  }
}
```

**Error Handling**:
- LLM timeout → Fall back to template-based rationales
- LLM error → Log warning, use generic templates
- Invalid JSON response → Parse and sanitize

---

## Eligibility System

### Rules-Based Eligibility Checker

For each partner offer, check if user meets criteria.

**Eligibility Rules Framework**:

```python
def check_eligibility(user_id: str, offer: dict, features: dict) -> tuple[bool, dict]:
    """
    Returns: (eligible: bool, criteria_details: dict)
    """
    rules = offer['eligibility_rules']
    results = {}
    
    # Credit score estimation (from utilization heuristics)
    estimated_score = estimate_credit_score(features['credit'])
    results['estimated_credit_score'] = estimated_score
    
    if 'min_estimated_credit_score' in rules:
        results['min_credit_score_met'] = estimated_score >= rules['min_estimated_credit_score']
    
    # Credit utilization checks
    if 'max_credit_utilization' in rules:
        results['utilization_check'] = features['credit']['max_utilization'] <= rules['max_credit_utilization']
    
    # Balance/debt checks
    if 'min_credit_card_balance' in rules:
        results['has_sufficient_balance'] = features['credit']['total_balance'] >= rules['min_credit_card_balance']
    
    # Income checks (if offer requires minimum income)
    if 'min_monthly_income' in rules:
        avg_income = features['income']['avg_monthly_income']
        results['income_met'] = avg_income >= rules['min_monthly_income']
    
    # Existing account checks
    if 'exclude_if_has_account_type' in rules:
        # Check if user already has this type of account
        results['no_existing_account'] = not has_account_type(user_id, rules['exclude_if_has_account_type'])
    
    # All criteria must pass
    eligible = all(results.values())
    
    return eligible, results
```

**Credit Score Estimation Heuristics** (for demo purposes):
```python
def estimate_credit_score(credit_features: dict) -> int:
    """
    Rough estimation based on utilization and payment behavior.
    NOT accurate, just for demo eligibility checks.
    """
    base_score = 750
    
    # Utilization penalty
    max_util = credit_features.get('max_utilization', 0)
    if max_util >= 0.80:
        base_score -= 100
    elif max_util >= 0.50:
        base_score -= 50
    elif max_util >= 0.30:
        base_score -= 20
    
    # Payment behavior
    if credit_features.get('is_overdue'):
        base_score -= 80
    
    if credit_features.get('minimum_payment_only'):
        base_score -= 30
    
    return max(300, min(850, base_score))  # Clamp to 300-850 range
```

---

## Recommendation Generation Workflow

### High-Level Flow

```
1. Load persona assignments for user (both 30d and 180d windows)
2. Determine primary persona(s) to target
3. Select educational content from catalog (3-5 items)
4. Generate LLM rationales for each educational item
5. Generate LLM actionable items (1-3 items)
6. Check partner offer eligibility (0-2 offers)
7. Assemble recommendation package
8. Store in SQLite + Parquet
```

### Cross-Window Persona Handling

**Scenario**: User has different personas for 30d vs 180d windows

**Example**:
- 30d window: Persona 5 (Cash Flow Stressed)
- 180d window: Persona 1 (High Utilization)

**Strategy**: Include educational content relevant to **both personas**
- 2-3 items for primary 30d persona (recent behavior, more urgent)
- 1-2 items for 180d persona (long-term pattern)

**Rationale**: User's recent cash flow stress may be exacerbated by long-term high utilization. Addressing both gives holistic picture.

**Implementation**:
```python
def determine_target_personas(assignments_30d, assignments_180d):
    """
    Returns list of persona_ids to target, prioritized.
    """
    personas = []
    
    primary_30d = assignments_30d['primary_persona_id']
    primary_180d = assignments_180d['primary_persona_id']
    
    if primary_30d == primary_180d:
        # Same persona both windows - focus entirely on it
        personas = [primary_30d]
    else:
        # Different personas - include both, prioritize 30d (recent behavior)
        personas = [primary_30d, primary_180d]
    
    return personas
```

---

## Data Schema

### SQLite Tables

#### 1. `recommendations` Table
```sql
CREATE TABLE recommendations (
    recommendation_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    window_30d_persona_id INTEGER,
    window_180d_persona_id INTEGER,
    target_personas TEXT,  -- JSON array of targeted persona IDs
    
    -- Metadata
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    llm_model TEXT,  -- e.g., "gpt-4o-mini"
    generation_latency_seconds REAL,
    
    -- Counts
    educational_item_count INTEGER,
    actionable_item_count INTEGER,
    partner_offer_count INTEGER,
    
    FOREIGN KEY (user_id) REFERENCES users(user_id)
)
```

#### 2. `recommendation_items` Table
```sql
CREATE TABLE recommendation_items (
    item_id TEXT PRIMARY KEY,
    recommendation_id TEXT NOT NULL,
    item_type TEXT NOT NULL,  -- 'educational', 'actionable', 'partner_offer'
    item_order INTEGER,  -- Display order
    
    -- Educational content (if type='educational')
    content_id TEXT,
    content_title TEXT,
    content_snippet TEXT,
    
    -- Actionable items (if type='actionable')
    action_text TEXT,
    rationale TEXT,
    data_cited TEXT,  -- JSON with cited metrics
    generated_by TEXT,  -- 'llm' or 'template'
    
    -- Partner offers (if type='partner_offer')
    offer_id TEXT,
    offer_title TEXT,
    offer_description TEXT,
    eligibility_passed BOOLEAN,
    eligibility_details TEXT,  -- JSON
    why_relevant TEXT,  -- LLM-generated relevance explanation
    
    FOREIGN KEY (recommendation_id) REFERENCES recommendations(recommendation_id)
)
```

#### 3. `generic_templates` Table
```sql
CREATE TABLE generic_templates (
    template_id TEXT PRIMARY KEY,
    persona_id INTEGER NOT NULL,
    persona_name TEXT,
    status TEXT DEFAULT 'PRE_APPROVED',
    
    -- Template content stored as JSON
    template_content TEXT,  -- JSON structure matching recommendation package
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

#### 4. `content_catalog` Table
```sql
CREATE TABLE content_catalog (
    content_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    content_type TEXT,  -- 'article', 'video', 'tool', 'guide'
    snippet TEXT,
    persona_tags TEXT,  -- JSON array
    topics TEXT,  -- JSON array
    estimated_read_time_minutes INTEGER,
    difficulty TEXT,  -- 'beginner', 'intermediate', 'advanced'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

#### 5. `partner_offers` Table
```sql
CREATE TABLE partner_offers (
    offer_id TEXT PRIMARY KEY,
    product_type TEXT,
    product_name TEXT,
    short_description TEXT,
    persona_relevance TEXT,  -- JSON array
    eligibility_rules TEXT,  -- JSON
    benefits TEXT,  -- JSON array
    disclaimer TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Indexes**:
```sql
CREATE INDEX idx_recommendations_user ON recommendations(user_id);
CREATE INDEX idx_rec_items_rec_id ON recommendation_items(recommendation_id);
CREATE INDEX idx_content_persona ON content_catalog(persona_tags);
CREATE INDEX idx_offers_persona ON partner_offers(persona_relevance);
```

---

### Parquet Schema

**`data/features/recommendations.parquet`**:
```
user_id | recommendation_id | generated_at | window_30d_persona_id | window_180d_persona_id | target_personas_json | educational_count | actionable_count | offer_count | generation_latency_seconds
```

**Purpose**: Analytics and reporting (e.g., coverage metrics)

---

## Module Structure

```
backend/
└── recommend/
    ├── __init__.py
    ├── generator.py          # Main orchestrator
    ├── content_selector.py   # Educational content selection logic
    ├── llm_client.py         # LLM API integration
    ├── prompts.py            # Prompt templates
    ├── eligibility.py        # Rules-based eligibility checking
    ├── templates.py          # Generic template management
    ├── storage.py            # SQLite + Parquet write utilities
    ├── content_catalog.json  # Educational content metadata
    ├── partner_offers.json   # Partner offer definitions
    └── generic_templates.json # Pre-approved templates

scripts/
└── generate_recommendations.py  # CLI entry point
```

---

## Generation Workflow Implementation

### Main Orchestrator Logic

```python
def generate_recommendation(user_id: str, as_of_date: Optional[str] = None) -> dict:
    """
    Generate recommendation package for a user.
    """
    # 1. Load persona assignments
    assignments_30d = load_persona_assignment(user_id, window_days=30, as_of_date=as_of_date)
    assignments_180d = load_persona_assignment(user_id, window_days=180, as_of_date=as_of_date)
    
    # 2. Handle unassigned/stable users
    if assignments_30d['status'] == 'STABLE' and assignments_180d['status'] == 'STABLE':
        return generate_stable_user_content(user_id)
    
    # 3. Determine target personas
    target_personas = determine_target_personas(assignments_30d, assignments_180d)
    
    # 4. Load features for context
    features = load_all_features(user_id, as_of_date=as_of_date)
    
    # 5. Select educational content (3-5 items)
    educational_items = select_educational_content(
        target_personas=target_personas,
        count=5 if len(target_personas) == 1 else 4
    )
    
    # 6. Generate rationales for educational items (LLM)
    for item in educational_items:
        item['rationale'] = generate_educational_rationale(
            user_id=user_id,
            persona=target_personas[0],
            content=item,
            features=features
        )
    
    # 7. Generate actionable items (LLM)
    actionable_items = generate_actionable_items(
        user_id=user_id,
        personas=target_personas,
        features=features,
        count=min(3, len(target_personas) + 1)
    )
    
    # 8. Check partner offer eligibility (0-2 offers)
    partner_offers = select_eligible_offers(
        user_id=user_id,
        personas=target_personas,
        features=features,
        max_offers=2
    )
    
    # 9. Generate relevance explanations for offers (LLM)
    for offer in partner_offers:
        offer['why_relevant'] = generate_offer_rationale(
            user_id=user_id,
            persona=target_personas[0],
            offer=offer,
            features=features
        )
    
    # 10. Assemble package
    recommendation = {
        'recommendation_id': generate_id(),
        'user_id': user_id,
        'window_30d_persona_id': assignments_30d['primary_persona_id'],
        'window_180d_persona_id': assignments_180d['primary_persona_id'],
        'target_personas': target_personas,
        'educational_content': educational_items,
        'actionable_items': actionable_items,
        'partner_offers': partner_offers,
        'generated_at': datetime.now().isoformat(),
        'llm_model': config['llm']['model']
    }
    
    # 11. Store in SQLite + Parquet
    store_recommendation(recommendation)
    
    return recommendation
```

---

## Example Outputs

### Example 1: Persona 1 (High Utilization)

**User Context**:
- Visa ending in 4523: 68% utilization ($3,400 of $5,000 limit)
- Mastercard ending in 7821: 82% utilization ($4,100 of $5,000 limit)
- Interest charges present: $87/month

**Generated Recommendation Package**:

```json
{
  "recommendation_id": "rec_abc123",
  "user_id": "user_456",
  "window_30d_persona_id": 1,
  "window_180d_persona_id": 1,
  "target_personas": [1],
  
  "educational_content": [
    {
      "content_id": "edu_credit_utilization_101",
      "title": "Understanding Credit Utilization and Your Credit Score",
      "snippet": "Credit utilization is the percentage of your available credit...",
      "rationale": "We noticed your credit card utilization is currently at 68-82% across your cards. This guide explains how bringing utilization below 30% could help improve your credit score and save on interest charges."
    },
    {
      "content_id": "edu_debt_avalanche",
      "title": "Debt Avalanche vs Debt Snowball: Which Strategy Is Right for You?",
      "rationale": "With interest charges of approximately $87/month across your cards, choosing an effective payoff strategy could save you hundreds in interest over time."
    },
    {
      "content_id": "edu_autopay",
      "title": "Setting Up Automatic Payments to Avoid Late Fees",
      "rationale": "Automating at least your minimum payments can help you avoid late fees and protect your credit score while you work on paying down your balances."
    }
  ],
  
  "actionable_items": [
    {
      "text": "Consider paying an extra $200 toward your Mastercard ending in 7821 to bring utilization below 80%",
      "rationale": "Your Mastercard is currently at 82% utilization ($4,100 of $5,000 limit). Bringing this below 80% is a manageable first step that could improve your credit profile.",
      "data_cited": {
        "account_last_4": "7821",
        "current_utilization": 0.82,
        "current_balance": 4100,
        "credit_limit": 5000
      }
    },
    {
      "text": "Review your monthly statements to identify which card has the highest APR, then focus extra payments there first",
      "rationale": "This debt avalanche approach helps you save the most on interest charges over time. With $87/month currently going to interest, this strategy could reduce that amount significantly."
    }
  ],
  
  "partner_offers": [
    {
      "offer_id": "offer_bt_card_001",
      "product_name": "Generic Balance Transfer Card",
      "description": "0% APR for 18 months on balance transfers",
      "eligibility_passed": true,
      "eligibility_details": {
        "estimated_credit_score": 680,
        "min_required": 670,
        "utilization_check": true,
        "has_balance_to_transfer": true
      },
      "why_relevant": "This balance transfer offer could help you save on the approximately $87 you're currently paying in monthly interest charges, giving you 18 months to pay down your balance without accruing additional interest."
    }
  ]
}
```

---

### Example 2: Cross-Window Personas

**User Context**:
- 30d window: Persona 5 (Cash Flow Stressed) - 42% of days below $100, volatility 1.3
- 180d window: Persona 1 (High Utilization) - 58% avg utilization, interest charges

**Generated Recommendation Package**:

```json
{
  "recommendation_id": "rec_xyz789",
  "user_id": "user_789",
  "window_30d_persona_id": 5,
  "window_180d_persona_id": 1,
  "target_personas": [5, 1],
  
  "educational_content": [
    {
      "content_id": "edu_paycheck_to_paycheck",
      "title": "Living Paycheck to Paycheck: Strategies for Building a Buffer",
      "rationale": "We noticed your checking account balance dropped below $100 on 42% of days in the past month. This guide offers practical strategies to build a small buffer and reduce financial stress."
    },
    {
      "content_id": "edu_expense_timing",
      "title": "Expense Timing Strategies to Avoid Overdrafts",
      "rationale": "With frequent low balances, timing your bill payments strategically around paydays could help you avoid overdraft fees."
    },
    {
      "content_id": "edu_credit_utilization_101",
      "title": "Understanding Credit Utilization and Your Credit Score",
      "rationale": "Over the past 6 months, your credit card utilization has averaged 58%. Understanding how this impacts your finances could help you make strategic choices about debt paydown."
    },
    {
      "content_id": "edu_debt_payoff_strategies",
      "title": "How to Create a Debt Payoff Plan",
      "rationale": "Balancing immediate cash flow needs with longer-term debt reduction can be challenging. This guide shows how to create a sustainable plan."
    }
  ],
  
  "actionable_items": [
    {
      "text": "Try to set aside $50 from your next paycheck before paying bills to start building a small cash buffer",
      "rationale": "Even a small buffer of $50-100 can help break the cycle of low balances and provide breathing room for unexpected expenses.",
      "data_cited": {
        "pct_days_below_100": 0.42,
        "min_balance_30d": 12,
        "avg_balance_30d": 245
      }
    },
    {
      "text": "List all your recurring bills and their due dates to align them with your pay schedule",
      "rationale": "With variable cash flow, strategic timing of bill payments could help you maintain higher average balances throughout the month."
    }
  ],
  
  "partner_offers": [
    {
      "offer_id": "offer_overdraft_protection",
      "product_name": "Generic Overdraft Protection Service",
      "description": "Link your checking to savings to avoid overdraft fees",
      "eligibility_passed": true,
      "why_relevant": "Given that your checking balance frequently drops below $100, overdraft protection could help you avoid costly fees while you work on building your cash buffer."
    }
  ]
}
```

---

## Testing Strategy

### Unit Tests (≥8 for Epic 4)

1. **Content selection**: Given Persona 1, select 3-5 relevant educational items from catalog
2. **Eligibility check**: User with 68% utilization passes balance transfer card eligibility
3. **Eligibility check**: User with 92% utilization fails balance transfer card (too high)
4. **Credit score estimation**: User with high utilization gets estimated score <700
5. **Cross-window persona targeting**: User with different 30d/180d personas gets content for both
6. **LLM rationale generation**: Mock LLM call returns properly formatted rationale
7. **LLM error handling**: When LLM times out, system falls back to template
8. **Stable user handling**: User with STABLE status gets generic template

### Integration Tests (≥3 for Epic 4)

1. **End-to-end generation**: Load persona → generate recommendation → store in SQLite + Parquet
2. **Multi-user batch**: Generate recommendations for 10 users, validate all succeed
3. **Cross-window integration**: User with different personas gets blended content

### Validation

**Coverage Checks**:
- All users with ASSIGNED status get recommendations
- All recommendations have 3-5 educational items
- All recommendations have 1-3 actionable items
- All recommendations with eligible offers have rationales

**Quality Checks** (manual review of sample):
- Rationales cite actual user data
- Language is empowering, not judgmental
- Actionable items are specific and measurable

---

## Configuration

Extend `config.json`:
```json
{
  "recommendations": {
    "output_db": "data/spendsense.db",
    "output_parquet": "data/features/recommendations.parquet",
    "content_catalog_path": "backend/recommend/content_catalog.json",
    "partner_offers_path": "backend/recommend/partner_offers.json",
    "generic_templates_path": "backend/recommend/generic_templates.json",
    
    "content_selection": {
      "educational_items_min": 3,
      "educational_items_max": 5,
      "actionable_items_min": 1,
      "actionable_items_max": 3,
      "partner_offers_max": 2
    },
    
    "cross_window_strategy": {
      "primary_weight": 0.6,
      "secondary_weight": 0.4
    }
  },
  
  "llm": {
    "provider": "openai",
    "model": "gpt-4o-mini",
    "api_key_env": "OPENAI_API_KEY",
    "temperature": 0.7,
    "max_tokens": 200,
    "timeout_seconds": 10,
    "retry_attempts": 2
  },
  
  "eligibility": {
    "credit_score_estimation_enabled": true,
    "strict_mode": false
  }
}
```

---

## Implementation Phases

### Phase 1: Catalog Setup (Days 1-2)
- Create content catalog JSON with 15-20 educational items
- Create partner offers JSON with 8-10 generic products
- Create generic templates JSON (5 templates)
- Populate SQLite tables

### Phase 2: Selection Logic (Days 2-3)
- Implement content selection based on persona tags
- Implement eligibility checking for partner offers
- Implement cross-window persona blending

### Phase 3: LLM Integration (Days 3-4)
- Set up OpenAI client
- Implement prompt templates
- Implement rationale generation for educational items
- Implement actionable item generation
- Implement offer relevance explanation generation
- Add error handling and fallbacks

### Phase 4: Storage & Assembly (Day 5)
- Implement recommendation package assembly
- Implement SQLite write operations
- Implement Parquet export
- End-to-end generation workflow

### Phase 5: Testing (Day 6)
- Unit tests for all components
- Integration tests for full workflow
- Manual validation of sample outputs

---

## Next Epic Prerequisites

**What Epic 5 Needs from Epic 4**:
- [ ] Content catalog populated with 15-20 educational items
- [ ] Partner offers catalog with 8-10 generic products
- [ ] Generic templates created for all 5 personas (+ stable)
- [ ] LLM integration operational with error handling
- [ ] Eligibility checking functional with credit score estimation
- [ ] SQLite tables (`recommendations`, `recommendation_items`, etc.) populated
- [ ] Parquet file `recommendations.parquet` exported
- [ ] Generation script runnable via `python scripts/generate_recommendations.py`
- [ ] Tests passing (≥11 tests)
- [ ] Sample recommendations validated for quality

---

## Success Criteria

Epic 4 complete when:
- [ ] Educational content catalog with ≥15 items created
- [ ] Partner offer catalog with ≥8 products created
- [ ] Generic templates for all personas created
- [ ] LLM generates rationales and actionable items successfully
- [ ] Eligibility checking filters offers appropriately
- [ ] Cross-window persona handling works (different personas get blended content)
- [ ] All ASSIGNED users have generated recommendations
- [ ] Stable users have generic template content
- [ ] Storage operational (SQLite + Parquet)
- [ ] ≥11 tests passing
- [ ] Decision log updated
- [ ] One-command execution: `python scripts/generate_recommendations.py`

---

## Design Decisions

### 1. Hybrid Content Strategy
**Decision**: Pre-approved educational catalog + LLM-generated rationales/actions  
**Rationale**: Balances personalization with consistency; risky content (LLM) gets operator review  
**Impact**: Two-tier content system, operator reviews rationales in Epic 5

### 2. Generic Placeholder Products
**Decision**: Don't use real financial products, create generic placeholders  
**Rationale**: Demo focuses on workflow, not product accuracy; avoids partnership/legal complexity  
**Impact**: Partner offers have descriptive names like "Generic Balance Transfer Card"

### 3. Credit Score Estimation
**Decision**: Use simple heuristics to estimate credit score from utilization/payment data  
**Rationale**: No real credit data available; estimation enables eligibility checks  
**Impact**: `eligibility.py` has estimation logic, documented as "demo only, not accurate"

### 4. Cross-Window Persona Blending
**Decision**: When 30d ≠ 180d personas, include content for both (weighted toward 30d)  
**Rationale**: Recent behavior (30d) is more urgent, but long-term patterns provide context  
**Impact**: Content selection logic considers multiple personas, prioritizes primary

### 5. Stable User Handling
**Decision**: Generate minimal "you're doing well" generic content for stable users  
**Rationale**: Positive reinforcement, demonstrates system doesn't force recommendations  
**Impact**: Generic template for stable users differs from persona-specific templates

### 6. No Approval Status in Epic 4
**Decision**: Epic 4 generates and stores recommendations, Epic 5 adds approval workflow  
**Rationale**: Clean separation of concerns; generation logic independent of review process  
**Impact**: All recommendations implicitly "pending review" until Epic 5 adds status field

### 7. LLM Timeouts and Fallbacks
**Decision**: If LLM fails, fall back to template-based rationales  
**Rationale**: Demo should never fail due to LLM API issues  
**Impact**: Template library for rationales, graceful degradation

---

## Open Questions for Epic 5

1. Should Epic 5 add a `status` column to `recommendations` table (PENDING_REVIEW, APPROVED, FLAGGED)?
2. How should the operator override mechanism work—edit existing items or replace entire package?
3. For flagged recommendations, should user see generic template immediately, or nothing until operator approves?

---

## Decision Log Updates Needed

After implementation, document:
- Final content catalog structure and categorization approach
- LLM prompt engineering refinements
- Eligibility rule tuning (credit score thresholds, etc.)
- Any challenges with cross-window persona blending
- Rationale quality assessment (manual review findings)

---


**From Plaid to Personalized Learning**

An explainable, consent-aware system that detects behavioral patterns from transaction data, assigns personas, and delivers personalized financial education with clear guardrails.

## Technology Stack

- **Backend**: Python 3.11+, FastAPI, SQLite, Parquet
- **Frontend**: React 18+, Vite, Tailwind CSS
- **AI**: OpenAI GPT-4o-mini (content generation only; all logic is rules-based)

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- OpenAI API key (for Epic 4+ recommendation generation)

### Installation

```bash
# Clone repository
cd /path/to/spendSense

# Backend setup
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install

# Environment variables
export OPENAI_API_KEY="your-api-key-here"
```

---

## Running the System

### Epic 1-4: Data Generation → Recommendations

```bash
# Activate backend virtual environment
source backend/venv/bin/activate

# 1. Generate synthetic data (Epic 1)
python scripts/generate_data.py

# 2. Compute behavioral features (Epic 2)
python scripts/compute_features.py

# 3. Assign personas (Epic 3)
python scripts/assign_personas.py

# 4. Generate recommendations (Epic 4)
python scripts/generate_recommendations.py
```

### Epic 5: Operator Dashboard

**Terminal 1 - FastAPI Backend**:
```bash
cd /path/to/spendSense
source backend/venv/bin/activate
python -m uvicorn backend.api.main:app --reload --port 8000
```

**Terminal 2 - React Frontend**:
```bash
cd /path/to/spendSense/frontend
npm run dev
```

**Access**:
- **Operator Dashboard**: http://localhost:5173/operator
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

---

## Operator Dashboard Features

### Main Dashboard
- **Aggregate Metrics**: Total users, pending recommendations, approval rate, coverage
- **User List**: Filterable by persona, status, sortable
- **Visual Indicators**: Pending recommendations highlighted

### User Detail View
- **Left Panel**: User metrics (personas, key features, accounts, recommendation counts)
- **Center Panel**: Recommendation cards (educational content, actionable items, partner offers)
- **Right Panel**: Decision traces (why persona assigned, why content selected)

### Actions
- **Approve**: Mark recommendation as deliverable to user
- **Flag**: Block recommendation with required notes
- **Override**: (Coming in Epic 6) Edit content before approving

---

## Testing

### Run All Tests
```bash
# Backend tests
python -m pytest backend/tests/ -v

# Epic 5 guardrails tests specifically
python -m pytest backend/tests/test_guardrails.py -v
```

### Test Coverage
- Epic 1: Data generation and validation
- Epic 2: Feature computation
- Epic 3: Persona assignment
- Epic 4: Recommendation generation (coming)
- Epic 5: Guardrails, consent, approval workflow (18 tests)

---

## Database Migrations

If you need to add Epic 5 status fields to existing database:

```bash
python -m backend.storage.migrations
```

---

## API Endpoints

### Operator Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/operator/users` | List consented users (filterable) |
| GET | `/api/operator/users/{user_id}` | User detail with metrics |
| GET | `/api/operator/users/{user_id}/recommendations` | User's recommendations |
| GET | `/api/operator/recommendations/{rec_id}` | Full recommendation with items |
| POST | `/api/operator/recommendations/{rec_id}/approve` | Approve recommendation |
| POST | `/api/operator/recommendations/{rec_id}/flag` | Flag recommendation |
| GET | `/api/operator/traces/{user_id}` | Decision traces |
| GET | `/api/operator/metrics` | Aggregate metrics |

**Interactive Docs**: http://localhost:8000/docs

---

## Project Structure

```
spendSense/
├── backend/
│   ├── core/data_gen/      # Synthetic data generation (Epic 1)
│   ├── features/           # Signal detection (Epic 2)
│   ├── personas/           # Persona assignment (Epic 3)
│   ├── recommend/          # Recommendation engine (Epic 4)
│   ├── guardrails/         # Consent, metrics (Epic 5)
│   ├── api/                # FastAPI endpoints (Epic 5)
│   ├── storage/            # Database utilities
│   └── tests/              # Test suite
├── frontend/
│   ├── src/
│   │   ├── api/            # API client
│   │   ├── components/     # React components
│   │   └── pages/          # Dashboard pages
├── data/
│   ├── spendsense.db       # SQLite database
│   └── features/           # Parquet feature files
├── docs/
│   ├── decision_log.md     # Architecture decisions
│   ├── epic[1-5]_technical_design.md
│   └── epic[1-5]_task_list.md
├── scripts/                # CLI utilities
└── config.json             # Configuration
```

---

## Personas

1. **High Utilization** (Persona 1): Credit utilization ≥50% or overdue/minimum-payment-only
2. **Variable Income** (Persona 2): Median pay gap >45 days + cash buffer <1 month
3. **Subscription-Heavy** (Persona 3): ≥3 recurring merchants + significant recurring spend
4. **Savings Builder** (Persona 4): Positive savings growth + low credit utilization
5. **Cash Flow Stressed** (Persona 5): Checking balance frequently <$100 + high volatility

---

## Configuration

Key settings in `config.json`:

```json
{
  "data_generation": {
    "user_count": 75,
    "consent_ratio": 0.9  // 90% of users consent
  },
  "llm": {
    "model": "gpt-4o-mini",
    "temperature": 0.7
  },
  "api": {
    "port": 8000,
    "cors_origins": ["http://localhost:5173"]
  }
}
```

---

## Compliance & Guardrails

- **Consent-First**: Non-consented users are filtered from all processing
- **Human-in-the-Loop**: Operator reviews all recommendations before delivery
- **No Financial Advice**: All content includes disclaimer
- **Explainable**: Every recommendation cites specific user data
- **Tone Controls**: Manual review ensures empowering, non-judgmental language



## License

Demo project for educational purposes.

---

## Documentation

- **Architecture**: See `agentPlanning/roadmap.md`
- **Requirements**: See `agentPlanning/project_requirements.md`
- **Design Decisions**: See `docs/decision_log.md`
- **Epic Details**: See `docs/epic[1-5]_technical_design.md`


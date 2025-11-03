# SpendSense

**From Plaid to Personalized Learning**

An explainable, consent-aware system that detects behavioral patterns from transaction data, assigns personas, and delivers personalized financial education with strict compliance guardrails.

## Project Overview

SpendSense is a demo platform that demonstrates how financial institutions can:
- Process Plaid-style transaction data
- Detect behavioral signals (subscriptions, savings, credit utilization, income stability)
- Assign users to financial personas
- Generate personalized educational recommendations
- Enforce strict compliance and consent requirements

**⚠️ Disclaimer:** This is educational content, not financial advice. This is a demo/prototype project, not production software.

## Tech Stack

- **Backend:** Python, FastAPI, SQLAlchemy, SQLite
- **Frontend:** React, Vite, React Router
- **Optional:** OpenAI API for LLM-generated recommendations

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm or yarn

### Backend Setup

1. **Navigate to backend directory:**
```bash
cd backend
```

2. **Create and activate virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables (optional):**
```bash
cp .env.example .env
# Add your OpenAI API key if using LLM features
```

5. **Start the FastAPI server:**
```bash
uvicorn api.main:app --reload
```

The API will be available at `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

### Frontend Setup

1. **Navigate to frontend directory:**
```bash
cd frontend
```

2. **Install dependencies:**
```bash
npm install
```

3. **Start development server:**
```bash
npm run dev
```

The app will be available at `http://localhost:5173`

## Project Structure

```
spendsense/
├── backend/
│   ├── api/                    # FastAPI routes
│   ├── core/
│   │   ├── data_gen/           # Synthetic data generator
│   │   ├── signals/            # Feature detection
│   │   ├── personas/           # Assignment logic
│   │   ├── engine/             # Recommendation engine
│   │   └── guardrails/         # Compliance checks
│   ├── storage/                # Database models
│   ├── eval/                   # Metrics harness
│   └── tests/                  # Unit & integration tests
├── frontend/                   # React operator dashboard
│   ├── src/
│   │   ├── api/                # API client
│   │   ├── components/         # Reusable components
│   │   └── pages/              # Page components
├── data/                       # Generated datasets
├── scripts/                    # CLI tools
├── docs/                       # Documentation
└── agentPlanning/              # Project planning docs
```

## Features

### 🎯 Behavioral Signal Detection
- Subscription patterns
- Savings behavior
- Credit utilization
- Income stability

### 👤 Smart Persona Assignment
- High Utilization
- Variable Income Budgeter
- Subscription-Heavy
- Savings Builder
- Custom Persona (TBD)

### 📚 Personalized Recommendations
- 3-5 education items per user
- 1-3 partner offers with eligibility checks
- Plain-language rationales with data citations
- LLM-generated with template fallbacks

### 🛡️ Compliance Guardrails
- Explicit consent tracking
- Eligibility filtering
- Tone validation (no shaming language)
- Required disclaimers
- Harmful product blocklist

### 🖥️ Operator Dashboard
- User list with filtering
- Individual user profiles
- Behavioral signals view (30d & 180d)
- Recommendation review
- Decision trace audit log

## Development Roadmap

See `agentPlanning/phased_plan.md` for the detailed implementation plan.

### Current Status: Epic 0 - Setup & Scaffolding

- [x] Monorepo structure
- [x] Python environment with dependencies
- [x] React frontend with Vite
- [x] Routing structure
- [x] API client setup
- [ ] Database schema
- [ ] Basic FastAPI endpoints
- [ ] React-to-API connection

### Next Steps

1. **Epic 1:** Synthetic data generation (Plaid-style)
2. **Epic 2:** Feature engineering (signal detection)
3. **Epic 3:** Persona assignment system
4. **Epic 4:** Recommendation engine with LLM
5. **Epic 5:** Guardrails (consent, eligibility, tone)
6. **Epic 6:** Operator dashboard completion

## Testing

Run backend tests:
```bash
cd backend
pytest
```

Run frontend linter:
```bash
cd frontend
npm run lint
```

## Documentation

- **Project Requirements:** `agentPlanning/project_requirements.md`
- **Implementation Plan:** `agentPlanning/phased_plan.md`
- **Backend Docs:** `backend/README.md` (TODO)
- **Frontend Docs:** `frontend/README.md`

## License

This is a demo project for educational purposes.

## Core Principles

- **Transparency over sophistication**
- **User control over automation**
- **Education over sales**
- **Fairness built in from day one**
- **Explainability and auditability first**


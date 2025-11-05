# Recommendation Engine

## Setup

### 1. Environment Variables

Create a `.env` file in the project root (`/Users/tombauer/workspace/github.com/TBau23/spendSense/.env`):

```bash
# OpenAI API Configuration
OPENAI_API_KEY=sk-your_actual_key_here

# Optional: Use mock mode for testing (no API calls, no costs)
MOCK_LLM=false
```

Get your OpenAI API key from: https://platform.openai.com/api-keys

### 2. Testing Without API Key

You can test the recommendation engine without an API key by setting `MOCK_LLM=true`:

```bash
export MOCK_LLM=true
python scripts/generate_recommendations.py
```

Mock mode returns placeholder text for all LLM calls, allowing you to test the full pipeline without costs.

### 3. Database Initialization

The recommendation tables, content catalog, partner offers, and generic templates are already loaded. You can verify with:

```bash
python -c "from backend.recommend.storage import *; print('Recommendation system ready!')"
```

## Modules

- `storage.py` - SQLite and Parquet storage operations
- `llm_client.py` - OpenAI API client with error handling and mock mode
- `prompts.py` - Prompt templates for rationale and actionable item generation
- `content_catalog.json` - 23 educational content items
- `partner_offers.json` - 9 generic placeholder products
- `generic_templates.json` - 6 pre-approved fallback templates
- `content_loader.py` - Load catalogs into database
- `generator.py` - Main recommendation generation logic (TODO: Phase 4)

## Current Status

- ✅ Phase 1 Complete: Module setup, catalogs created and loaded
- ✅ Phase 2 Complete: LLM client and prompts system ready
- ⏳ Phase 3-7: In progress


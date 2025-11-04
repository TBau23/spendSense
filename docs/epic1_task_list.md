# Epic 1: Data Foundation - Task List

**Status**: Ready for Implementation  
**Design Doc**: `epic1_technical_design.md`  
**Core Problem**: Generate high-quality synthetic data that triggers all 5 personas and supports Epic 2 signal detection

---

## Implementation Tasks

### 1. Database Setup
**Task**: Setup SQLite schema + database connection utilities  
**Output**: 4 tables operational (users, accounts, transactions, liabilities)  
**Key Files**: `backend/storage/database.py`, `backend/storage/schemas.py`

### 2. Archetype Definitions
**Task**: Define archetype configs with realistic financial behaviors  
**Output**: Archetype configurations for 5 personas + multi-persona + stable + edge cases  
**Key Files**: `backend/core/data_gen/archetypes.py`, `config.json`

### 3. User & Account Generation
**Task**: Build user + account generator  
**Output**: 50-100 users with Faker PII, 90/10 consent split, account types per archetype  
**Key Files**: `backend/core/data_gen/generator.py`, `backend/core/data_gen/accounts.py`

### 4. Transaction Generation (Chronological)
**Task**: Build chronological transaction generator with running balance tracking  
**Output**: 7 months transactions with archetype-specific patterns, validated balances for Cash Flow Stressed  
**Key Files**: `backend/core/data_gen/transactions.py`  
**Critical**: Ensure Cash Flow Stressed users hit 30%+ days with balance <$100

### 5. Liabilities Generation
**Task**: Generate credit card and loan data  
**Output**: Credit utilization levels, APRs, payment history matching archetypes  
**Key Files**: `backend/core/data_gen/liabilities.py`

### 6. Data Validation Pipeline
**Task**: Build validation checks and quality assurance  
**Output**: Validation report (persona coverage, consent distribution, date ranges, data quality)  
**Key Files**: `backend/core/data_gen/validation.py`

### 7. Generation Script & Config
**Task**: Create CLI entry point and configuration management  
**Output**: One-command generation via `python scripts/generate_data.py`  
**Key Files**: `scripts/generate_data.py`, `config.json`

### 8. Testing
**Task**: Write unit and integration tests  
**Output**: ≥4 tests passing (archetype logic, schema creation, consent distribution, end-to-end)  
**Key Files**: `backend/tests/test_data_generation.py`

---

## Validation Criteria

Before moving to Epic 2, verify:
- [ ] All 5 personas have ≥5 representative users in dataset
- [ ] Consent distribution: 88-92% consent=true (±2% variance acceptable)
- [ ] Cash Flow Stressed users verified to have 30%+ days with balance <$100
- [ ] High Utilizer users have credit utilization ≥50%
- [ ] Variable Income users have payroll gaps >45 days
- [ ] Subscription Heavy users have ≥3 recurring merchants
- [ ] Savings Builder users show positive savings growth
- [ ] Date range: exactly 7 months ending "today"
- [ ] No validation errors in quality checks
- [ ] Tests passing

---

## Dependencies

**External Libraries**:
- `Faker` - PII generation
- `sqlite3` - Database
- Standard Python libraries (datetime, random, etc.)

**Config**:
- `config.json` with archetype distributions and generation parameters

---

## Epic Completion

**Definition of Done**:
1. ✅ SQLite database populated with validated data
2. ✅ All validation criteria met
3. ✅ Tests passing
4. ✅ Decision log updated
5. ✅ Generation script works via single command
6. ✅ Next Epic Prerequisites documented in decision log


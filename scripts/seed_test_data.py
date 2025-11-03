"""
Quick test data seeder
Adds a few sample users to test the API
"""
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from storage import init_db, SessionLocal
from storage.models import User, Consent


def seed_test_users():
    """Create a few test users"""
    print("🌱 Seeding test data...")
    
    # Initialize database
    init_db()
    
    # Create session
    db = SessionLocal()
    
    try:
        # Check if users already exist
        existing = db.query(User).count()
        if existing > 0:
            print(f"⚠️  Database already has {existing} users. Skipping seed.")
            return
        
        # Create test users
        users = [
            User(
                user_id="user_001",
                name="Alice Johnson",
                email="alice@example.com",
                primary_persona="high_utilization",
                persona_assigned_at=datetime.utcnow()
            ),
            User(
                user_id="user_002",
                name="Bob Smith",
                email="bob@example.com",
                primary_persona="savings_builder",
                persona_assigned_at=datetime.utcnow()
            ),
            User(
                user_id="user_003",
                name="Carol Martinez",
                email="carol@example.com",
                primary_persona="variable_income",
                persona_assigned_at=datetime.utcnow()
            ),
            User(
                user_id="user_004",
                name="David Chen",
                email="david@example.com",
                primary_persona="subscription_heavy",
                persona_assigned_at=datetime.utcnow()
            ),
            User(
                user_id="user_005",
                name="Eve Williams",
                email="eve@example.com",
                primary_persona=None,  # No persona assigned yet
            ),
        ]
        
        # Add users to database
        for user in users:
            db.add(user)
        
        # Create consent records
        consents = [
            Consent(user_id="user_001", consent_status=True, consent_date=datetime.utcnow()),
            Consent(user_id="user_002", consent_status=True, consent_date=datetime.utcnow()),
            Consent(user_id="user_003", consent_status=False),  # No consent
            Consent(user_id="user_004", consent_status=True, consent_date=datetime.utcnow()),
            Consent(user_id="user_005", consent_status=False),  # No consent
        ]
        
        for consent in consents:
            db.add(consent)
        
        # Commit changes
        db.commit()
        
        print(f"✅ Created {len(users)} test users")
        print("   - Alice Johnson (High Utilization, Consented)")
        print("   - Bob Smith (Savings Builder, Consented)")
        print("   - Carol Martinez (Variable Income, No Consent)")
        print("   - David Chen (Subscription Heavy, Consented)")
        print("   - Eve Williams (No Persona, No Consent)")
        print("\n🚀 Ready to test! Start backend with: uvicorn api.main:app --reload")
        
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_test_users()


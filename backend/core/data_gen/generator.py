"""
Main synthetic data generation orchestrator for SpendSense
Coordinates user, account, transaction, and liability generation
"""

import sqlite3
import random
from typing import Dict, List, Any
from datetime import datetime, timedelta
from faker import Faker

from .archetypes import (
    ARCHETYPES,
    get_archetype_distribution,
    get_archetype_by_name,
    Archetype
)
from .accounts import generate_user_accounts
from .transactions import generate_user_transactions
from .liabilities import generate_user_liabilities


# Initialize Faker with seed for reproducibility
fake = Faker()
Faker.seed(42)
random.seed(42)


def generate_user_id() -> str:
    """Generate a unique user ID"""
    return f"user_{fake.uuid4()[:8]}"


def generate_users(
    count: int,
    consent_ratio: float,
    archetype_distribution: Dict[str, int],
    conn: sqlite3.Connection
) -> Dict[str, Dict[str, Any]]:
    """
    Generate synthetic users with consent distribution
    
    Args:
        count: Total number of users to generate
        consent_ratio: Ratio of users with consent (e.g., 0.9 for 90%)
        archetype_distribution: Dictionary mapping archetype name to count
        conn: Database connection
        
    Returns:
        Dictionary mapping user_id to user metadata
    """
    cursor = conn.cursor()
    users = {}
    
    # Shuffle archetype list for random assignment
    archetype_list = []
    for archetype_name, archetype_count in archetype_distribution.items():
        archetype_list.extend([archetype_name] * archetype_count)
    
    random.shuffle(archetype_list)
    
    # Ensure we have exactly the right count
    archetype_list = archetype_list[:count]
    
    # Determine which users have consent (first N% get consent)
    consent_count = int(count * consent_ratio)
    consented_indices = set(random.sample(range(count), consent_count))
    
    created_at = datetime.now()
    
    for i, archetype_name in enumerate(archetype_list):
        user_id = generate_user_id()
        name = fake.name()
        has_consent = i in consented_indices
        
        cursor.execute("""
            INSERT INTO users (user_id, name, created_at, consent_status, consent_updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            user_id,
            name,
            created_at,
            has_consent,
            created_at
        ))
        
        archetype = get_archetype_by_name(archetype_name)
        
        users[user_id] = {
            "name": name,
            "archetype": archetype,
            "archetype_name": archetype_name,
            "consent": has_consent,
            "created_at": created_at
        }
    
    conn.commit()
    print(f"✓ Generated {count} users ({consent_count} with consent, {count - consent_count} without)")
    
    return users


def generate_synthetic_data(
    user_count: int,
    consent_ratio: float,
    date_range_months: int,
    conn: sqlite3.Connection,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Generate complete synthetic dataset
    
    Args:
        user_count: Number of users to generate
        consent_ratio: Ratio of users with consent (0.0 to 1.0)
        date_range_months: Number of months of transaction history
        conn: Database connection
        seed: Random seed for reproducibility
        
    Returns:
        Generation summary report
    """
    print("\n" + "="*60)
    print("SpendSense Synthetic Data Generation")
    print("="*60)
    
    # Set seeds
    random.seed(seed)
    Faker.seed(seed)
    
    start_time = datetime.now()
    
    # Calculate archetype distribution
    archetype_dist = get_archetype_distribution(user_count)
    print(f"\nArchetype distribution for {user_count} users:")
    for name, count in archetype_dist.items():
        print(f"  {name}: {count}")
    
    # Generate users
    print("\n[1/4] Generating users...")
    users = generate_users(user_count, consent_ratio, archetype_dist, conn)
    
    # Generate accounts
    print("[2/4] Generating accounts...")
    account_count = 0
    for user_id, user_data in users.items():
        account_ids = generate_user_accounts(
            user_id,
            user_data["archetype"],
            conn
        )
        user_data["account_ids"] = account_ids
        account_count += len(account_ids)
    print(f"✓ Generated {account_count} accounts")
    
    # Generate transactions (chronologically with balance tracking)
    print("[3/4] Generating transactions...")
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=date_range_months * 30)
    
    total_transactions = 0
    for user_id, user_data in users.items():
        transaction_count = generate_user_transactions(
            user_id,
            user_data["archetype"],
            user_data["account_ids"],
            start_date,
            end_date,
            conn
        )
        user_data["transaction_count"] = transaction_count
        total_transactions += transaction_count
    
    print(f"✓ Generated {total_transactions} transactions")
    
    # Generate liabilities (for credit accounts)
    print("[4/4] Generating liabilities...")
    liability_count = 0
    for user_id, user_data in users.items():
        liabilities = generate_user_liabilities(
            user_id,
            user_data["archetype"],
            user_data["account_ids"],
            conn
        )
        user_data["liabilities"] = liabilities
        liability_count += len(liabilities)
    
    print(f"✓ Generated {liability_count} liabilities")
    
    # Generate summary report
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    consented_users = sum(1 for u in users.values() if u["consent"])
    
    report = {
        "generation_date": start_time.isoformat(),
        "duration_seconds": duration,
        "seed": seed,
        "user_count": user_count,
        "consent_distribution": {
            "consented": consented_users,
            "not_consented": user_count - consented_users,
            "ratio": consent_ratio
        },
        "archetype_distribution": archetype_dist,
        "date_range": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "months": date_range_months
        },
        "counts": {
            "users": user_count,
            "accounts": account_count,
            "transactions": total_transactions,
            "liabilities": liability_count
        }
    }
    
    print("\n" + "="*60)
    print("Generation Complete!")
    print("="*60)
    print(f"Duration: {duration:.2f} seconds")
    print(f"Users: {user_count} ({consented_users} consented)")
    print(f"Accounts: {account_count}")
    print(f"Transactions: {total_transactions}")
    print(f"Liabilities: {liability_count}")
    print(f"Date range: {start_date} to {end_date}")
    
    return report


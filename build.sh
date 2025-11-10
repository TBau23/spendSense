#!/bin/bash
set -e

echo "================================"
echo "SpendSense Backend Build Script"
echo "================================"

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r backend/requirements.txt

# Create persistent data directory if it doesn't exist
mkdir -p /data
mkdir -p /data/features

# Create symlink from 'data' to '/data' so code can use relative paths
# This allows config.json to use 'data/' paths that work both locally and in production
if [ -L "data" ]; then
    echo "Symlink already exists: data -> /data"
elif [ -d "data" ]; then
    echo "Removing data directory and creating symlink: data -> /data"
    rm -rf data
    ln -sf /data data
else
    echo "Creating symlink: data -> /data"
    ln -sf /data data
fi

# Check if database exists
if [ ! -f "/data/spendsense.db" ]; then
    echo "Database not found. Initializing demo data..."
    
    # Initialize database schema
    echo "Initializing database schema..."
    python -c "
from backend.storage.database import initialize_database
initialize_database(reset=False)
print('✓ Database schema initialized')
"
    
    # Load content catalogs (educational content, partner offers, templates)
    echo "Loading content catalogs..."
    python -c "
from backend.recommend.content_loader import (
    load_content_catalog_from_json,
    load_partner_offers_from_json,
    load_generic_templates_from_json
)
from backend.storage.database import get_db_path

db_path = get_db_path()

catalog_count = load_content_catalog_from_json(
    db_path,
    'backend/recommend/content_catalog.json'
)

offers_count = load_partner_offers_from_json(
    db_path,
    'backend/recommend/partner_offers.json'
)

templates_count = load_generic_templates_from_json(
    db_path,
    'backend/recommend/generic_templates.json'
)

print(f'✓ Loaded {catalog_count} educational items, {offers_count} partner offers, {templates_count} templates')
"
    
    # Generate synthetic user data (uses seed from config.json for reproducibility)
    echo "Step 1/3: Generating synthetic transaction data..."
    python scripts/generate_data.py
    
    # Compute features (deterministic based on transactions)
    echo "Step 2/3: Computing behavioral features..."
    python scripts/compute_features.py
    
    # Assign personas (deterministic based on features)
    echo "Step 3/3: Assigning user personas..."
    python scripts/assign_personas.py
    
    echo ""
    echo "✓ Demo data initialization complete!"
    echo ""
    echo "To generate recommendations manually, run:"
    echo "  python scripts/generate_recommendations.py --batch"
else
    echo "Database found at /data/spendsense.db. Skipping data generation."
    echo ""
    echo "To regenerate all data, delete the database and restart:"
    echo "  rm /data/spendsense.db"
    echo "Or locally run: ./regenerate_data.sh --users 75 --seed 100"
fi


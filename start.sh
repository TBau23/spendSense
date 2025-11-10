#!/bin/bash
set -e

echo "================================"
echo "SpendSense Backend Start Script"
echo "================================"

# Set Python path to include backend modules
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Use PORT environment variable from Render, default to 8000 for local
PORT="${PORT:-8000}"

# Create persistent data directory if it doesn't exist
echo "Setting up data directory..."
mkdir -p /data
mkdir -p /data/features

# Create symlink from 'data' to '/data' so code can use relative paths
# This allows config.json to use 'data/' paths that work both locally and in production
if [ -L "data" ]; then
    echo "✓ Symlink already exists: data -> /data"
elif [ -d "data" ]; then
    echo "Removing data directory and creating symlink: data -> /data"
    rm -rf data
    ln -sf /data data
else
    echo "Creating symlink: data -> /data"
    ln -sf /data data
fi

# Check if database exists - if not, initialize demo data
if [ ! -f "/data/spendsense.db" ]; then
    echo ""
    echo "================================"
    echo "First-time setup: Initializing demo data..."
    echo "This will take 2-3 minutes"
    echo "================================"
    echo ""
    
    # Generate synthetic data (uses seed from config.json for reproducibility)
    echo "Step 1/4: Generating synthetic transaction data..."
    python scripts/generate_data.py
    
    # Compute features (deterministic based on transactions)
    echo "Step 2/4: Computing behavioral features..."
    python scripts/compute_features.py
    
    # Assign personas (deterministic based on features)
    echo "Step 3/4: Assigning user personas..."
    python scripts/assign_personas.py
    
    # Generate recommendations for all users
    echo "Step 4/4: Generating recommendations..."
    python scripts/generate_recommendations.py --batch
    
    echo ""
    echo "✓ Demo data initialization complete!"
    echo ""
else
    echo "✓ Database found at /data/spendsense.db"
fi

echo ""
echo "Starting FastAPI server on port $PORT..."
echo ""

# Start uvicorn with production settings
python -m uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT

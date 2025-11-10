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
    
    echo "Demo data initialization complete!"
else
    echo "Database found at /data/spendsense.db. Skipping data generation."
fi

echo "Build complete!"


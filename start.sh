#!/bin/bash
set -e

echo "================================"
echo "SpendSense Backend Start Script"
echo "================================"

# Set Python path to include backend modules
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Use PORT environment variable from Render, default to 8000 for local
PORT="${PORT:-8000}"

echo "Starting FastAPI server on port $PORT..."

# Start uvicorn with production settings
python -m uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT


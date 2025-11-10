#!/bin/bash
set -e

echo "================================"
echo "SpendSense Backend Build Script"
echo "================================"

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r backend/requirements.txt

echo "✓ Build complete!"
echo ""
echo "Note: Data initialization will happen on startup when disk is mounted"

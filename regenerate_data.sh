#!/bin/bash
# Helper script to regenerate data using the correct Python environment

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Use the venv Python
PYTHON="${SCRIPT_DIR}/backend/venv/bin/python"

# Check if venv exists
if [ ! -f "$PYTHON" ]; then
    echo "❌ Virtual environment not found at backend/venv"
    echo "   Please run: cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Run the regeneration script with all arguments passed through
"$PYTHON" "${SCRIPT_DIR}/scripts/regenerate_all_data.py" "$@"


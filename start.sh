#!/bin/bash
set -e

# Load .env if it exists
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Install dependencies if needed
if ! python3 -c "import flask" 2>/dev/null; then
  pip3 install -r requirements.txt
fi

echo ""
echo "  YouTube Learning is running!"
echo "  Open: http://localhost:5000"
echo ""

python3 app.py

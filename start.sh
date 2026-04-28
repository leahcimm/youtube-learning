#!/bin/bash
set -e

# Install dependencies if needed
python3 -c "import flask, youtube_transcript_api, jieba, sklearn" 2>/dev/null || {
  echo "Installing dependencies..."
  pip3 install -r requirements.txt -q
}

echo ""
echo "  YouTube Learning is running!"
echo "  Open: http://localhost:8080"
echo ""

export PYTHONPATH="$(dirname "$0")"
python3 "$(dirname "$0")/app.py"

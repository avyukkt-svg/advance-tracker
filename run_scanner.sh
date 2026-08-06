#!/bin/bash

echo "Starting NSE Catalyst Scanner..."
cd "/Users/avyukktvuppalanchi/news feed reader/nse-catalyst-scanner"

# Run the python script using the virtual environment
PYTHONPATH=. venv/bin/python main.py

echo ""
echo "Done! Check your email for any detected catalysts."

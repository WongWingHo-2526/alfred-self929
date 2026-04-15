#!/bin/bash
echo "Installing dependencies..."
pip install -r requirements.txt
echo "Dependencies installed. Starting Flask..."
exec flask --debug run --host=0.0.0.0 --port=5000
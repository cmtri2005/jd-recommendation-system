#!/bin/bash

# Script to run Streamlit dashboard
# Usage: ./run.sh

cd "$(dirname "$0")"

echo "🚀 Starting JD Analytics Dashboard..."
echo "📊 Dashboard will be available at: http://localhost:8501"
echo ""

streamlit run app.py


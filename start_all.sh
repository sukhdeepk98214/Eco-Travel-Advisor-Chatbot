#!/bin/bash

# Activate environment
source venv39/bin/activate

echo "Starting Action Server..."
rasa run actions > action.log 2>&1 &

sleep 5

echo "Starting Rasa Server..."
rasa run --enable-api --cors "*" > rasa.log 2>&1 &

sleep 5

echo "Starting Streamlit..."
cd frontend
streamlit run app.py > streamlit.log 2>&1 &

echo "ALL SERVICES STARTED 🚀"
echo "Open: http://localhost:8501"

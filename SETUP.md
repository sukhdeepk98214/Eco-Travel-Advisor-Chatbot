# Eco-Travel Advisor — Setup & Run Guide

## Project Structure

```
Eco-Travel Advisor CHATBOT/
├── config.yml              # NLU pipeline + dialogue policies
├── domain.yml              # Intents, entities, slots, responses, forms
├── credentials.yml         # Channel credentials (REST, SocketIO)
├── endpoints.yml           # Action server + tracker store
├── requirements.txt        # Python dependencies
│
├── data/
│   ├── nlu.yml             # NLU training data (20+ examples/intent)
│   ├── stories.yml         # Multi-turn conversation stories
│   └── rules.yml           # Deterministic conversation rules
│
├── actions/
│   ├── __init__.py
│   └── actions.py          # All 6 custom actions + form validation
│
├── tests/
│   └── test_stories.yml    # End-to-end conversation tests
│
├── frontend/
│   └── app.py              # Streamlit chat interface
│
└── models/                 # Trained models saved here
```

---

## Prerequisites

- Python 3.9 (Rasa 3.6 requires Python 3.9 specifically)
- pip
- 4GB+ RAM recommended for training

---

## Step 1 — Create Virtual Environment

```bash
# Create a Python 3.9 virtual environment
python3.9 -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Activate it (macOS/Linux)
source venv/bin/activate
```

---

## Step 2 — Install Dependencies

```bash
pip install --upgrade pip
pip install rasa==3.6.20
pip install rasa-sdk==3.6.2
pip install streamlit==1.32.0 requests
```

Or using requirements.txt:
```bash
pip install -r requirements.txt
```

---

## Step 3 — Train the Model

From the project root directory:

```bash
cd "c:\Eco-Travel Advisor CHATBOT"
rasa train
```

This will:
- Train the NLU model (intent classification + entity extraction)
- Train the dialogue model (stories + rules)
- Save the model to `models/` directory

Training takes approximately 3-8 minutes.

---

## Step 4 — Run the Chatbot (3 terminals required)

### Terminal 1: Start Rasa Action Server
```bash
cd "c:\Eco-Travel Advisor CHATBOT"
rasa run actions
```
Starts on port 5055

### Terminal 2: Start Rasa REST API Server
```bash
cd "c:\Eco-Travel Advisor CHATBOT"
rasa run --enable-api --cors "*" --debug
```
Starts on port 5005

### Terminal 3: Start Streamlit Frontend
```bash
cd "c:\Eco-Travel Advisor CHATBOT\frontend"
streamlit run app.py
```
Opens browser at http://localhost:8501

---

## Step 5 — Test via Command Line (Optional)

```bash
# Interactive shell test
rasa shell

# Test NLU only
rasa shell nlu

# Run automated tests
rasa test
```

---

## Step 6 — Test via API (curl)

```bash
# Send a message
curl -X POST http://localhost:5005/webhooks/rest/webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "test_user", "message": "I want to plan a trip to Costa Rica"}'

# Check server status
curl http://localhost:5005/

# Get conversation tracker
curl http://localhost:5005/conversations/test_user/tracker
```

---

## Quick Test Conversation

Once running, try this conversation flow:

```
User: Hello
Bot:  [Greets and explains capabilities]

User: I want to plan an eco trip
Bot:  [Asks for destination]

User: Costa Rica
Bot:  [Confirms destination, asks for dates]

User: July 10-20
Bot:  [Confirms dates, asks for budget]

User: $2000
Bot:  [Confirms budget, asks for travelers]

User: 2 people
Bot:  [Confirms travelers, asks for sustainability preference]

User: High
Bot:  [Confirms high eco, shows trip summary]

User: Show me eco hotels
Bot:  [Shows 3 eco-certified hotels in Costa Rica with scores]

User: What transport options are there?
Bot:  [Compares flight/train/bus/EV emissions]

User: Calculate my carbon footprint
Bot:  [Full emissions breakdown + offset recommendations]

User: What activities are available?
Bot:  [Shows 6 eco-friendly cultural activities]

User: I want to talk to a human
Bot:  [Summarizes trip, initiates handover]
```

---

## Intent Reference

| Intent | Example |
|--------|---------|
| greet | "Hello", "Hi there" |
| plan_trip | "I want to plan an eco trip" |
| provide_destination | "I want to go to Costa Rica" |
| provide_budget | "My budget is $2000" |
| provide_dates | "July 10-20" |
| provide_travelers | "2 people" |
| sustainability_preference | "High sustainability" |
| ask_hotel | "Show me eco hotels" |
| ask_transport | "What are green transport options?" |
| ask_carbon | "Calculate my carbon footprint" |
| ask_activities | "What activities are available?" |
| human_handover | "I want to talk to a human" |
| affirm | "Yes", "Sure", "Correct" |
| deny | "No", "Cancel", "Never mind" |

---

## Slot Reference

| Slot | Type | Example |
|------|------|---------|
| destination | text | "Costa Rica" |
| budget | text | "$2000" |
| travel_date | text | "July 10-20" |
| travelers | text | "2 people" |
| sustainability_level | categorical | "high" / "medium" / "low" |
| transport_type | text | "train" / "flight" |

---

## Troubleshooting

**"No module named rasa"**
→ Ensure your virtualenv is activated and Rasa is installed

**Action server connection refused (port 5055)**
→ Start action server first: `rasa run actions`

**"Model not found"**
→ Run `rasa train` before starting the server

**Streamlit shows "Cannot connect to Rasa"**
→ Ensure Rasa is running: `rasa run --enable-api --cors "*"`

**Training fails with memory error**
→ Reduce epochs in config.yml (DIETClassifier epochs: 50, TEDPolicy epochs: 50)

---

## Production Deployment Notes

1. Replace SQLite tracker store with PostgreSQL in endpoints.yml
2. Set CORS origins specifically (not `"*"`) in production
3. Use Redis lock store for multi-worker deployments
4. Add SSL/TLS via nginx reverse proxy
5. Set `RASA_TELEMETRY_ENABLED=false` for privacy

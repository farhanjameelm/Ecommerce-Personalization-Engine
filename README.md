# Ecommerce Personalization Rules Engine

A real-time LLM-powered mini-tool that classifies shoppers into behavioral states and provides personalized recommendations.

## Features

- **Event Stream Processing**: Processes mock user events (page views, cart actions, searches, etc.)
- **Shopper Classification**: Classifies users into states:
  - Browser
  - Comparer
  - Discount Seeker
  - Cart Abandoner
  - Loyal Customer
- **Evidence & Confidence**: Explains the reasoning behind each classification with confidence scores
- **Recommendations**: Provides site actions and nudges based on shopper state
- **Real-time Simulator**: Interactive UI to add events and see classifications update live

## Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run the backend
python backend/main.py
```

The API will be available at `http://localhost:8000`

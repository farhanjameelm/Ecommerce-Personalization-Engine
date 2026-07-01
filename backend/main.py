from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, ConfigDict
from typing import Dict, List, Any
import json
import uuid
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models import Event, Session, ClassificationResult, EventType
from backend.classifier import ShopperClassifier
from backend.event_generator import MockEventGenerator


app = FastAPI(title="Ecommerce Personalization Engine")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for sessions
sessions: Dict[str, Session] = {}
classifier = ShopperClassifier()


class AddEventRequest(BaseModel):
    session_id: str
    event_type: EventType
    product_id: str = None
    product_category: str = None
    page_url: str = None
    search_query: str = None
    cart_value: float = None
    coupon_code: str = None


class CreateSessionRequest(BaseModel):
    preset: str = None  # 'browser', 'comparer', 'discount_seeker', 'cart_abandoner', 'loyal_customer'


@app.get("/")
async def get_frontend():
    """Serve the frontend HTML."""
    frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "index.html")
    with open(frontend_path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.post("/api/sessions")
async def create_session(request: CreateSessionRequest):
    """Create a new session with optional preset events."""
    session_id = str(uuid.uuid4())
    events = []
    
    if request.preset:
        if request.preset == "browser":
            events = MockEventGenerator.generate_browser_sequence(session_id)
        elif request.preset == "comparer":
            events = MockEventGenerator.generate_comparer_sequence(session_id)
        elif request.preset == "discount_seeker":
            events = MockEventGenerator.generate_discount_seeker_sequence(session_id)
        elif request.preset == "cart_abandoner":
            events = MockEventGenerator.generate_cart_abandoner_sequence(session_id)
        elif request.preset == "loyal_customer":
            events = MockEventGenerator.generate_loyal_customer_sequence(session_id)
    
    session = Session(session_id=session_id, events=events)
    classification = classifier.classify(events)
    session.classification = classification
    
    sessions[session_id] = session
    return {"session_id": session_id, "classification": classification.model_dump(mode='json')}


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session details including classification."""
    if session_id not in sessions:
        return {"error": "Session not found"}
    
    session = sessions[session_id]
    return {
        "session_id": session.session_id,
        "events": [e.model_dump(mode='json') for e in session.events],
        "classification": session.classification.model_dump(mode='json') if session.classification else None
    }


@app.post("/api/sessions/{session_id}/events")
async def add_event(session_id: str, request: AddEventRequest):
    """Add an event to a session and reclassify."""
    if session_id not in sessions:
        return {"error": "Session not found"}
    
    session = sessions[session_id]
    event = Event(
        event_type=request.event_type,
        session_id=session_id,
        product_id=request.product_id,
        product_category=request.product_category,
        page_url=request.page_url,
        search_query=request.search_query,
        cart_value=request.cart_value,
        coupon_code=request.coupon_code,
    )
    
    session.events.append(event)
    classification = classifier.classify(session.events)
    session.classification = classification
    
    return {
        "event": event.model_dump(mode='json'),
        "classification": classification.model_dump(mode='json')
    }


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    if session_id in sessions:
        del sessions[session_id]
    return {"success": True}


@app.get("/api/sessions")
async def list_sessions():
    """List all sessions."""
    return {
        "sessions": [
            {
                "session_id": sid,
                "event_count": len(s.events),
                "state": s.classification.state.value if s.classification else "unknown",
                "confidence": s.classification.confidence if s.classification else 0
            }
            for sid, s in sessions.items()
        ]
    }


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    
    try:
        while True:
            # Wait for client message
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "add_event":
                # Add event and reclassify
                if session_id in sessions:
                    session = sessions[session_id]
                    event_data = message.get("event", {})
                    event = Event(
                        event_type=EventType(event_data["event_type"]),
                        session_id=session_id,
                        product_id=event_data.get("product_id"),
                        product_category=event_data.get("product_category"),
                        page_url=event_data.get("page_url"),
                        search_query=event_data.get("search_query"),
                        cart_value=event_data.get("cart_value"),
                        coupon_code=event_data.get("coupon_code"),
                    )
                    
                    session.events.append(event)
                    classification = classifier.classify(session.events)
                    session.classification = classification
                    
                    # Send updated classification back
                    await websocket.send_json({
                        "type": "classification_update",
                        "event": event.model_dump(mode='json'),
                        "classification": classification.model_dump(mode='json')
                    })
            
            elif message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        print(f"WebSocket error: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

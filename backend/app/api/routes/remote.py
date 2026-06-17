from fastapi import APIRouter, status
from pydantic import BaseModel
from typing import List, Optional
import time

router = APIRouter(prefix="/remote", tags=["Remote Control"])

class RemoteEvent(BaseModel):
    id: int
    event_type: str
    payload: Optional[dict] = None
    created_at: float

# In-memory store for demo purposes (Hackathon ready)
events_store: List[RemoteEvent] = []

@router.post("/event", status_code=status.HTTP_201_CREATED)
def push_event(event_data: dict):
    """Push an event from a mobile device or external trigger."""
    event_type = event_data.get("type", "UNKNOWN")
    payload = event_data.get("payload", {})
    
    new_event = RemoteEvent(
        id=len(events_store) + 1,
        event_type=event_type,
        payload=payload,
        created_at=time.time()
    )
    events_store.append(new_event)
    
    # Keep only last 50 events
    if len(events_store) > 50:
        events_store.pop(0)
        
    return new_event

@router.get("/events", response_model=List[RemoteEvent])
def get_events(since_id: int = 0):
    """Retrieve new events since a specific ID (for polling)."""
    return [e for e in events_store if e.id > since_id]

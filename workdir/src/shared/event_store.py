"""Event Store with JSON persistence and snapshots."""
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import uuid

@dataclass
class Event:
    event_id: str
    event_type: str
    aggregate_id: str
    data: Dict[str, Any]
    timestamp: str
    version: int = 1

class EventStore:
    def __init__(self, data_dir: str = "workdir/data"):
        self.data_dir = data_dir
        self.events_file = f"{data_dir}/events/events.json"
        self.snapshots_dir = f"{data_dir}/snapshots"
        self.events: List[Event] = []
        self._ensure_directories()
        self._load_events()
    
    def _ensure_directories(self):
        os.makedirs(f"{self.data_dir}/events", exist_ok=True)
        os.makedirs(self.snapshots_dir, exist_ok=True)
    
    def _load_events(self):
        if os.path.exists(self.events_file):
            with open(self.events_file, 'r') as f:
                events_data = json.load(f)
                self.events = [Event(**event) for event in events_data]
    
    def append_event(self, event_type: str, aggregate_id: str, data: Dict[str, Any]) -> Event:
        event = Event(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            aggregate_id=aggregate_id,
            data=data,
            timestamp=datetime.now().isoformat()
        )
        self.events.append(event)
        self._persist_events()
        return event
    
    def get_events(self, aggregate_id: Optional[str] = None) -> List[Event]:
        if aggregate_id:
            return [e for e in self.events if e.aggregate_id == aggregate_id]
        return self.events
    
    def _persist_events(self):
        with open(self.events_file, 'w') as f:
            json.dump([asdict(event) for event in self.events], f, indent=2)
    
    def create_snapshot(self, aggregate_id: str, state: Dict[str, Any]):
        snapshot_file = f"{self.snapshots_dir}/{aggregate_id}_snapshot.json"
        snapshot_data = {
            "aggregate_id": aggregate_id,
            "timestamp": datetime.now().isoformat(),
            "state": state
        }
        with open(snapshot_file, 'w') as f:
            json.dump(snapshot_data, f, indent=2)
    
    def load_snapshot(self, aggregate_id: str) -> Optional[Dict[str, Any]]:
        snapshot_file = f"{self.snapshots_dir}/{aggregate_id}_snapshot.json"
        if os.path.exists(snapshot_file):
            with open(snapshot_file, 'r') as f:
                return json.load(f)
        return None
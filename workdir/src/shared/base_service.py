"""Base service class with event publishing and logging."""
from abc import ABC
from typing import Dict, Any, Optional
from .event_store import EventStore
from .logging import BusinessLogger

class BaseService(ABC):
    def __init__(self, unit_name: str, event_store: EventStore):
        self.unit_name = unit_name
        self.event_store = event_store
        self.logger = BusinessLogger(unit_name)
    
    def publish_event(self, event_type: str, aggregate_id: str, data: Dict[str, Any]):
        """Publish an event to the event store."""
        event = self.event_store.append_event(event_type, aggregate_id, data)
        self.logger.log_business_event('INFO', aggregate_id, 'EVENT_PUBLISHED', 'SUCCESS', 
                                      f'Published {event_type} event')
        return event
    
    def validate_required_fields(self, data: Dict[str, Any], required_fields: list) -> bool:
        """Validate that all required fields are present."""
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        return True
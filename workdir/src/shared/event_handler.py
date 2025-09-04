"""Event handling system for inter-unit communication."""
from typing import Dict, Any, Callable, List
from .event_store import Event, EventStore
from .logging import BusinessLogger

class EventHandler:
    def __init__(self, unit_name: str, event_store: EventStore):
        self.unit_name = unit_name
        self.event_store = event_store
        self.logger = BusinessLogger(f"{unit_name}-EventHandler")
        self.handlers: Dict[str, List[Callable]] = {}
        self.last_processed_event = 0
    
    def register_handler(self, event_type: str, handler: Callable[[Event], None]):
        """Register a handler for a specific event type."""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
    
    def process_events(self):
        """Process new events since last check."""
        all_events = self.event_store.get_events()
        new_events = all_events[self.last_processed_event:]
        
        for event in new_events:
            self._handle_event(event)
        
        self.last_processed_event = len(all_events)
    
    def _handle_event(self, event: Event):
        """Handle a single event."""
        if event.event_type in self.handlers:
            for handler in self.handlers[event.event_type]:
                try:
                    handler(event)
                    self.logger.log_business_event('INFO', event.aggregate_id, 
                                                 'EVENT_HANDLED', 'SUCCESS',
                                                 f'Processed {event.event_type} event')
                except Exception as e:
                    self.logger.log_error(event.aggregate_id, 'EVENT_HANDLING', 
                                        f'Failed to handle {event.event_type}: {str(e)}')
"""Base repository with in-memory storage and JSON persistence."""
import json
import os
from typing import Dict, Any, Optional, List, TypeVar, Generic
from abc import ABC, abstractmethod
import uuid

T = TypeVar('T')

class BaseRepository(Generic[T], ABC):
    def __init__(self, data_file: str):
        self.data_file = data_file
        self.data: Dict[str, Dict[str, Any]] = {}
        self._ensure_directory()
        self._load_data()
    
    def _ensure_directory(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
    
    def _load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                self.data = json.load(f)
    
    def _persist_data(self):
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def save(self, entity_id: str, entity_data: Dict[str, Any]) -> str:
        if not entity_id:
            entity_id = str(uuid.uuid4())
        entity_data['id'] = entity_id
        self.data[entity_id] = entity_data
        self._persist_data()
        return entity_id
    
    def find_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        return self.data.get(entity_id)
    
    def find_all(self) -> List[Dict[str, Any]]:
        return list(self.data.values())
    
    def find_by_field(self, field: str, value: Any) -> List[Dict[str, Any]]:
        return [entity for entity in self.data.values() if entity.get(field) == value]
    
    def delete(self, entity_id: str) -> bool:
        if entity_id in self.data:
            del self.data[entity_id]
            self._persist_data()
            return True
        return False
    
    def update(self, entity_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if entity_id in self.data:
            self.data[entity_id].update(updates)
            self._persist_data()
            return self.data[entity_id]
        return None
"""Persistence manager for periodic snapshots and data recovery."""
import json
import os
import threading
import time
from typing import Dict, Any
from datetime import datetime

class PersistenceManager:
    def __init__(self, data_dir: str = "workdir/data", snapshot_interval: int = 300):
        self.data_dir = data_dir
        self.snapshot_interval = snapshot_interval  # 5 minutes
        self.repositories: Dict[str, Any] = {}
        self.running = False
        self.snapshot_thread = None
        self._ensure_directories()
    
    def _ensure_directories(self):
        os.makedirs(f"{self.data_dir}/snapshots", exist_ok=True)
        os.makedirs(f"{self.data_dir}/backups", exist_ok=True)
    
    def register_repository(self, name: str, repository):
        """Register a repository for periodic snapshots."""
        self.repositories[name] = repository
    
    def start_periodic_snapshots(self):
        """Start periodic snapshot creation in background thread."""
        if not self.running:
            self.running = True
            self.snapshot_thread = threading.Thread(target=self._snapshot_loop)
            self.snapshot_thread.daemon = True
            self.snapshot_thread.start()
    
    def stop_periodic_snapshots(self):
        """Stop periodic snapshot creation."""
        self.running = False
        if self.snapshot_thread:
            self.snapshot_thread.join()
    
    def _snapshot_loop(self):
        """Background loop for creating periodic snapshots."""
        while self.running:
            try:
                self.create_snapshots()
                time.sleep(self.snapshot_interval)
            except Exception as e:
                print(f"Error creating snapshots: {e}")
    
    def create_snapshots(self):
        """Create snapshots of all registered repositories."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for name, repository in self.repositories.items():
            snapshot_data = {
                "timestamp": timestamp,
                "repository": name,
                "data": repository.data if hasattr(repository, 'data') else {}
            }
            
            snapshot_file = f"{self.data_dir}/snapshots/{name}_{timestamp}.json"
            with open(snapshot_file, 'w') as f:
                json.dump(snapshot_data, f, indent=2)
        
        # Keep only last 10 snapshots per repository
        self._cleanup_old_snapshots()
    
    def _cleanup_old_snapshots(self):
        """Remove old snapshots, keeping only the latest 10 per repository."""
        snapshot_dir = f"{self.data_dir}/snapshots"
        
        for repo_name in self.repositories.keys():
            snapshots = [f for f in os.listdir(snapshot_dir) if f.startswith(f"{repo_name}_")]
            snapshots.sort(reverse=True)  # Latest first
            
            # Remove old snapshots
            for old_snapshot in snapshots[10:]:
                os.remove(os.path.join(snapshot_dir, old_snapshot))
    
    def restore_from_snapshot(self, repository_name: str, snapshot_timestamp: str = None):
        """Restore a repository from a snapshot."""
        snapshot_dir = f"{self.data_dir}/snapshots"
        
        if snapshot_timestamp:
            snapshot_file = f"{snapshot_dir}/{repository_name}_{snapshot_timestamp}.json"
        else:
            # Find latest snapshot
            snapshots = [f for f in os.listdir(snapshot_dir) if f.startswith(f"{repository_name}_")]
            if not snapshots:
                return False
            snapshots.sort(reverse=True)
            snapshot_file = f"{snapshot_dir}/{snapshots[0]}"
        
        if os.path.exists(snapshot_file):
            with open(snapshot_file, 'r') as f:
                snapshot_data = json.load(f)
                if repository_name in self.repositories:
                    self.repositories[repository_name].data = snapshot_data.get('data', {})
                    return True
        
        return False
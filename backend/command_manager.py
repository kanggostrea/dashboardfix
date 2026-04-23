import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional

class CommandManager:
    """Manage commands queue and track command status"""
    
    def __init__(self, storage_file: str = "commands.json"):
        self.storage_file = storage_file
        self.commands: Dict = {}
        self.load()
    
    def load(self):
        """Load commands from persistent storage"""
        import os
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r') as f:
                    self.commands = json.load(f)
            except:
                self.commands = {}
    
    def save(self):
        """Save commands to persistent storage"""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(self.commands, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving commands: {e}")
    
    def create_command(self, slot: int, action: str, payload: dict = None) -> str:
        """Create a new command for a panel"""
        command_id = str(uuid.uuid4())
        self.commands[command_id] = {
            "id": command_id,
            "slot": slot,
            "action": action,
            "payload": payload or {},
            "status": "PENDING",
            "created_at": datetime.now().isoformat(),
            "executed_at": None,
            "result": None
        }
        self.save()
        return command_id
    
    def get_pending_commands(self, slot: int) -> List[Dict]:
        """Get pending commands for a specific panel slot"""
        pending = []
        for cmd_id, cmd in self.commands.items():
            if cmd["slot"] == slot and cmd["status"] == "PENDING":
                pending.append(cmd)
        return pending
    
    def update_command_status(self, command_id: str, status: str, result: dict = None) -> bool:
        """Update command status"""
        if command_id not in self.commands:
            return False
        
        self.commands[command_id]["status"] = status
        self.commands[command_id]["executed_at"] = datetime.now().isoformat()
        if result:
            self.commands[command_id]["result"] = result
        self.save()
        return True
    
    def get_command(self, command_id: str) -> Optional[Dict]:
        """Get command by ID"""
        return self.commands.get(command_id)
    
    def list_all_commands(self) -> List[Dict]:
        """List all commands"""
        return list(self.commands.values())
    
    def list_commands_by_slot(self, slot: int) -> List[Dict]:
        """List all commands for a specific slot"""
        return [cmd for cmd in self.commands.values() if cmd["slot"] == slot]

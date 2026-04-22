import os
import json
import time
from datetime import datetime
from typing import Dict, List

class PanelRegistry:
    """Registry untuk menyimpan dan mengelola data panel instances"""
    
    def __init__(self, registry_file: str = "panel_registry.json"):
        self.registry_file = registry_file
        self.panels: Dict = {}
        self.load()
    
    def load(self):
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, 'r') as f:
                    self.panels = json.load(f)
            except:
                self.panels = {}
    
    def save(self):
        try:
            with open(self.registry_file, 'w') as f:
                json.dump(self.panels, f, indent=2)
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def register_panel(self, slot: int, ip: str, url: str, port: int = 7860) -> bool:
        try:
            panel_id = f"panel_{slot}"
            self.panels[panel_id] = {
                "slot": slot,
                "ip": ip,
                "url": url,
                "port": port,
                "status": "ONLINE",
                "registered_at": datetime.now().isoformat(),
                "last_heartbeat": datetime.now().isoformat(),
                "process_state": "IDLE",
                "data": {"emails": 0, "links": 0}
            }
            self.save()
            return True
        except:
            return False
    
    def update_heartbeat(self, slot: int, state: str, data: dict = None) -> bool:
        try:
            panel_id = f"panel_{slot}"
            if panel_id not in self.panels:
                return False
            
            self.panels[panel_id]["last_heartbeat"] = datetime.now().isoformat()
            self.panels[panel_id]["process_state"] = state
            self.panels[panel_id]["status"] = "ONLINE"
            if data:
                self.panels[panel_id]["data"] = data
            self.save()
            return True
        except:
            return False
    
    def get_status_summary(self) -> Dict:
        summary = {"total_panels": len(self.panels), "online": 0, "offline": 0, "busy": 0, "idle": 0, "panels": []}
        for panel_id, panel_data in self.panels.items():
            slot = panel_data["slot"]
            status = panel_data["status"]
            state = panel_data["process_state"]
            
            if status == "ONLINE":
                summary["online"] += 1
                if state.startswith("BUSY"):
                    summary["busy"] += 1
                else:
                    summary["idle"] += 1
            else:
                summary["offline"] += 1
            
            summary["panels"].append({
                "slot": slot,
                "ip": panel_data["ip"],
                "status": status,
                "state": state,
                "data": panel_data["data"],
                "last_heartbeat": panel_data["last_heartbeat"]
            })
        return summary

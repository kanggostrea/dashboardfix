import requests
import threading
import time
from panel_registry import PanelRegistry

class PanelDiscoveryService:
    def __init__(self, registry: PanelRegistry, scan_interval: int = 30):
        self.registry = registry
        self.scan_interval = scan_interval
        self.running = False
        self.thread = None
    
    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._discovery_loop, daemon=True)
        self.thread.start()
    
    def _discovery_loop(self):
        while self.running:
            try:
                summary = self.registry.get_status_summary()
                print(f"📊 Status: {summary['online']} online, {summary['offline']} offline, {summary['busy']} busy")
                time.sleep(self.scan_interval)
            except Exception as e:
                print(f"❌ Error: {e}")
                time.sleep(5)

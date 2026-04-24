import os
import json
import time
from datetime import datetime
from typing import Dict

class PanelRegistry:
    def __init__(self, registry_file: str = \"panel_registry.json\"):
        self.registry_file = registry_file
        self.panels: Dict = {}
        self.load()
    
    def load(self):
        try:
            if os.path.exists(self.registry_file):
                content = open(self.registry_file, 'r').read().strip()
                if content:
                    self.panels = json.loads(content)
                    print(f'✅ [REGISTRY] Loaded {len(self.panels)} panels', flush=True)
                else:
                    self.panels = {}
                    self.save()
            else:
                self.panels = {}
                self.save()
        except Exception as e:
            print(f'⚠️ [REGISTRY] Load error: {e}, reset to empty', flush=True)
            self.panels = {}
            self.save()
    
    def save(self):
        try:
            with open(self.registry_file, 'w') as f:
                json.dump(self.panels, f, indent=2)
        except Exception as e:
            print(f'❌ [REGISTRY] Save error: {e}', flush=True)
    
    def register_panel(self, slot: int, ip: str, url: str, port: int = 7860) -> bool:
        try:
            panel_id = f'panel_{slot}'
            self.panels[panel_id] = {
                'slot': slot,
                'ip': ip,
                'url': url,
                'port': port,
                'status': 'ONLINE',
                'registered_at': datetime.now().isoformat(),
                'last_heartbeat': datetime.now().isoformat(),
                'process_state': 'IDLE',
                'data': {'emails': 0, 'links': 0}
            }
            self.save()
            print(f'✅ [REGISTRY] Panel slot {slot} saved to JSON', flush=True)
            return True
        except Exception as e:
            print(f'❌ [REGISTRY] register_panel error: {e}', flush=True)
            return False
    
    def update_heartbeat(self, slot: int, state: str, data: dict = None) -> bool:
        try:
            panel_id = f'panel_{slot}'
            
            # Auto-create kalau belum ada
            if panel_id not in self.panels:
                print(f'⚠️ [REGISTRY] Panel {slot} tidak ada, auto-create dari heartbeat', flush=True)
                self.panels[panel_id] = {
                    'slot': slot,
                    'ip': 'unknown',
                    'url': 'unknown',
                    'port': 7860,
                    'status': 'ONLINE',
                    'registered_at': datetime.now().isoformat(),
                    'last_heartbeat': datetime.now().isoformat(),
                    'process_state': 'IDLE',
                    'data': {'emails': 0, 'links': 0}
                }
            
            self.panels[panel_id]['last_heartbeat'] = datetime.now().isoformat()
            self.panels[panel_id]['process_state'] = state
            self.panels[panel_id]['status'] = 'ONLINE'
            if data:
                self.panels[panel_id]['data'] = data
            self.save()
            return True
        except Exception as e:
            print(f'❌ [REGISTRY] update_heartbeat error: {e}', flush=True)
            return False
    
    def get_status_summary(self) -> Dict:
        # Reload dari file dulu biar selalu fresh
        self.load()
        
        summary = {
            'total_panels': len(self.panels),
            'online': 0,
            'offline': 0,
            'busy': 0,
            'idle': 0,
            'panels': []
        }
        
        current_time = datetime.now()
        
        for panel_id, panel_data in self.panels.items():
            try:
                last_hb = datetime.fromisoformat(panel_data['last_heartbeat'])
                elapsed = (current_time - last_hb).total_seconds()
                panel_data['status'] = 'ONLINE' if elapsed <= 120 else 'OFFLINE'
            except:
                panel_data['status'] = 'OFFLINE'
            
            status = panel_data['status']
            state = panel_data['process_state']
            
            if status == 'ONLINE':
                summary['online'] += 1
                if state.startswith('BUSY'):
                    summary['busy'] += 1
                else:
                    summary['idle'] += 1
            else:
                summary['offline'] += 1
            
            summary['panels'].append({
                'slot': panel_data['slot'],
                'ip': panel_data['ip'],
                'status': status,
                'state': state,
                'data': panel_data['data'],
                'last_heartbeat': panel_data['last_heartbeat']
            })
        
        return summary

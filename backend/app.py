from flask import Flask, request, jsonify
from flask_cors import CORS
from panel_registry import PanelRegistry
from discovery_service import PanelDiscoveryService
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

registry = PanelRegistry()
discovery_service = PanelDiscoveryService(registry)

@app.before_request
def startup():
    if not discovery_service.running:
        discovery_service.start()

AUTH_KEY = os.getenv("DASHBOARD_AUTH_KEY", "GHOST_SECRET_2026")

@app.before_request
def check_auth():
    """Skip auth untuk static files, health, dan root"""
    # ✅ FIX: Check function names, not string names
    if request.path == '/' or request.path.startswith('/static/') or request.path == '/health':
        return
    if request.path.startswith('/favicon'):
        return
    
    # Require auth untuk /api/*
    if request.path.startswith('/api/'):
        if request.headers.get("X-Auth-Key") != AUTH_KEY:
            print(f"❌ [AUTH] Unauthorized: {request.method} {request.path}", flush=True)
            return jsonify({"error": "Unauthorized"}), 401

# ============================================
# SERVE STATIC FILES
# ============================================
@app.route('/')
def serve_index():
    """Serve dashboard index.html"""
    try:
        with open('frontend/index.html', 'r') as f:
            print(f"✅ [SERVE] Serving index.html", flush=True)
            return f.read()
    except FileNotFoundError:
        print(f"⚠️ [SERVE] frontend/index.html not found", flush=True)
        return """
        <!DOCTYPE html>
<html>
<head>
    <title>GHOST COMMANDER - Dashboard</title>
    <link rel="stylesheet" href="/css/styles.css">
    <style>
        .command-section {
            background: #16213e;
            border: 2px solid #0f3460;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
        }
        .command-form {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }
        .command-form input, .command-form select, .command-form button {
            padding: 10px;
            border: 1px solid #0f3460;
            background: #0f1419;
            color: #ecf0f1;
            border-radius: 4px;
            cursor: pointer;
        }
        .command-form button:hover {
            background: #0f3460;
        }
        .command-list {
            margin-top: 20px;
        }
        .command-item {
            background: #16213e;
            padding: 10px;
            margin: 5px 0;
            border-radius: 4px;
            font-size: 0.9rem;
        }
        .status-pending { color: #f39c12; }
        .status-executing { color: #3498db; }
        .status-success { color: #27ae60; }
        .status-failed { color: #e74c3c; }
    </style>
</head>
<body>
    <div class="navbar">
        <h1>👻 GHOST COMMANDER</h1>
        <div class="navbar-stats">
            <div>ONLINE: <span id="stat-online">0</span></div>
            <div>BUSY: <span id="stat-busy">0</span></div>
        </div>
    </div>

    <div class="container">
        <!-- PANELS TAB -->
        <div id="panels-tab">
            <h2>Panels</h2>
            <div class="panels-grid" id="panels-grid"></div>
        </div>

        <!-- COMMANDS TAB -->
        <div class="command-section">
            <h2>Send Command</h2>
            <div class="command-form">
                <input type="number" id="slot-input" placeholder="Slot" min="1" value="1">
                <select id="action-select">
                    <option value="start_login">Start Login</option>
                    <option value="start_loop">Start Loop</option>
                    <option value="stop">Stop</option>
                    <option value="clean_ram">Clean RAM</option>
                </select>
                <button onclick="sendCommand()">Send Command</button>
            </div>

            <h2>Command History</h2>
            <div id="command-list" class="command-list"></div>
        </div>
    </div>

    <script>
        const API_BASE = '/api';
        const AUTH_KEY = 'GHOST_SECRET_2026';

        // Load panels setiap 3 detik
        document.addEventListener('DOMContentLoaded', () => {
            loadPanels();
            loadCommands();
            setInterval(loadPanels, 3000);
            setInterval(loadCommands, 2000);
        });

        async function loadPanels() {
            try {
                const response = await fetch(`${API_BASE}/status`, {
                    headers: { 'X-Auth-Key': AUTH_KEY }
                });
                const data = await response.json();
                renderPanels(data);
            } catch (error) {
                console.error('Error:', error);
            }
        }

        function renderPanels(data) {
            const grid = document.getElementById('panels-grid');
            grid.innerHTML = '';
            
            document.getElementById('stat-online').textContent = data.online;
            document.getElementById('stat-busy').textContent = data.busy;
            
            data.panels.forEach(panel => {
                const card = document.createElement('div');
                card.className = 'panel-card';
                card.innerHTML = `
                    <div class="panel-slot">SLOT ${panel.slot}</div>
                    <span class="status-badge ${panel.status.toLowerCase()}">${panel.status}</span>
                    <div style="margin-top: 1rem; font-size: 0.85rem;">
                        <div>IP: ${panel.ip}</div>
                        <div>State: ${panel.state}</div>
                        <div>Emails: ${panel.data.emails}</div>
                        <div>Links: ${panel.data.links}</div>
                    </div>
                    <div style="margin-top: 10px; gap: 5px; display: flex; flex-wrap: wrap;">
                        <button onclick="executeAction(${panel.slot}, 'start_login')" style="flex: 1; padding: 5px; background: #0f3460; cursor: pointer; border: none; color: #ecf0f1; border-radius: 4px;">Login</button>
                        <button onclick="executeAction(${panel.slot}, 'start_loop')" style="flex: 1; padding: 5px; background: #0f3460; cursor: pointer; border: none; color: #ecf0f1; border-radius: 4px;">Loop</button>
                        <button onclick="executeAction(${panel.slot}, 'stop')" style="flex: 1; padding: 5px; background: #e74c3c; cursor: pointer; border: none; color: #ecf0f1; border-radius: 4px;">Stop</button>
                    </div>
                `;
                grid.appendChild(card);
            });
        }

        async function sendCommand() {
            const slot = parseInt(document.getElementById('slot-input').value);
            const action = document.getElementById('action-select').value;

            await executeAction(slot, action);
        }

        async function executeAction(slot, action) {
            try {
                const response = await fetch(`${API_BASE}/command/create`, {
                    method: 'POST',
                    headers: {
                        'X-Auth-Key': AUTH_KEY,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        slot: slot,
                        action: action,
                        payload: {}
                    })
                });

                if (response.ok) {
                    const data = await response.json();
                    alert(`✅ Command sent: ${action} to slot ${slot}`);
                    loadCommands();
                } else {
                    alert(`❌ Error: ${response.status}`);
                }
            } catch (error) {
                console.error('Error:', error);
                alert(`❌ Error: ${error.message}`);
            }
        }

        async function loadCommands() {
            try {
                const response = await fetch(`${API_BASE}/command/list`, {
                    headers: { 'X-Auth-Key': AUTH_KEY }
                });
                const commands = await response.json();
                renderCommands(commands);
            } catch (error) {
                console.error('Error:', error);
            }
        }

        function renderCommands(commands) {
            const list = document.getElementById('command-list');
            
            if (!commands || commands.length === 0) {
                list.innerHTML = '<p style="color: #999;">No commands yet</p>';
                return;
            }

            list.innerHTML = commands.map(cmd => `
                <div class="command-item">
                    <strong>Slot ${cmd.slot}</strong> - ${cmd.action}
                    <span class="status-${cmd.status.toLowerCase()}">[${cmd.status}]</span>
                    <br>
                    <small>ID: ${cmd.id.substring(0, 8)}...</small>
                </div>
            `).join('');
        }
    </script>
</body>
</html>
        """

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    print(f"📊 [HEALTH] Health check", flush=True)
    return jsonify({"status": "healthy"}), 200

# ============================================
# API: COMMANDS (Baru)
# ============================================

@app.route('/api/command/create', methods=['POST'])
def create_command():
    """Create command untuk mengirim task ke panel"""
    try:
        data = request.json or {}
        
        slot = data.get('slot')
        action = data.get('action')  # start_login, start_loop, stop, clean_ram
        payload = data.get('payload', {})
        
        print(f"➕ [COMMAND] Creating: slot={slot}, action={action}", flush=True)
        
        if not slot or not action:
            return jsonify({"error": "Missing slot or action"}), 400
        
        # Simpan command (untuk sekarang, bisa pake in-memory dict atau file)
        # TODO: Pakai database untuk production
        if not hasattr(app, 'commands'):
            app.commands = {}
        
        import uuid
        cmd_id = str(uuid.uuid4())
        app.commands[cmd_id] = {
            "id": cmd_id,
            "slot": slot,
            "action": action,
            "payload": payload,
            "status": "PENDING"
        }
        
        print(f"✅ [COMMAND] Created: {cmd_id}", flush=True)
        return jsonify({
            "id": cmd_id,
            "status": "PENDING"
        }), 201
        
    except Exception as e:
        print(f"❌ [COMMAND] Error: {e}", flush=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/command/get/<int:slot>', methods=['GET'])
def get_commands(slot):
    """Panel pull commands untuk slot tertentu"""
    try:
        if not hasattr(app, 'commands'):
            app.commands = {}
        
        # Filter commands untuk slot ini yang PENDING
        pending_cmds = [
            cmd for cmd in app.commands.values() 
            if cmd.get('slot') == slot and cmd.get('status') == 'PENDING'
        ]
        
        print(f"📥 [COMMAND] Slot {slot} pulling {len(pending_cmds)} commands", flush=True)
        
        return jsonify(pending_cmds), 200
        
    except Exception as e:
        print(f"❌ [COMMAND] Error: {e}", flush=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/command/update/<cmd_id>', methods=['POST'])
def update_command(cmd_id):
    """Panel report command status"""
    try:
        data = request.json or {}
        
        if not hasattr(app, 'commands'):
            app.commands = {}
        
        if cmd_id not in app.commands:
            return jsonify({"error": "Command not found"}), 404
        
        # Update status
        app.commands[cmd_id]['status'] = data.get('status', 'UNKNOWN')
        app.commands[cmd_id]['result'] = data.get('result')
        
        print(f"🔄 [COMMAND] Updated {cmd_id}: {data.get('status')}", flush=True)
        
        return jsonify({"status": "updated"}), 200
        
    except Exception as e:
        print(f"❌ [COMMAND] Error: {e}", flush=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/command/list', methods=['GET'])
def list_commands():
    """Get all commands"""
    if not hasattr(app, 'commands'):
        app.commands = {}
    
    return jsonify(list(app.commands.values())), 200
    
# ============================================
# API: PANEL REGISTRATION
# ============================================
@app.route('/api/register', methods=['POST'])
def register_panel():
    """Register new panel to dashboard"""
    try:
        data = request.json or {}
        
        # Get panel data
        slot = data.get('slot')
        ip = data.get('ip')
        url = data.get('url')
        port = data.get('port', 7860)
        
        print(f"📡 [REGISTER] Incoming: slot={slot}, ip={ip}, url={url}, port={port}", flush=True)
        
        # Validate
        if not all([slot, ip, url]):
            print(f"❌ [REGISTER] Missing fields: slot={slot}, ip={ip}, url={url}", flush=True)
            return jsonify({
                "error": "Missing fields",
                "received": {"slot": slot, "ip": ip, "url": url}
            }), 400
        
        # Register
        registry.register_panel(slot, ip, url, port)
        print(f"✅ [REGISTER] Panel registered successfully: Slot {slot}", flush=True)
        
        return jsonify({
            "status": "registered",
            "slot": slot,
            "message": f"Panel slot {slot} registered successfully"
        }), 200
        
    except Exception as e:
        print(f"❌ [REGISTER] Exception: {e}", flush=True)
        return jsonify({"error": str(e)}), 500

# ============================================
# API: HEARTBEAT
# ============================================
@app.route('/api/heartbeat', methods=['POST'])
def heartbeat():
    """Update panel heartbeat status"""
    try:
        data = request.json or {}
        
        slot = data.get('slot')
        state = data.get('state')
        panel_data = data.get('data', {})
        
        print(f"💓 [HEARTBEAT] Slot {slot}: {state} | Emails: {panel_data.get('emails', 0)}, Links: {panel_data.get('links', 0)}", flush=True)
        
        if not slot or not state:
            print(f"⚠️ [HEARTBEAT] Missing slot or state", flush=True)
            return jsonify({"error": "Missing slot or state"}), 400
        
        registry.update_heartbeat(slot, state, panel_data)
        return jsonify({"status": "updated"}), 200
        
    except Exception as e:
        print(f"❌ [HEARTBEAT] Exception: {e}", flush=True)
        return jsonify({"error": str(e)}), 500

# ============================================
# API: STATUS
# ============================================
@app.route('/api/status', methods=['GET'])
def status():
    """Get dashboard status summary"""
    try:
        summary = registry.get_status_summary()
        print(f"📊 [STATUS] Online: {summary['online']}, Busy: {summary['busy']}, Idle: {summary['idle']}", flush=True)
        return jsonify(summary), 200
    except Exception as e:
        print(f"❌ [STATUS] Exception: {e}", flush=True)
        return jsonify({"error": str(e)}), 500

# ============================================
# ERROR HANDLERS
# ============================================
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Server error"}), 500

if __name__ == '__main__':
    print("🚀 [DASHBOARD] Starting GHOST COMMANDER on port 5000", flush=True)
    app.run(host='0.0.0.0', port=5000, debug=False)

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
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Courier New', monospace;
            background-color: #0f0f1e;
            color: #ecf0f1;
        }

        .navbar {
            background: linear-gradient(135deg, #1a1a2e, #0f3460);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #2d2d4d;
        }

        .navbar h1 { font-size: 1.5rem; letter-spacing: 2px; }

        .navbar-stats { display: flex; gap: 2rem; }

        .container { padding: 2rem; max-width: 1400px; margin: 0 auto; }

        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid #2d2d4d;
        }

        .tab-btn {
            padding: 10px 20px;
            background: transparent;
            border: none;
            color: #ecf0f1;
            cursor: pointer;
            border-bottom: 3px solid transparent;
            font-weight: bold;
        }

        .tab-btn.active {
            border-bottom-color: #0f3460;
            color: #0f3460;
        }

        .tab-content { display: none; }
        .tab-content.active { display: block; }

        /* PANELS TAB */
        .panels-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1.5rem;
        }

        .panel-card {
            background: linear-gradient(135deg, #16213e, #0f3460);
            border: 2px solid #2d2d4d;
            border-radius: 8px;
            padding: 1.5rem;
            transition: all 0.3s;
        }

        .panel-card:hover {
            border-color: #0f3460;
            box-shadow: 0 0 20px rgba(15, 52, 96, 0.5);
        }

        .panel-slot { font-size: 1.5rem; font-weight: bold; margin-bottom: 1rem; }

        .status-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: bold;
        }

        .status-badge.online { background-color: rgba(39, 174, 96, 0.3); color: #27ae60; }
        .status-badge.offline { background-color: rgba(231, 76, 60, 0.3); color: #e74c3c; }

        .panel-info { margin-top: 1rem; font-size: 0.85rem; }

        .panel-buttons {
            margin-top: 10px;
            gap: 5px;
            display: flex;
            flex-wrap: wrap;
        }

        .panel-buttons button {
            flex: 1;
            padding: 8px;
            background: #0f3460;
            cursor: pointer;
            border: none;
            color: #ecf0f1;
            border-radius: 4px;
            font-size: 0.8rem;
            transition: all 0.2s;
        }

        .panel-buttons button:hover { background: #1a5a8a; }
        .panel-buttons button.stop { background: #e74c3c; }
        .panel-buttons button.stop:hover { background: #c0392b; }

        /* TASK TAB */
        .task-form {
            background: #16213e;
            border: 2px solid #0f3460;
            padding: 20px;
            border-radius: 8px;
            max-width: 600px;
        }

        .form-group {
            margin-bottom: 15px;
        }

        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }

        .form-group input,
        .form-group textarea,
        .form-group select {
            width: 100%;
            padding: 10px;
            background: #0f1419;
            border: 1px solid #0f3460;
            color: #ecf0f1;
            border-radius: 4px;
            font-family: monospace;
        }

        .form-group textarea {
            min-height: 100px;
            resize: vertical;
        }

        .form-group button {
            width: 100%;
            padding: 12px;
            background: #0f3460;
            border: none;
            color: #ecf0f1;
            cursor: pointer;
            border-radius: 4px;
            font-weight: bold;
            transition: all 0.2s;
        }

        .form-group button:hover { background: #1a5a8a; }

        .url-list {
            margin-top: 10px;
        }

        .url-item {
            display: flex;
            gap: 5px;
            margin-bottom: 5px;
        }

        .url-item input { flex: 1; }
        .url-item button {
            width: 40px;
            padding: 8px;
            background: #e74c3c;
            cursor: pointer;
            border: none;
            color: #ecf0f1;
            border-radius: 4px;
        }

        .add-url-btn {
            background: #27ae60;
            padding: 8px 15px;
            border: none;
            color: #ecf0f1;
            cursor: pointer;
            border-radius: 4px;
            margin-top: 10px;
        }

        /* COMMAND HISTORY TAB */
        .command-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .command-item {
            background: #16213e;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #0f3460;
        }

        .command-item.pending { border-left-color: #f39c12; }
        .command-item.executing { border-left-color: #3498db; }
        .command-item.success { border-left-color: #27ae60; }
        .command-item.failed { border-left-color: #e74c3c; }

        .command-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 5px;
        }

        .command-status {
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 0.75rem;
            font-weight: bold;
        }

        .status-pending { background: rgba(243, 156, 18, 0.3); color: #f39c12; }
        .status-executing { background: rgba(52, 152, 219, 0.3); color: #3498db; }
        .status-success { background: rgba(39, 174, 96, 0.3); color: #27ae60; }
        .status-failed { background: rgba(231, 76, 60, 0.3); color: #e74c3c; }
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
        <!-- TABS -->
        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('panels')">Panels</button>
            <button class="tab-btn" onclick="switchTab('task')">Send Task</button>
            <button class="tab-btn" onclick="switchTab('commands')">Command History</button>
        </div>

        <!-- PANELS TAB -->
        <div id="panels" class="tab-content active">
            <h2>Active Panels</h2>
            <div class="panels-grid" id="panels-grid"></div>
        </div>

        <!-- TASK TAB -->
        <div id="task" class="tab-content">
            <h2>Send Task to Panel</h2>
            <div class="task-form">
                <div class="form-group">
                    <label>Select Panel (Slot):</label>
                    <select id="slot-select">
                        <option value="">-- Select Panel --</option>
                    </select>
                </div>

                <div class="form-group">
                    <label>Email Address:</label>
                    <input type="email" id="email-input" placeholder="example@gmail.com" required>
                </div>

                <div class="form-group">
                    <label>Password:</label>
                    <input type="password" id="password-input" placeholder="Enter password" required>
                </div>

                <div class="form-group">
                    <label>URLs (one per line):</label>
                    <textarea id="urls-input" placeholder="https://example.com/1&#10;https://example.com/2&#10;https://example.com/3"></textarea>
                </div>

                <div class="form-group">
                    <button onclick="sendTask()">Send Task</button>
                </div>
            </div>
        </div>

        <!-- COMMAND HISTORY TAB -->
        <div id="commands" class="tab-content">
            <h2>Command History</h2>
            <div id="command-list" class="command-list"></div>
        </div>
    </div>

    <script>
        const API_BASE = '/api';
        const AUTH_KEY = 'GHOST_SECRET_2026';

        // Load data on startup
        document.addEventListener('DOMContentLoaded', () => {
            loadPanels();
            loadCommands();
            setInterval(loadPanels, 2000);  // ✅ Realtime update setiap 2 detik
            setInterval(loadCommands, 3000);
        });

        // Tab switching
        function switchTab(tab) {
            // Hide all
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            
            // Show selected
            document.getElementById(tab).classList.add('active');
            event.target.classList.add('active');
        }

        // ============================================
        // PANELS TAB
        // ============================================
        async function loadPanels() {
            try {
                const response = await fetch(`${API_BASE}/status`, {
                    headers: { 'X-Auth-Key': AUTH_KEY }
                });
                const data = await response.json();
                renderPanels(data);
                updateSlotSelect(data.panels);
            } catch (error) {
                console.error('Error loading panels:', error);
            }
        }

        function renderPanels(data) {
            const grid = document.getElementById('panels-grid');
            grid.innerHTML = '';
            
            document.getElementById('stat-online').textContent = data.online;
            document.getElementById('stat-busy').textContent = data.busy;
            
            if (data.panels.length === 0) {
                grid.innerHTML = '<p style="grid-column: 1/-1; color: #999;">No panels connected</p>';
                return;
            }
            
            data.panels.forEach(panel => {
                const card = document.createElement('div');
                card.className = 'panel-card';
                card.innerHTML = `
                    <div class="panel-slot">SLOT ${panel.slot}</div>
                    <span class="status-badge ${panel.status.toLowerCase()}">${panel.status}</span>
                    <div class="panel-info">
                        <div>IP: ${panel.ip}</div>
                        <div>State: ${panel.state}</div>
                        <div>Emails: ${panel.data.emails}</div>
                        <div>Links: ${panel.data.links}</div>
                    </div>
                    <div class="panel-buttons">
                        <button onclick="executeAction(${panel.slot}, 'start_login')">Login</button>
                        <button onclick="executeAction(${panel.slot}, 'start_loop')">Loop</button>
                        <button class="stop" onclick="executeAction(${panel.slot}, 'stop')">Stop</button>
                    </div>
                `;
                grid.appendChild(card);
            });
        }

        function updateSlotSelect(panels) {
            const select = document.getElementById('slot-select');
            const currentValue = select.value;
            
            select.innerHTML = '<option value="">-- Select Panel --</option>';
            panels.forEach(panel => {
                const option = document.createElement('option');
                option.value = panel.slot;
                option.textContent = `Slot ${panel.slot} (${panel.status} - ${panel.state})`;
                select.appendChild(option);
            });
            
            if (currentValue) select.value = currentValue;
        }

        // ============================================
        // TASK TAB
        // ============================================
        async function sendTask() {
            const slot = parseInt(document.getElementById('slot-select').value);
            const email = document.getElementById('email-input').value;
            const password = document.getElementById('password-input').value;
            const urlsText = document.getElementById('urls-input').value;
            const urls = urlsText.split('\n').filter(u => u.trim());

            // Validation
            if (!slot || !email || !password || urls.length === 0) {
                alert('❌ Please fill all fields!');
                return;
            }

            try {
                // Create command dengan payload
                const response = await fetch(`${API_BASE}/command/create`, {
                    method: 'POST',
                    headers: {
                        'X-Auth-Key': AUTH_KEY,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        slot: slot,
                        action: 'start_login',
                        payload: {
                            email: email,
                            password: password,
                            urls: urls
                        }
                    })
                });

                if (response.ok) {
                    const data = await response.json();
                    alert(`✅ Task sent to Slot ${slot}!\nCommand ID: ${data.id}`);
                    
                    // Clear form
                    document.getElementById('email-input').value = '';
                    document.getElementById('password-input').value = '';
                    document.getElementById('urls-input').value = '';
                    
                    // Reload commands
                    loadCommands();
                } else {
                    alert(`❌ Error: ${response.status}`);
                }
            } catch (error) {
                console.error('Error:', error);
                alert(`❌ Error: ${error.message}`);
            }
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
                    console.log(`✅ ${action} sent to slot ${slot}`);
                    loadCommands();
                }
            } catch (error) {
                console.error('Error:', error);
            }
        }

        // ============================================
        // COMMAND HISTORY TAB
        // ============================================
        async function loadCommands() {
            try {
                const response = await fetch(`${API_BASE}/command/list`, {
                    headers: { 'X-Auth-Key': AUTH_KEY }
                });
                const commands = await response.json();
                renderCommands(commands);
            } catch (error) {
                console.error('Error loading commands:', error);
            }
        }

        function renderCommands(commands) {
            const list = document.getElementById('command-list');
            
            if (!commands || commands.length === 0) {
                list.innerHTML = '<p style="color: #999;">No commands yet</p>';
                return;
            }

            // Sort by newest first
            commands.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));

            list.innerHTML = commands.map((cmd, idx) => `
                <div class="command-item ${(cmd.status || 'pending').toLowerCase()}">
                    <div class="command-header">
                        <div><strong>Slot ${cmd.slot} - ${cmd.action}</strong></div>
                        <span class="command-status status-${(cmd.status || 'pending').toLowerCase()}">
                            ${(cmd.status || 'PENDING').toUpperCase()}
                        </span>
                    </div>
                    <div style="font-size: 0.85rem; color: #999;">
                        ID: ${cmd.id ? cmd.id.substring(0, 8) : 'N/A'}...
                        ${cmd.created_at ? '| ' + new Date(cmd.created_at).toLocaleTimeString() : ''}
                    </div>
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
    """Get dashboard status summary dengan offline detection"""
    try:
        summary = registry.get_status_summary()
        
        # ✅ Mark panels offline jika heartbeat lama
        import time as time_module
        current_time = time_module.time()
        
        # Check each panel's last heartbeat
        for panel_id, panel_data in registry.panels.items():
            try:
                from datetime import datetime
                last_hb = datetime.fromisoformat(panel_data['last_heartbeat'])
                last_hb_seconds = (datetime.now() - last_hb).total_seconds()
                
                # Offline jika > 60 detik tanpa heartbeat
                if last_hb_seconds > 60:
                    panel_data['status'] = 'OFFLINE'
                else:
                    panel_data['status'] = 'ONLINE'
            except:
                pass
        
        # Recalculate summary
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

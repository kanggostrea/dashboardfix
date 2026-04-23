from flask import Flask, request, jsonify
from flask_cors import CORS
from panel_registry import PanelRegistry
from discovery_service import PanelDiscoveryService
from command_manager import CommandManager
from command_dispatcher import CommandDispatcher
import os
from dotenv import load_dotenv
import requests

load_dotenv()
app = Flask(__name__)
CORS(app)

registry = PanelRegistry()
discovery_service = PanelDiscoveryService(registry)
command_manager = CommandManager()
command_dispatcher = CommandDispatcher(registry, command_manager)

@app.before_request
def startup():
    if not discovery_service.running:
        discovery_service.start()
    if not command_dispatcher.running:
        command_dispatcher.start()

AUTH_KEY = os.getenv("DASHBOARD_AUTH_KEY", "GHOST_SECRET_2026")

@app.before_request
def check_auth():
    if request.endpoint in ['index', 'health']:
        return
    if request.headers.get("X-Auth-Key") != AUTH_KEY:
        return jsonify({"error": "Unauthorized"}), 401

@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>GHOST COMMANDER - Dashboard</title>
        <link rel="stylesheet" href="/css/styles.css">
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
            <div class="panels-grid" id="panels-grid"></div>
        </div>
        <script src="/js/app.js"></script>
    </body>
    </html>
    """

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

# ==========================================
# PANEL REGISTRATION & HEARTBEAT ENDPOINTS
# ==========================================

@app.route('/api/register', methods=['POST'])
def register_panel():
    try:
        data = request.json
        slot, ip, url = data.get('slot'), data.get('ip'), data.get('url')
        port = data.get('port', 7860)
        if not all([slot, ip, url]):
            return jsonify({"error": "Missing fields"}), 400
        registry.register_panel(slot, ip, url, port)
        return jsonify({"status": "registered", "slot": slot}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/heartbeat', methods=['POST'])
def heartbeat():
    try:
        data = request.json
        slot, state = data.get('slot'), data.get('state')
        registry.update_heartbeat(slot, state, data.get('data'))
        return jsonify({"status": "updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify(registry.get_status_summary()), 200

# ==========================================
# COMMAND MANAGEMENT ENDPOINTS
# ==========================================

@app.route('/api/command/create', methods=['POST'])
def create_command():
    """Create a new command for a panel"""
    try:
        data = request.json
        slot = data.get('slot')
        action = data.get('action')
        payload = data.get('payload', {})
        
        if not slot or not action:
            return jsonify({"error": "Missing slot or action"}), 400
        
        command_id = command_manager.create_command(slot, action, payload)
        return jsonify({
            "id": command_id,
            "status": "created",
            "slot": slot,
            "action": action
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/command/get/<slot>', methods=['GET'])
def get_commands(slot):
    """Get pending commands for a specific slot (for panel polling)"""
    try:
        slot = int(slot)
        commands = command_manager.get_pending_commands(slot)
        return jsonify({"slot": slot, "commands": commands}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/command/status/<command_id>', methods=['GET'])
def get_command_status(command_id):
    """Get command status"""
    try:
        command = command_manager.get_command(command_id)
        if not command:
            return jsonify({"error": "Command not found"}), 404
        return jsonify(command), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/command/update/<command_id>', methods=['POST'])
def update_command(command_id):
    """Update command status (called by panel after execution)"""
    try:
        data = request.json
        status = data.get('status')
        result = data.get('result')
        
        if not status:
            return jsonify({"error": "Missing status"}), 400
        
        success = command_manager.update_command_status(command_id, status, result)
        if not success:
            return jsonify({"error": "Command not found"}), 404
        
        return jsonify({"id": command_id, "status": status}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/command/list', methods=['GET'])
def list_commands():
    """List all commands with optional filtering"""
    try:
        slot = request.args.get('slot')
        status = request.args.get('status')
        
        if slot:
            commands = command_manager.list_commands_by_slot(int(slot))
        else:
            commands = command_manager.list_all_commands()
        
        if status:
            commands = [c for c in commands if c['status'] == status]
        
        return jsonify({"commands": commands}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/command/list/<slot>', methods=['GET'])
def list_slot_commands(slot):
    """List all commands for a specific slot"""
    try:
        slot = int(slot)
        commands = command_manager.list_commands_by_slot(slot)
        return jsonify({"slot": slot, "commands": commands}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

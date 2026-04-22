from flask import Flask, request, jsonify
from flask_cors import CORS
from panel_registry import PanelRegistry
from discovery_service import PanelDiscoveryService
import os
from dotenv import load_dotenv
import requests

load_dotenv()
app = Flask(__name__)
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
    if request.endpoint in ['index', 'health']:
        return
    if request.headers.get("X-Auth-Key") != AUTH_KEY:
        return jsonify({"error": "Unauthorized"}), 401

@app.route('/', methods=['GET'])
def index():
    return jsonify({"status": "online", "service": "Dashboard API"})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

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
    except:
        return jsonify({"error": "Error"}), 500

@app.route('/api/heartbeat', methods=['POST'])
def heartbeat():
    try:
        data = request.json
        slot, state = data.get('slot'), data.get('state')
        registry.update_heartbeat(slot, state, data.get('data'))
        return jsonify({"status": "updated"}), 200
    except:
        return jsonify({"error": "Error"}), 500

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify(registry.get_status_summary()), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

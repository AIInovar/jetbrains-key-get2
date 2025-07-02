import os
import random
import time
from flask import Flask, jsonify

app = Flask(__name__)

# Configuration
PORT = int(os.getenv('PORT', 8080))
LICENSE_FILE = os.getenv('LICENSE_FILE', 'licenses.txt')

# Load licenses from file
def load_licenses():
    licenses = []
    if os.path.exists(LICENSE_FILE):
        with open(LICENSE_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith(('#', '!', '-')):
                    # Extract just the license key part
                    license_key = line.split(' | ')[0] if ' | ' in line else line
                    licenses.append(license_key)
    return licenses

# Generate a fake license server response
def generate_license_response():
    return {
        "licenseId": f"{int(time.time())}-{random.randint(1000,9999)}",
        "licenseeName": "Fake License Server User",
        "assigneeName": "Fake License Server User",
        "assigneeEmail": "user@fakelicense.com",
        "licenseRestriction": "",
        "checkConcurrentUse": False,
        "products": [{"code": "II", "fallbackDate": "2099-12-31"}],
        "metadata": {"autoProlongated": True},
        "hash": "fakehash",
        "gracePeriodDays": 365,
        "isEligibleForProlongation": True
    }

@app.route('/')
def index():
    return "JetBrains Fake License Server - Use /license for license keys"

@app.route('/license')
def get_license():
    licenses = load_licenses()
    if not licenses:
        return jsonify({"error": "No licenses available"}), 404
    
    # Select a random license key
    license_key = random.choice(licenses)
    
    response = generate_license_response()
    response['licenseKey'] = license_key
    return jsonify(response)

@app.route('/status')
def status():
    licenses = load_licenses()
    return jsonify({
        "status": "active",
        "license_count": len(licenses),
        "server_time": time.strftime('%Y-%m-%d %H:%M:%S')
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=False)

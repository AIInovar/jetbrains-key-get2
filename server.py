import os
import random
import time
import logging
from pathlib import Path
from flask import Flask, jsonify, send_file

app = Flask(__name__)

# Configuration
PORT = int(os.getenv('PORT', '5000'))
LICENSE_FILE = os.getenv('LICENSE_FILE', 'jetbrains_licenses.txt')
CACHE_DIR = os.getenv('CACHE_DIR', 'cache')
LOG_FILE = os.getenv('LOG_FILE', 'logs/server.log')

# Ensure directories exist
os.makedirs(os.path.dirname(os.path.abspath(LOG_FILE)), exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_license_file_path():
    """Get the absolute path to the license file."""
    return os.path.abspath(LICENSE_FILE)

def load_licenses():
    """Load and validate licenses from the license file."""
    licenses = set()
    license_file = get_license_file_path()
    
    if not os.path.exists(license_file):
        logger.warning(f"License file not found: {license_file}")
        return list(licenses)
    
    try:
        with open(license_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith(('#', '!', '-', '//')):
                    continue
                # Extract just the license key part if it's in a formatted line
                license_key = line.split('|')[0].strip() if '|' in line else line
                if len(license_key) >= 16:  # Basic validation
                    licenses.add(license_key)
                    
        logger.info(f"Loaded {len(licenses)} valid licenses from {license_file}")
        return sorted(licenses)
        
    except Exception as e:
        logger.error(f"Error loading licenses from {license_file}: {str(e)}")
        return []

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
    """Main endpoint with usage information."""
    return """
    <h1>JetBrains License Server</h1>
    <p>Endpoints:</p>
    <ul>
        <li><code>GET /license</code> - Get a random license key</li>
        <li><code>GET /licenses</code> - List all license keys</li>
        <li><code>GET /download</code> - Download all licenses as text file</li>
        <li><code>GET /health</code> - Health check endpoint</li>
        <li><code>GET /status</code> - Server status</li>
    </ul>
    """

@app.route('/license')
def get_license():
    """Get a random license key."""
    try:
        licenses = load_licenses()
        if not licenses:
            logger.warning("No valid licenses available")
            return jsonify({"error": "No valid licenses available"}), 404
        
        return jsonify({
            "licenseKey": random.choice(licenses),
            "metadata": {
                "total_licenses": len(licenses),
                "server_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "license_file": get_license_file_path()
            }
        })
    except Exception as e:
        logger.error(f"Error in /license: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route('/licenses')
def list_licenses():
    """List all available license keys."""
    try:
        licenses = load_licenses()
        return jsonify({
            "licenses": licenses,
            "count": len(licenses),
            "server_time": time.strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as e:
        logger.error(f"Error in /licenses: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route('/download')
def download_licenses():
    """Download all licenses as a text file."""
    try:
        license_file = get_license_file_path()
        if not os.path.exists(license_file):
            return jsonify({"error": "License file not found"}), 404
            
        return send_file(
            license_file,
            as_attachment=True,
            download_name=f"jetbrains_licenses_{time.strftime('%Y%m%d')}.txt",
            mimetype='text/plain'
        )
    except Exception as e:
        logger.error(f"Error in /download: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route('/health')
def health_check():
    """Health check endpoint."""
    try:
        licenses = load_licenses()
        if not licenses:
            return jsonify({"status": "unhealthy"}), 500
        
        return jsonify({"status": "healthy"})
    except Exception as e:
        logger.error(f"Error in /health: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

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

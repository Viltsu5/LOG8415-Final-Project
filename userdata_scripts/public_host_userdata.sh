#!/bin/bash

# Redirect all output to a log file
exec > /home/ubuntu/gatekeeper_userdata.log 2>&1

# Update and install Python and pip
apt-get update -y
apt-get install -y python3 python3-pip

# Install Flask and requests
pip3 install flask requests --break-system-packages;

# Create the Python script
cat <<EOF > /home/ubuntu/gatekeeper.py
from flask import Flask, request, jsonify, Response
import requests
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(filename='/home/ubuntu/gatekeeper.log', level=logging.INFO, format='%(asctime)s %(message)s')

# Trusted host URL
TRUSTED_HOST_URL = 'http://172.31.32.104:5000/forward'
TRUSTED_HOST_LOGS_URL = 'http://172.31.32.104:5000/logs'

@app.route('/forward', methods=['POST'])
def forward():
    data = request.json
    logging.info(f"Received data: {data}")
    
    try:
        response = requests.post(TRUSTED_HOST_URL, json=data)
        response.raise_for_status()
        logging.info(f"Forwarded data to trusted host: {data}")
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        logging.error(f"Error forwarding data to trusted host: {e}")
        return str(e), 500

@app.route('/logs', methods=['GET'])
def get_logs():
    try:
        response = requests.get(TRUSTED_HOST_LOGS_URL)
        response.raise_for_status()
        logging.info("Fetched logs from trusted host")
        return Response(response.content, mimetype='text/plain')
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching logs from trusted host: {e}")
        return str(e), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)
EOF

# Make the Python script executable
chmod +x /home/ubuntu/gatekeeper.py

# Run the Python script
python3 /home/ubuntu/gatekeeper.py
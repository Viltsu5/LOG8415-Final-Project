#!/bin/bash

# Redirect all output to a log file
exec > /home/ubuntu/trusted_host_userdata.log 2>&1

# Update and install Python and pip
apt-get update -y
apt-get install -y python3 python3-pip

# Install Flask and requests
pip3 install flask requests --break-system-packages;

# Create the Python script
cat <<EOF > /home/ubuntu/trusted_host.py
from flask import Flask, request, jsonify, Response
import requests
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(filename='/home/ubuntu/trusted_host.log', level=logging.INFO, format='%(asctime)s %(message)s')

# Proxy instance URL
PROXY_URL = 'http://172.31.32.103:5000/query'
PROXY_LOGS_URL = 'http://172.31.32.103:5000/logs'

@app.route('/forward', methods=['POST'])
def forward():
    data = request.json
    logging.info(f"Received data: {data}")
    
    try:
        response = requests.post(PROXY_URL, json=data)
        response.raise_for_status()
        logging.info(f"Forwarded data to proxy: {data}")
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        logging.error(f"Error forwarding data to proxy: {e}")
        return str(e), 500

@app.route('/logs', methods=['GET'])
def get_logs():
    try:
        response = requests.get(PROXY_LOGS_URL)
        response.raise_for_status()
        logging.info("Fetched logs from proxy")
        return Response(response.content, mimetype='text/plain')
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching logs from proxy: {e}")
        return str(e), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
EOF

# Make the Python script executable
chmod +x /home/ubuntu/trusted_host.py

# Run the Python script
python3 /home/ubuntu/trusted_host.py
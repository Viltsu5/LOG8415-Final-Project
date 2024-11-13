from flask import Flask, request, jsonify, Response
import requests
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(filename='/home/ubuntu/gatekeeper.log', level=logging.INFO, format='%(asctime)s %(message)s')

# Trusted host URL
TRUSTED_DIRECT_URL = 'http://172.31.32.104:5000/direct'
TRUSTED_RANDOM_URL = 'http://172.31.32.104:5000/random'
TRUSTED_CUSTOMIZED_URL = 'http://172.31.32.104:5000/customized'
TRUSTED_LOGS_URL = 'http://172.31.32.104:5000/logs'

@app.route('/direct', methods=['POST'])
def direct_hit():
    data = request.json
    logging.info(f"Received data: {data}")
    
    try:
        response = requests.post(TRUSTED_DIRECT_URL, json=data)
        response.raise_for_status()
        logging.info(f"Forwarded data to trusted host: {data}")
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        logging.error(f"Error forwarding data to trusted host: {e}")
        return str(e), 500

@app.route('/random', methods=['POST'])
def random_forward():
    data = request.json
    logging.info(f"Received data: {data}")
    
    try:
        response = requests.post(TRUSTED_RANDOM_URL, json=data)
        response.raise_for_status()
        logging.info(f"Forwarded data to trusted host: {data}")
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        logging.error(f"Error forwarding data to trusted host: {e}")
        return str(e), 500

@app.route('/customized', methods=['POST'])
def customized():
    data = request.json
    logging.info(f"Received data: {data}")
    
    try:
        response = requests.post(TRUSTED_CUSTOMIZED_URL, json=data)
        response.raise_for_status()
        logging.info(f"Forwarded data to trusted host: {data}")
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        logging.error(f"Error forwarding data to trusted host: {e}")
        return str(e), 500

@app.route('/logs', methods=['GET'])
def get_logs():
    try:
        response = requests.get(TRUSTED_LOGS_URL)
        response.raise_for_status()
        logging.info("Fetched logs from trusted host")
        return Response(response.content, mimetype='text/plain')
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching logs from trusted host: {e}")
        return str(e), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)
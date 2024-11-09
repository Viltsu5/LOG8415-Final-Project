#!/bin/bash

# Redirect all output to a log file
exec > /home/ubuntu/proxy_userdata.log 2>&1

# Update and install Python and pip
apt-get update -y
apt-get install -y python3 python3-pip

# Install pymysql and Flask
pip3 install pymysql flask --break-system-packages;

# Create the Python script
cat <<EOF > /home/ubuntu/proxy.py
from flask import Flask, request, jsonify
import pymysql
import random
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(filename='/home/ubuntu/proxy.log', level=logging.INFO, format='%(asctime)s %(message)s')

# Database connection details
MANAGER_HOST = '172.31.32.100'
WORKER_HOSTS = ['172.31.32.101', '172.31.32.102']
USER = 'proxy_user'
PASSWORD = 'paita'
DATABASE = 'sakila'

def get_connection(host):
    return pymysql.connect(
        host=host,
        user=USER,
        password=PASSWORD,
        database=DATABASE
    )

def execute_query(query, is_write=False):
    if is_write:
        # Direct hit to manager for write operations
        connection = get_connection(MANAGER_HOST)
        logging.info(f"Executing write query on manager: {query}")
    else:
        # Randomly select a worker for read operations
        worker_host = random.choice(WORKER_HOSTS)
        connection = get_connection(worker_host)
        logging.info(f"Executing read query on worker {worker_host}: {query}")
    
    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            if not is_write:
                result = cursor.fetchall()
                logging.info(f"Query result: {result}")
                return result
            connection.commit()
            logging.info("Write query committed.")
    finally:
        connection.close()

@app.route('/query', methods=['POST'])
def query():
    data = request.json
    query = data.get('query')
    is_write = data.get('is_write', False)
    
    try:
        result = execute_query(query, is_write)
        return jsonify(result), 200
    except Exception as e:
        logging.error(f"Error executing query: {e}")
        return str(e), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
EOF

# Make the Python script executable
chmod +x /home/ubuntu/proxy.py

# Run the Python script
python3 /home/ubuntu/proxy.py
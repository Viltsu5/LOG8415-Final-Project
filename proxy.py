from flask import Flask, request, jsonify, Response
import pymysql
import random
import logging
from ping3 import ping

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

# Check if the query is a write query
def is_write_query(query):
    write_keywords = ['INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER']
    return any(keyword in query.upper() for keyword in write_keywords)

def execute_query(query, host):
    connection = get_connection(host)
    logging.info(f"Executing query on {host}: {query}")
    
    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            
            if not is_write_query(query):
                # Fetch all rows from the result
                result = cursor.fetchall()
                
                # Log
                logging.info(f"Query result: {result}")
                
                # Format the result for JSON respone
                formatted_result = [list(row) for row in result]
                return formatted_result
            
            connection.commit()
            logging.info("Write query committed.")
            
    finally:
        connection.close()


@app.route('/direct', methods=['POST'])
def direct_hit():
    data = request.json
    query = data.get('query')
    
    try:
        result = execute_query(query, MANAGER_HOST)
        return jsonify(result), 200
    except Exception as e:
        logging.error(f"Error executing query: {e}")
        return str(e), 500

@app.route('/random', methods=['POST'])
def random_forward():
    data = request.json
    query = data.get('query')
    is_write = is_write_query(query)
    
    try:
        if is_write:
            result = execute_query(query, MANAGER_HOST)
        else:
            worker_host = random.choice(WORKER_HOSTS)
            result = execute_query(query, worker_host)
        return jsonify(result), 200
    except Exception as e:
        logging.error(f"Error executing query: {e}")
        return str(e), 500

@app.route('/customized', methods=['POST'])
def customized():
    data = request.json
    query = data.get('query')
    is_write = is_write_query(query)
    
    try:
        if is_write:
            result = execute_query(query, MANAGER_HOST)
        else:
            # Log ping results for each worker host
            ping_results = {host: ping(host) for host in WORKER_HOSTS}
            logging.info(f"Ping results: {ping_results}")
            
            # Filter out None values and choose the worker with the least ping time
            valid_ping_results = {host: ping_time for host, ping_time in ping_results.items() if ping_time is not None}
            if not valid_ping_results:
                raise Exception("All workers are unreachable")
            
            worker_host = min(valid_ping_results, key=valid_ping_results.get)
            logging.info(f"Selected worker with least ping time: {worker_host}")
            result = execute_query(query, worker_host)
        return jsonify(result), 200
    except Exception as e:
        logging.error(f"Error executing query: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/logs', methods=['GET'])
def get_logs():
    try:
        with open('/home/ubuntu/proxy.log', 'r') as log_file:
            log_content = log_file.read()
        return Response(log_content, mimetype='text/plain')
    except Exception as e:
        logging.error(f"Error sending log file: {e}")
        return str(e), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
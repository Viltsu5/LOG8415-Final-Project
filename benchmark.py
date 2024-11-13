import requests
import concurrent.futures
import time
from requests.auth import HTTPBasicAuth
import matplotlib.pyplot as plt
from utils import get_public_ip as gp

# Get the public IP of the public host
URL = gp.get_public_ip('Name', 'public-host')
USERNAME = 'admin'
PASSWORD = 'password'
NUM_REQUESTS = 1000

# Sample read query
READ_QUERY = "SELECT * FROM actor WHERE first_name = 'Aarne';"

# Authentication
auth = HTTPBasicAuth(USERNAME, PASSWORD)

# Function to send a write request
def send_write_request(url, index):
    WRITE_QUERY = f"INSERT INTO actor (first_name, last_name) VALUES ('Aarne', 'Alligator{index}');"
    data = {"query": WRITE_QUERY}
    response = requests.post(url, json=data, auth=auth)
    return response.status_code

# Function to send a read request
def send_read_request(url):
    data = {"query": READ_QUERY}
    response = requests.post(url, json=data, auth=auth)
    return response.status_code

# Benchmarking function
def benchmark_test(url):
    start_time = time.time()

    # Send write requests
    with concurrent.futures.ThreadPoolExecutor() as executor:
        write_futures = [executor.submit(send_write_request, url, i) for i in range(NUM_REQUESTS)]
        write_results = [future.result() for future in concurrent.futures.as_completed(write_futures)]

    # Send read requests
    with concurrent.futures.ThreadPoolExecutor() as executor:
        read_futures = [executor.submit(send_read_request, url) for _ in range(NUM_REQUESTS)]
        read_results = [future.result() for future in concurrent.futures.as_completed(read_futures)]

    end_time = time.time()
    duration = end_time - start_time

    return len(write_results), len(read_results), duration

# Plotting function
def plot_results(results):
    labels = ['Direct', 'Random', 'Customized']
    write_counts = [result[0] for result in results]
    read_counts = [result[1] for result in results]
    durations = [result[2] for result in results]

    x = range(len(labels))

    fig, ax1 = plt.subplots()

    ax2 = ax1.twinx()
    ax1.bar(x, write_counts, color='g', width=0.4, align='center', label='Write Requests')
    ax2.bar([p + 0.4 for p in x], read_counts, color='b', width=0.4, align='center', label='Read Requests')

    ax1.set_xlabel('Query Patterns')
    ax1.set_ylabel('Number of Write Requests', color='g')
    ax2.set_ylabel('Number of Read Requests', color='b')
    ax1.set_xticks([p + 0.2 for p in x])
    ax1.set_xticklabels(labels)
    ax1.legend(loc='upper left')
    ax2.legend(loc='upper right')

    plt.title('Benchmark Results')
    plt.show()

# Configuration
def run_benchmark():

    urls = [
        f"http://{URL}:5001/direct",
        f"http://{URL}:5001/random",
        f"http://{URL}:5001/customized"
    ]

    results = []
    for url in urls:
        print(f"Running benchmark for {url}")
        results.append(benchmark_test(url))

    plot_results(results)

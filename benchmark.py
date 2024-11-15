import requests
import concurrent.futures
import time
from requests.auth import HTTPBasicAuth
import matplotlib.pyplot as plt
from utils import get_public_ip as gp
from utils import globals as g


NUM_REQUESTS = 1000
PAUSE_DURATION = 15  # Pause duration in seconds

# Database credentials
with open(g.authentication_path, 'r') as file:
    data = file.read().splitlines()
    USERNAME = data[0]
    PASSWORD = data[1]


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
    write_start_time = time.time()

    # Send write requests
    with concurrent.futures.ThreadPoolExecutor() as executor:
        write_futures = [executor.submit(send_write_request, url, i) for i in range(NUM_REQUESTS)]
        write_results = [future.result() for future in concurrent.futures.as_completed(write_futures)]
    
    write_end_time = time.time()

    start_read_time = time.time()
    # Send read requests
    with concurrent.futures.ThreadPoolExecutor() as executor:
        read_futures = [executor.submit(send_read_request, url) for _ in range(NUM_REQUESTS)]
        read_results = [future.result() for future in concurrent.futures.as_completed(read_futures)]

    end_read_time = time.time()

    write_duration = write_end_time - write_start_time
    read_duration = end_read_time - start_read_time

    return write_duration, read_duration

# Plotting function
def plot_results(results):
    labels = ['Direct', 'Random', 'Customized']

    write_duration = [result[0] for result in results]
    read_duration = [result[1] for result in results]

    x = range(len(labels))

    fig, ax = plt.subplots()

    # Plot total duration for write and read operations
    ax.bar(x, write_duration, color='g', width=0.4, align='center', label='Total Write Duration')
    ax.bar([p + 0.4 for p in x], read_duration, color='b', width=0.4, align='center', label='Total Read Duration')

    ax.set_xlabel('Query Patterns')
    ax.set_ylabel('Total Duration (seconds)')
    ax.set_xticks([p + 0.2 for p in x])
    ax.set_xticklabels(labels)
    ax.legend(loc='upper left')

    plt.title('Benchmark Results: Total Duration of 100 Write and 100 Read Operations')
    plt.show()

# Configuration
def run_benchmark():

    IP = gp.get_public_ip('Name', 'public-host')

    urls = [
        f"http://{IP}:5001/direct",
        f"http://{IP}:5001/random",
        f"http://{IP}:5001/customized"
    ]

    results = []
    for url in urls:
        print(f"Running benchmark for {url}")
        results.append(benchmark_test(url))
        time.sleep(PAUSE_DURATION)

    plot_results(results)

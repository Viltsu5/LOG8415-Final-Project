import time
import os
from utils import globals as g
import boto3
import stat
from functions import setup_instances as i
from benchmark import run_benchmark as b
import paramiko
from utils import get_public_ip as gp
from utils import remove_permission as rp


'''
Description: Main script to set up AWS EC2 instances, including key pair creation, security group setup, 
             instance creation, and user data configuration.

'''

if __name__ == "__main__":

    key_path = g.key_path

    # Create EC2 Client
    session = boto3.Session()
    ec2 = session.resource('ec2')

    # Read VPC and Subnet IDs from files
    with open(g.vpc_path, 'r') as file:
        vpc_id = file.read().strip()
    with open(g.subnet_path, 'r') as file:
        subnet_id = file.read().strip()
    with open(g.ip_path, 'r') as file:
        ips = [line.strip() for line in file.readlines()]

    
    # Delete keypair with same name if it exists
    ec2.KeyPair(g.key_name).delete()

    # Create a new key pair and save the .pem file
    key_pair = ec2.create_key_pair(KeyName=g.key_name)

    # Change file permissions to 600 to protect the private key
    os.chmod(g.key_path, stat.S_IWUSR) # Change security to be able to read
    # Save the private key to a .pem file
    with open(g.key_path, 'w') as pem_file:
        pem_file.write(key_pair.key_material)
    os.chmod(key_path, stat.S_IRUSR) # Change file permissions to 400 to protect the private key

    # Create security group
    public_security_id = i.createPublicSecurityGroup(vpc_id, g.public_security_group_name)
    private_security_id = i.createPrivateSecurityGroup(vpc_id, g.private_security_group_name, public_security_id)

    # Read userdata scripts
    with open('userdata_scripts/manager_userdata.sh', 'r') as file:
        manager_userdata = file.read()

    with open('userdata_scripts/worker1_userdata.sh', 'r') as file:
        worker1_userdata = file.read()

    with open('userdata_scripts/worker2_userdata.sh', 'r') as file:
        worker2_userdata = file.read()

    with open('userdata_scripts/proxy_userdata.sh', 'r') as file:
        proxy_userdata = file.read()

    with open('userdata_scripts/trusted_host_userdata.sh', 'r') as file:
        trusted_host_userdata = file.read()

    with open('userdata_scripts/public_host_userdata.sh', 'r') as file:
        public_host_userdata = file.read()

    print("Creating instances...\n")

    # 3x t2.micro for 1 manager and 2 worker instances
    i.createInstance('t2.micro', 1, 1, key_pair, private_security_id, subnet_id, ips[0], manager_userdata, "manager")

    print("Wait for manager to be created and configured (2 minutes)...\n")

    time.sleep(120)

    i.createInstance('t2.micro', 1, 1, key_pair, private_security_id, subnet_id, ips[1], worker1_userdata, "worker-1")
    i.createInstance('t2.micro', 1, 1, key_pair, private_security_id, subnet_id, ips[2], worker2_userdata, "worker-2")
    print("Wait for workers to be created and configured (1.5 minutes)...\n")
    time.sleep(90)

    # 1x t2.large for proxy instance
    i.createInstance('t2.large', 1, 1, key_pair, private_security_id, subnet_id, ips[3], proxy_userdata, "proxy")
    print("Wait for proxy to be created and configured (1 minute)...\n")
    # 1x t2.large for trusted host instance
    i.createInstance('t2.large', 1, 1, key_pair, private_security_id, subnet_id, ips[4], trusted_host_userdata, "trusted-host")
    print("Wait for trusted host to be created and configured (1 minute)...\n")
    time.sleep(60)
    # 1x t2.large for public host instance
    i.createInstance('t2.large', 1, 1, key_pair, public_security_id, subnet_id, ips[5], public_host_userdata, "public-host")
    print("Wait for public host to be created and configured (1 minute)...\n")
    time.sleep(120)

    print("Instances created successfully!\n")

    public_host_ip = gp.get_public_ip('Name', 'public-host')
    trusted_host_ip = gp.get_public_ip('Name', 'trusted-host')
    proxy_ip = gp.get_public_ip('Name', 'proxy')

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    print(f"Connecting to {proxy_ip} using SSH...")
    # Connect to the instance
    ssh.connect(proxy_ip, username='ubuntu', key_filename=g.key_path)

    print("Connected! Now running 'python3 on the proxy'...")
    # Run the flask app on the proxy in the background
    ssh.exec_command('sudo nohup python3 proxy.py > proxy.log 2>&1 &')
    ssh.close()

    print(f"Connecting to {trusted_host_ip} using SSH...")
    # Connect to the instance
    ssh.connect(trusted_host_ip, username='ubuntu', key_filename=g.key_path)

    print("Connected! Now running 'python3 on the trusted host'...")
    # Run the flask app on the trusted host in the background
    ssh.exec_command('sudo nohup python3 trusted_host.py > trusted_host.log 2>&1 &')
    ssh.close()

    print(f"Connecting to {public_host_ip} using SSH...")
    # Connect to the instance
    ssh.connect(public_host_ip, username='ubuntu', key_filename=g.key_path)

    print("Connected! Now running 'python3 on the public-host'...")
    # Run the flask app on the public host in the background
    ssh.exec_command('sudo nohup python3 gatekeeper.py > gatekeeper.log 2>&1 &')
    ssh.close()

    print("Instances are now running the Flask apps!\n")

    response = rp.remove_permission(private_security_id, 'tcp', 22, 22, '0.0.0.0/0')

    print("Security group permissions updated.\n")

    print("Running the benchmark")
    # Run benchmark
    b()

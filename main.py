import time
import os
from utils import globals as g
import boto3
import stat
from functions import setup_instances as i


'''
Description: Main script to set up AWS EC2 instances, including key pair creation, security group setup, 
             instance creation, and application deployment.
Inputs: 
    - None.
Outputs: 
    - EC2 instances, security groups, key pair, and the successful deployment of the .
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

    # Delete keypair with same name, USED IN TESTING
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
    security_id = i.createSecurityGroup(vpc_id, g.security_group_name)

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

    print("Creating instances...\n")

    # 3x t2.micro for 1 manager and 2 worker instances
    i.createInstance('t2.micro', 1, 1, key_pair, security_id, subnet_id, ips[0], manager_userdata, "manager")

    print("Wait for manager to be created and configured (2 minutes)...\n")

    time.sleep(120)

    i.createInstance('t2.micro', 1, 1, key_pair, security_id, subnet_id, ips[1], worker1_userdata, "worker-1")
    i.createInstance('t2.micro', 1, 1, key_pair, security_id, subnet_id, ips[2], worker2_userdata, "worker-2")
    print("Wait for workers to be created and configured (1.5 minutes)...\n")
    time.sleep(90)

    # 1x t2.large for proxy instance
    i.createInstance('t2.large', 1, 1, key_pair, security_id, subnet_id, ips[3], proxy_userdata, "proxy")
    print("Wait for proxy to be created and configured (1 minute)...\n")
    time.sleep(60)

    i.createInstance('t2.large', 1, 1, key_pair, security_id, subnet_id, ips[4], trusted_host_userdata, "trusted-host")
    print("Wait for trusted host to be created and configured (1 minute)...\n")
    time.sleep(60)
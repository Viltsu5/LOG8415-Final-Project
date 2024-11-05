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

    with open('userdata_scripts/manager_userdata.sh', 'r') as file:
        manager_userdata = file.read()

    with open('userdata_scripts/worker_userdata.sh', 'r') as file:
        worker_userdata = file.read()

    print("Creating instances...")
    # 3x t2.micro for 1 manager and 2 worker instances
    i.createInstance('t2.micro', 1, 1, key_pair, security_id, subnet_id, ips[0], manager_userdata, "manager-instance")
    #i.createInstance('t2.micro', 1, 1, key_pair, security_id, subnet_id, ips[1], worker_userdata, "worker-instance")
    #time.sleep(240)
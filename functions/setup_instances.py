import boto3

'''
Description: Creates a security group in the specified VPC that allows HTTP traffic on port 80 and SSH on port 22.
Inputs: 
    vpc_id (str) - The ID of the VPC where the security group will be created.
    group_name (str) - The name to assign to the new security group.
Outputs: 
    security_group_id (str) - The ID of the created security group.
'''
# Function that creates a security group in the specified VPC.
# Returns the security group ID
import boto3

def createPublicSecurityGroup(vpc_id: str, group_name: str):
    # Create EC2 Client
    session = boto3.Session()
    ec2 = session.resource('ec2')

    # Create the security group
    response = ec2.create_security_group(GroupName=group_name,
                                         Description='Public security group',
                                         VpcId=vpc_id)
    security_group_id = response.group_id
    print(f'Security Group Created {security_group_id} in vpc {vpc_id}.')

    # Add ingress rules to allow inbound traffic on ports 5001 and 22 (SSH)
    ec2.SecurityGroup(security_group_id).authorize_ingress(
        GroupId=security_group_id,
        IpPermissions=[
            # Allow traffic on port 5001 from anywhere (for external access)
        {
            'IpProtocol': 'tcp',
            'FromPort': 5001,
            'ToPort': 5001,
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
        },
            # Allow traffic on port 22 from anywhere (for SSH access)
        {
            'IpProtocol': 'tcp',
            'FromPort': 22,
            'ToPort': 22,
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
        }

    
        ]
    )

    return security_group_id


def createPrivateSecurityGroup(vpc_id: str, group_name: str, public_security_group_id: str):
    # Create EC2 Client
    session = boto3.Session()
    ec2 = session.resource('ec2')

    # Create the security group
    response = ec2.create_security_group(GroupName=group_name,
                                         Description='Private security group',
                                         VpcId=vpc_id)
    security_group_id = response.group_id
    print(f'Security Group Created {security_group_id} in vpc {vpc_id}.')

    # Add ingress rules to allow inbound traffic on ports 5000
    ec2.SecurityGroup(security_group_id).authorize_ingress(
        GroupId=security_group_id,
        IpPermissions=[
        {
            'IpProtocol': 'tcp',
            'FromPort': 5000,
            'ToPort': 5000,
            'UserIdGroupPairs': [
                {'GroupId': public_security_group_id}, 
                {'GroupId': security_group_id}]
        },
                    
        # Allow traffic on port 5001 from the public security group and the private security group itself

        {
            'IpProtocol': 'tcp',
            'FromPort': 5001,
            'ToPort': 5001,
            'UserIdGroupPairs': [
                {'GroupId': public_security_group_id}, 
                {'GroupId': security_group_id}
            ]
        },

        # Allow traffic to db cluster on port 3306
        {
            'IpProtocol': 'tcp',
            'FromPort': 3306,
            'ToPort': 3306,
            'UserIdGroupPairs': [{'GroupId': security_group_id}]
        }
    
        ]
    )

    return security_group_id

'''
Description: Creates an EC2 instance with the specified parameters and waits for it to enter the running state.
Inputs: 
    instanceType (str) - The type of instance to create (e.g., 't2.micro').
    minCount (int) - The minimum number of instances to launch.
    maxCount (int) - The maximum number of instances to launch.
    key_pair (boto3.KeyPair) - The key pair used for SSH access.
    security_id (str) - The security group ID associated with the instance.
    subnet_id (str) - The subnet ID where the instance will be launched.
    user_data (str) - The user data script to configure the instance at launch.
    instance_name (str) - The name to assign to the created instance.
Outputs: 
    instances (list) - A list of created instance objects.
'''
def createInstance(instanceType: str, minCount: int, maxCount: int, key_pair, security_id: str, subnet_id: str, ip: str,  user_data: str, instance_name: str):
    
    # Create EC2 Client
    session = boto3.Session()
    ec2 = session.resource('ec2')

    instances = ec2.create_instances(
        ImageId='ami-0e86e20dae9224db8',
        InstanceType=instanceType,
        MinCount=minCount,
        MaxCount=maxCount,
        KeyName=key_pair.name,
        SecurityGroupIds=[security_id],
        SubnetId=subnet_id,
        UserData=user_data,
        PrivateIpAddress=ip
    )

    # Wait until the instances are running
    for instance in instances:
        print(f"Waiting for instance {instance.id} to enter running state...")
        instance.wait_until_running()
        print(f"Instance {instance.id} is now running.")
        
        # Add tags to the instance
        instance.create_tags(Tags=[{'Key': 'Name', 'Value': instance_name}])
    
    return instances
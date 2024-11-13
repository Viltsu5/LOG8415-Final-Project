import boto3

def get_public_ip(tag_key, tag_value):
    ec2 = boto3.client('ec2')
    
    # Describe instances with the wanted tag
    response = ec2.describe_instances(
        Filters=[
            {
                'Name': f'tag:{tag_key}',
                'Values': [tag_value]
            }
        ]
    )
    
    # Iterate through the instances and find the public IP
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            if 'PublicIpAddress' in instance:
                return instance['PublicIpAddress']
    
    return None
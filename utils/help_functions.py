def remove_permission(security_group_id, ip_protocol, from_port, to_port, cidr_ip):
    import boto3
    ec2 = boto3.client('ec2')

    response = ec2.revoke_security_group_ingress(
        GroupId=security_group_id,
        IpPermissions=[
            {
                'IpProtocol': ip_protocol,
                'FromPort': from_port,
                'ToPort': to_port,
                'IpRanges': [{'CidrIp': cidr_ip}]
            }
        ]
    )
    return response


def write_proxy_log_to_file():
    import requests
    from requests.auth import HTTPBasicAuth
    from utils import get_public_ip as gp
    from utils import globals as g
    with open(g.authentication_path, 'r') as file:
        data = file.read().splitlines()
        USERNAME = data[0]
        PASSWORD = data[1]

    # get the url of the public host:
    proxy_ip = gp.get_public_ip('Name', 'public-host')

    logs_url = f'http://{proxy_ip}:5001/logs'

    # Send a GET request to the logs route
    response = requests.get(logs_url, auth=HTTPBasicAuth(USERNAME, PASSWORD))

    # Check if the request was successful
    if response.status_code == 200:
        # Save the response content to a text file
        with open('benchmark_log.txt', 'w') as file:
            file.write(response.text)
        print("Log file saved as 'benchmark_log.txt'")
    else:
        print(f"Failed to get logs. Status code: {response.status_code}")
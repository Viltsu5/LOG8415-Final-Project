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
#!/bin/bash

# Install MySQL Server
sudo apt-get update
sudo apt-get install -y mysql-server

# Configure MySQL for replication
sudo bash -c 'cat <<EOF >> /etc/mysql/my.cnf
[mysqld]
server-id=2  # Change to 3 for the second worker
relay-log=relay-log
EOF'

# Restart MySQL service
sudo systemctl restart mysql

# Set up the slave
MASTER_HOST='manager_ec2_ip'  # Replace with the actual IP of the manager EC2 instance
MASTER_USER='replica_user'
MASTER_PASSWORD='password'
MASTER_LOG_FILE='mysql-bin.000001'  # Replace with the actual log file from the master status
MASTER_LOG_POS=123  # Replace with the actual log position from the master status

mysql -u root -e "CHANGE MASTER TO MASTER_HOST='$MASTER_HOST', MASTER_USER='$MASTER_USER', MASTER_PASSWORD='$MASTER_PASSWORD', MASTER_LOG_FILE='$MASTER_LOG_FILE', MASTER_LOG_POS=$MASTER_LOG_POS;"
mysql -u root -e "START SLAVE;"

# Verify slave status
mysql -u root -e "SHOW SLAVE STATUS\G"
#!/bin/bash

exec > /home/ubuntu/userdata.log 2>&1

# Install MySQL Server
apt-get update -y
apt-get install -y mysql-server

# Configure MySQL for replication
bash -c 'cat <<EOF >> /etc/mysql/my.cnf
[mysqld]
server-id=3
relay-log=relay-log
gtid_mode=ON                   
enforce_gtid_consistency=ON    
log-replica-updates=ON
super_read_only=ON
EOF'

# Restart MySQL service
systemctl restart mysql
systemctl enable mysql

PASSWORD="hattu"

# Create user and define password
mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '$PASSWORD';"
mysql -u root -p"$PASSWORD" -e "FLUSH PRIVILEGES;"

# Install sakila db
wget https://downloads.mysql.com/docs/sakila-db.tar.gz
tar -xvzf sakila-db.tar.gz
mysql -u root -p"$PASSWORD" < sakila-db/sakila-schema.sql
mysql -u root -p"$PASSWORD" < sakila-db/sakila-data.sql


# Set up the slave
MASTER_HOST='172.31.32.100'      # Private IP of the manager instance
MASTER_USER='replica_user'       # Replication username
MASTER_PASSWORD='takki'          # Replication password

mysql -u root -p"$PASSWORD" -e "CHANGE MASTER TO MASTER_HOST='$MASTER_HOST', MASTER_USER='$MASTER_USER', MASTER_PASSWORD='$MASTER_PASSWORD', MASTER_AUTO_POSITION=1;"
mysql -u root -p"$PASSWORD" -e "START SLAVE;"

# Verify slave status
mysql -u root -e "SHOW SLAVE STATUS\G"
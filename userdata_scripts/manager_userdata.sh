#!/bin/bash

# Write logs to file when running userdata script
exec > /home/ubuntu/userdata.log 2>&1

# Install MySQL Server
apt-get update -y
apt-get install -y mysql-server

# Configure MySQL for replication
bash -c 'cat <<EOF >> /etc/mysql/my.cnf
[mysqld]
server-id=1
bind-address = 0.0.0.0
gtid_mode=ON                   
enforce_gtid_consistency=ON    
log-bin=mysql-bin
read-only = 0
EOF'

# Restart MySQL service
systemctl restart mysql
systemctl enable mysql

# Variables
PASSWORD="hattu"
REPLICATION_USER="replica_user"
REPLICATION_PASSWORD="takki"
PROXY_USER="proxy_user"
PROXY_PASSWORD="paita"

# Create user and define password
mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH 'mysql_native_password' BY '$PASSWORD';"
mysql -u root -p"$PASSWORD" -e "FLUSH PRIVILEGES;"

# Create proxy user
mysql -u root -p"$PASSWORD" -e "CREATE USER '$PROXY_USER'@'%' IDENTIFIED WITH 'mysql_native_password' BY '$PROXY_PASSWORD';"
mysql -u root -p"$PASSWORD" -e "GRANT ALL PRIVILEGES ON *.* TO '$PROXY_USER'@'%' WITH GRANT OPTION;"
mysql -u root -p"$PASSWORD" -e "FLUSH PRIVILEGES;"

# Create replication user
mysql -u root -p"$PASSWORD" -e "CREATE USER '$REPLICATION_USER'@'%' IDENTIFIED WITH 'mysql_native_password' BY '$REPLICATION_PASSWORD';"
mysql -u root -p"$PASSWORD" -e "GRANT REPLICATION SLAVE ON *.* TO '$REPLICATION_USER'@'%';"
mysql -u root -p"$PASSWORD" -e "FLUSH PRIVILEGES;"

# Install sakila db
wget https://downloads.mysql.com/docs/sakila-db.tar.gz
tar -xvzf sakila-db.tar.gz
mysql -u root -p"$PASSWORD" < sakila-db/sakila-schema.sql
mysql -u root -p"$PASSWORD" < sakila-db/sakila-data.sql

# Verify Sakila installation
mysql -u root -p"$PASSWORD" -e "SHOW DATABASES;"
mysql -u root -p"$PASSWORD" -e "USE sakila; SHOW TABLES;"

# Install Sysbench for benchmarking
apt-get install sysbench -y
 
#Benchmarking
sysbench oltp_read_write --table-size=40000 --mysql-user=root --mysql-password=$PASSWORD --mysql-db=sakila --db-driver=mysql prepare
sysbench oltp_read_write --table-size=40000 --mysql-user=root --mysql-password=$PASSWORD --mysql-db=sakila --db-driver=mysql --max-requests=0 --max-time=60 --num-threads=6 run > /home/ubuntu/benchmark_results.txt
sysbench oltp_read_write --table-size=40000 --mysql-user=root --mysql-password=$PASSWORD --mysql-db=sakila --db-driver=mysql cleanup

# Get master status
MASTER_STATUS=$(sudo mysql -u root -p"$PASSWORD" -e "SHOW MASTER STATUS\G")

echo "$MASTER_STATUS"

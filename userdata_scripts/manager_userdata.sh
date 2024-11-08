#!/bin/bash

# Write logs to file when running userdata script
exec > /home/ubuntu/userdata.log 2>&1

# Install MySQL Server
apt-get update -y
apt-get install -y mysql-server

# Restart MySQL service
systemctl restart mysql
systemctl enable mysql

# Configure MySQL for replication
sudo bash -c 'cat <<EOF >> /etc/mysql/my.cnf
[mysqld]
server-id=1
log-bin=mysql-bin
binlog-do-db=shakila
EOF'

# Create user and define password
mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'password';"
mysql -u root -p"password" -e "FLUSH PRIVILEGES;"

# Create replication user
mysql -u root -p"password" -e "CREATE USER 'replica_user'@'%' IDENTIFIED BY 'password';"
mysql -u root -p"password" -e "GRANT REPLICATION SLAVE ON *.* TO 'replica_user'@'%';"
mysql -u root -p"password" -e "FLUSH PRIVILEGES;"

# Install sakila db
wget https://downloads.mysql.com/docs/sakila-db.tar.gz
tar -xvzf sakila-db.tar.gz
mysql -u root -p"password" < sakila-db/sakila-schema.sql
mysql -u root -p"password" < sakila-db/sakila-data.sql

# Verify Sakila installation
mysql -u root -p"password" -e "SHOW DATABASES;"
mysql -u root -p"password" -e "USE sakila; SHOW TABLES;"

# Install Sysbench for benchmarking
apt-get install sysbench -y
 

#Benchmarking
sysbench oltp_read_write --table-size=40000 --mysql-user=root --mysql-password=password --mysql-db=sakila --db-driver=mysql prepare
sysbench oltp_read_write --table-size=40000 --mysql-user=root --mysql-password=password --mysql-db=sakila --db-driver=mysql --max-requests=0 --max-time=60 --num-threads=6 run > /home/ubuntu/benchmark_results.txt
sysbench oltp_read_write --table-size=40000 --mysql-user=root --mysql-password=password --mysql-db=sakila --db-driver=mysql cleanup

# Get master status
MASTER_STATUS=$(sudo mysql -u root -p"password" -e "SHOW MASTER STATUS\G")
echo "$MASTER_STATUS"

#!/bin/bash

# Update and upgrade system
apt-get update -y
apt-get upgrade -y

# Install MySQL Server
apt-get install mysql-server -y

# Download and install the Sakila database
wget https://downloads.mysql.com/docs/sakila-db.tar.gz -O /home/ubuntu/sakila-db.tar.gz
tar -xvf /home/ubuntu/sakila-db.tar.gz -C /home/ubuntu/

# Install Sakila schema and data into MySQL
mysql -u root -e "SOURCE /home/ubuntu/sakila-db/sakila-schema.sql;"
mysql -u root -e "SOURCE /home/ubuntu/sakila-db/sakila-data.sql;"

# Verify Sakila installation
mysql -u root -e "SHOW DATABASES;"
mysql -u root -e "USE sakila; SHOW TABLES;"

# Install Sysbench for benchmarking
apt-get install sysbench -y
 
# Prepare for benchmarking
sysbench oltp_read_write --table-size=40000 --mysql-user=root --mysql-db=sakila --db-driver=mysql prepare
sysbench oltp_read_write --table-size=40000 --mysql-user=root --mysql-db=sakila --db-driver=mysql --max-requests=0 --max-time=60 --num-threads=6 run > /home/ubuntu/benchmark_results.txt
sysbench oltp_read_write --table-size=40000 --mysql-user=root --mysql-db=sakila --db-driver=mysql cleanup

#!/bin/bash

apt-get update -y
apt-get upgrade -y
#apt-get install libncurses5 libaio-dev libmecab2 sysbench -y

wget  https://dev.mysql.com/get/Downloads/MySQL-Cluster-8.4/mysql-cluster-community-management-server_8.4.3-1ubuntu24.04_amd64.deb
dpkg -i mysql-cluster-community-management-server_8.4.3-1ubuntu24.04_amd64.deb
mkdir /var/lib/mysql-cluster

cat <<EOF | sudo tee /var/lib/mysql-cluster/config.ini
[ndbd default]
NoOfReplicas=2

[ndb_mgmd]
hostname=ip-172-31-32-100.ec2.internal # Hostname of the manager
datadir=/var/lib/mysql-cluster 	# Directory for the log files

[ndbd]
hostname=ip-172-31-32-101.ec2.internal # Hostname of the first worker
NodeId=2			# Node ID for this worker
datadir=/usr/local/mysql/data	# Remote directory for the data files

[ndbd]
hostname=ip-172-31-32-102.ec2.internal # Hostname of the second worker
NodeId=3			# Node ID for this worker
datadir=/usr/local/mysql/data	# Remote directory for the data files

[mysqld]
# SQL node options:
hostname=ip-172-31-32-100.ec2.internal
EOF

# Create systemd service file for MySQL NDB
cat <<EOF | sudo tee /etc/systemd/system/ndb_mgmd.service
[Unit]
Description=MySQL NDB Cluster Management Server
After=network.target auditd.service

[Service]
Type=forking
ExecStart=/usr/sbin/ndb_mgmd -f /var/lib/mysql-cluster/config.ini
ExecReload=/bin/kill -HUP \$MAINPID
KillMode=process
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ndb_mgmd
systemctl start ndb_mgmd

wget https://dev.mysql.com/get/Downloads/MySQL-Cluster-8.4/mysql-cluster_8.4.3-1ubuntu24.04_amd64.deb-bundle.tar
mkdir install
tar -xvf mysql-cluster_8.4.3-1ubuntu24.04_amd64.deb-bundle.tar -C install/
cd install

apt-get update -y
apt install libaio-dev libmecab2

dpkg -i mysql-common_8.4.3-1ubuntu24.04_amd64.deb
dpkg -i mysql-cluster-community-client_8.4.3-1ubuntu24.04_amd64.deb
dpkg -i mysql-client_8.4.3-1ubuntu24.04_amd64.deb

apt-get install -f

dpkg -i mysql-client_8.4.3-1ubuntu24.04_amd64.deb

debconf-set-selections <<< 'mysql-cluster-community-server_8.4.3 mysql-cluster-community-server/root-pass password root'
debconf-set-selections <<< 'mysql-cluster-community-server_8.4.3 mysql-cluster-community-server/re-root-pass password root'

#Deal with the password prompts
dpkg -i mysql-cluster-community-server_8.4.3-1ubuntu24.04_amd64.deb
dpkg -i mysql-server_8.4.3-1ubuntu24.04_amd64.deb

# Connect the client to the cluster
cat <<EOF | sudo tee /etc/mysql/my.cnf
[mysqld]
ndbcluster                   

[mysql_cluster]
ndb-connectstring=ip-172-31-32-100.ec2.internal
EOF

systemctl restart mysql
systemctl enable mysql

# Download and install the Sakila database
wget https://downloads.mysql.com/docs/sakila-db.tar.gz -O /home/ubuntu/sakila-db.tar.gz
tar -xvf /home/ubuntu/sakila-db.tar.gz -C /home/ubuntu/

# Install Sakila schema and data into MySQL
mysql -u root -e "SOURCE /home/ubuntu/sakila-db/sakila-schema.sql;"
mysql -u root -e "SOURCE /home/ubuntu/sakila-db/sakila-data.sql;"

# Print out the databases and tables
mysql -u root -e "SHOW DATABASES;"
mysql -u root -e "USE sakila; SHOW TABLES;"

# Install Sysbench for benchmarking
sudo apt-get install sysbench -y

# Benchmark and save results to benchmark_results.txt
sysbench oltp_read_write --table-size=40000 --mysql-user=root --mysql-db=sakila --db-driver=mysql prepare
sysbench oltp_read_write --table-size=40000 --mysql-user=root --mysql-db=sakila --db-driver=mysql --max-requests=0 --max-time=60 --num-threads=6 run > /home/ubuntu/benchmark_results.txt
sysbench oltp_read_write --table-size=40000 --mysql-user=root --mysql-db=sakila --db-driver=mysql cleanup
# LOG8415-Final-Project

# Commands used for testing during ssh connection

ssh -i C:/Users/vilja/.aws/key.pem ubuntu@

ImageId='ami-0e86e20dae9224db8',

sudo systemctl status mysql

mysql -u root -p"hattu" -e "SHOW MASTER STATUS\G"

mysql -u root -p"hattu" -e "SHOW SLAVE STATUS\G"

mysql -h 172.31.32.100 -u replica_user -p"takki"

curl -u admin:password -X POST http://<public-host-ip>:5001/direct \
-H "Content-Type: application/json" \
-d '{"query": "SELECT * FROM actor LIMIT 10;"}'
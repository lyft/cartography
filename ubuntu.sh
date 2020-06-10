#!/bin/bash

wget -O - https://debian.neo4j.org/neotechnology.gpg.key | apt-key add -
echo 'deb http://debian.neo4j.org/repo stable/' > /etc/apt/sources.list.d/neo4j.list
apt-get update
apt-get install neo4j
apt install awscli
apt install python3-pip
pip3 install cartography
# For local testing, you might want to turn off authentication via property `dbms.security.auth_enabled` in file /NEO4J_PATH/conf/neo4j.conf
service neo4j start
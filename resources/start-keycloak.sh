#!/bin/bash
docker run -d --name keycloak --network host jboss/keycloak:12.0.2 -Djboss.bind.address.private=127.0.0.1 -Djboss.bind.address=127.0.0.1
sleep 60
docker exec keycloak /opt/jboss/keycloak/bin/add-user-keycloak.sh -u admin -p admin
docker restart keycloak
sleep 60

echo "Keycloak Ready"

( trap exit SIGINT ; read -r -d '' _ </dev/tty ) ## wait for Ctrl-C

echo "Stopping Keycloak"
docker stop keycloak
docker rm keycloak

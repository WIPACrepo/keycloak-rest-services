#!/bin/bash
docker run -d --name keycloak --network host \
 -v $PWD/resources/keycloak-to-rabbit-1.0.jar:/opt/jboss/keycloak/standalone/deployments/keycloak-to-rabbit-1.0.jar \
 -v $PWD/keycloak_theme:/opt/jboss/keycloak/themes/custom \
 --env KK_TO_RMQ_USERNAME=admin --env KK_TO_RMQ_PASSWORD=admin \
 --env KK_TO_RMQ_VHOST=keycloak \
 jboss/keycloak:15.0.1 -Djboss.bind.address.private=127.0.0.1 -Djboss.bind.address=127.0.0.1
sleep 60
docker exec keycloak /opt/jboss/keycloak/bin/add-user-keycloak.sh -u admin -p admin
docker restart keycloak

until curl http://localhost:8080 >/dev/null 2>/dev/null
do
    sleep 5
done

echo "Keycloak Ready"

( trap exit SIGINT ; read -r -d '' _ </dev/tty ) ## wait for Ctrl-C

echo "Stopping Keycloak"
docker stop keycloak
docker rm keycloak

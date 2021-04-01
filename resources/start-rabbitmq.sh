#!/bin/bash
docker run -d --name rabbitmq -h rabbitmq -p 5672:5672 -p 15672:15672 \
 --env RABBITMQ_DEFAULT_USER=admin --env RABBITMQ_DEFAULT_PASS=admin \
 --env RABBITMQ_DEFAULT_VHOST=keycloak \
 rabbitmq:3-management
sleep 5

# add read-only user for keycloak events
curl -u admin:admin -XPUT -d '{"password":"guest","tags":""}' http://localhost:15672/api/users/guest
curl -u admin:admin -XPUT -d '{"configure":".*","write":".*","read":".*"}' http://localhost:15672/api/permissions/keycloak/guest
curl -u admin:admin -XPUT -d '{"exchange":"amq.topic","write":"","read":".*"}' http://localhost:15672/api/topic-permissions/keycloak/guest

echo "server at: localhost:5672"
echo "mgmt server at: localhost:15672"
echo "RabbitMQ Ready"

( trap exit SIGINT ; read -r -d '' _ </dev/tty ) ## wait for Ctrl-C

echo "Stopping RabbitMQ"
docker stop rabbitmq
docker rm rabbitmq

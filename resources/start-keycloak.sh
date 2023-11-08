#!/bin/bash
docker build -t krs-test-keycloak -f ./resources/keycloak-image/Dockerfile .

docker run -d --name keycloak --network host \
  --env KEYCLOAK_ADMIN=admin --env KEYCLOAK_ADMIN_PASSWORD=admin \
  krs-test-keycloak start-dev

until curl http://localhost:8080 >/dev/null 2>/dev/null
do
    sleep 1
done

echo "Keycloak Ready"

( trap exit SIGINT ; read -r -d '' _ </dev/tty ) ## wait for Ctrl-C

echo "Stopping Keycloak"
docker stop keycloak
docker rm keycloak

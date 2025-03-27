#!/bin/bash
set -e

podman build -t krs-test-keycloak -f ./resources/keycloak-image/Dockerfile .

podman run --rm -it --name keycloak --network host \
  --env KC_BOOTSTRAP_ADMIN_USERNAME=admin --env KC_BOOTSTRAP_ADMIN_PASSWORD=admin \
  -v $PWD/resources/test-master-realm.json:/opt/keycloak/data/import/master-realm.json \
  krs-test-keycloak start-dev  --import-realm

until curl http://localhost:8080 >/dev/null 2>/dev/null
do
    sleep 1
done

echo "Keycloak Ready"

( trap exit SIGINT ; read -r -d '' _ </dev/tty ) ## wait for Ctrl-C

echo "Stopping Keycloak"
podman stop keycloak
podman rm keycloak

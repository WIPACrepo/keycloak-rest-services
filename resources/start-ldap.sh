#!/bin/bash
set -e

podman build -t krs-test-ldap -f ./resources/ldap-image/Dockerfile .

podman run -d --name ldap -p 1389:389 krs-test-ldap
sleep 5
echo "server at: localhost:1389"
echo "admin login: cn=admin,dc=icecube,dc=wisc,dc=edu"
echo "LDAP Ready"

( trap exit SIGINT ; read -r -d '' _ </dev/tty ) ## wait for Ctrl-C

echo "Stopping LDAP"
podman stop ldap
podman rm ldap

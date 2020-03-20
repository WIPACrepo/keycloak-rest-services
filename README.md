# keycloak-rest-services
Services surrounding KeyCloak, that use the REST API to read/update state

## Bootstrap KeyCloak

First, get a KeyCloak instance running.  For testing, the Docker container works:

    docker run --rm -it -e KEYCLOAK_USER=admin -e KEYCLOAK_PASSWORD=admin --network host jboss/keycloak:8.0.2 -Djboss.bind.address.private=127.0.0.1 -Djboss.bind.address=127.0.0.1

Then, run the bootstrap script:

    realm=test keycloak_url=http://localhost:8080 username=admin password=admin python3 -m krs.bootstrap
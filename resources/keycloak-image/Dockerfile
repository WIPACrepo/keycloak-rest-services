FROM quay.io/keycloak/keycloak:26.7.2 AS builder

# Keycloak core settings
ENV KC_HTTP_ENABLED="true"
ENV KC_HTTP_RELATIVE_PATH="/auth"
ENV KC_HOSTNAME_STRICT="false"
ENV KC_FEATURES=scripts,parameterized-scopes
ENV KC_LOG=console

# rabbitmq settings
COPY resources/keycloak-to-rabbit-3.0.jar /opt/keycloak/providers/
ENV KK_TO_RMQ_USERNAME=admin
ENV KK_TO_RMQ_PASSWORD=admin
ENV KK_TO_RMQ_VHOST=keycloak

# theme
COPY keycloak_theme /opt/keycloak/themes/i3_theme

# script jars
COPY custom-jars/*.jar /opt/keycloak/providers/

# testing TLS cert
RUN keytool -genkeypair -storepass password -storetype PKCS12 -keyalg RSA -keysize 2048 -dname "CN=server" -alias server -ext "SAN:c=DNS:localhost,IP:127.0.0.1" -keystore /opt/keycloak/conf/truststores/server.keystore

RUN /opt/keycloak/bin/kc.sh build

# GitHub Actions service containers can't be given a docker command/args, so
# let the desired kc.sh subcommand (e.g. "start-dev") be chosen at runtime via
# the CMD env var when no command is given at all. This wraps kc.sh rather
# than patching its internals, since kc.sh's own launch line has changed
# across Keycloak versions and silently broke a previous sed-based patch,
# leaving the entrypoint running with no subcommand at all (it just printed
# --help and exited). When a command IS given (e.g. `podman run image
# start-dev`, as resources/start-keycloak.sh does), use that instead of
# also appending CMD, or kc.sh sees "start-dev start-dev" and fails.
RUN printf '#!/bin/sh\nset -e\nif [ "$#" -gt 0 ]; then\n  exec /opt/keycloak/bin/kc.sh "$@"\nelse\n  exec /opt/keycloak/bin/kc.sh "${CMD:-start-dev}"\nfi\n' > /opt/keycloak/bin/docker-entrypoint.sh \
    && chmod +x /opt/keycloak/bin/docker-entrypoint.sh
ENTRYPOINT ["/opt/keycloak/bin/docker-entrypoint.sh"]

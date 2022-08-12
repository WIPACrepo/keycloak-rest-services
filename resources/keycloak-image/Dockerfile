FROM quay.io/keycloak/keycloak:latest as builder

ENV KC_HTTP_ENABLED="true"

RUN sed -i '/^eval exec/ s/$/ \$CMD/' /opt/keycloak/bin/kc.sh

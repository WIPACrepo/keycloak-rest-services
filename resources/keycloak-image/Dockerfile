FROM quay.io/keycloak/keycloak:latest as builder

ENV KC_HTTP_ENABLED="true"
ENV KC_HTTP_RELATIVE_PATH="/auth"

RUN /opt/keycloak/bin/kc.sh build

RUN sed -i '/^eval exec/ s/$/ \$CMD/' /opt/keycloak/bin/kc.sh

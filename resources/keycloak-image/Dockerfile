FROM quay.io/keycloak/keycloak:26.2.0 AS builder

# Keycloak core settings
ENV KC_HTTP_ENABLED="true"
ENV KC_HTTP_RELATIVE_PATH="/auth"
ENV KC_HOSTNAME_STRICT="false"
ENV KC_FEATURES=scripts,dynamic-scopes
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

RUN sed -i '/^eval exec/ s/$/ \$CMD/' /opt/keycloak/bin/kc.sh

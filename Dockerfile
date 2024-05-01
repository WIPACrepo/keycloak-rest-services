FROM python:3.11

RUN useradd -m -U keycloak

WORKDIR /home/keycloak
COPY . .
RUN pip install -e .[actions]

USER keycloak

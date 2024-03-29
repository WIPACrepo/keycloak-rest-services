FROM python:3.10

RUN useradd -m -U keycloak

WORKDIR /home/keycloak
COPY . .
RUN pip install -e .[actions]

USER keycloak

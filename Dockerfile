FROM python:3.8

RUN useradd -m -U keycloak

COPY requirements.txt requirements-actions.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-actions.txt

WORKDIR /home/keycloak
USER keycloak

COPY . .

ENV PYTHONPATH=/home/keycloak

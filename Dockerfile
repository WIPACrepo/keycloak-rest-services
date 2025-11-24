FROM python:3.13

RUN groupadd -g 1000 app && useradd -m -g 1000 -u 1000 app

RUN mkdir /app
WORKDIR /app

COPY actions /app/actions
COPY custom-jars /app/custom-jars
COPY keycloak_setup /app/keycloak_setup
COPY keycloak_theme /app/keycloak_theme
COPY krs /app/krs
COPY pyproject.toml /app/pyproject.toml
COPY resources /app/resources

RUN chown -R app:app /app

USER app

ENV VIRTUAL_ENV=/app/venv

RUN python3 -m venv $VIRTUAL_ENV

ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN --mount=type=bind,source=.git,target=.git,ro pip install --no-cache .[actions]

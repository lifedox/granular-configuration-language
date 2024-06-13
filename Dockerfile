ARG PYTHON_VERSION

FROM python:${PYTHON_VERSION}

USER root

RUN groupadd -g 1000 -r granular \
    && useradd -g 1000 -u 1000 --no-log-init -r -m -g granular granular \
    && mkdir /app \
    && chown granular:granular /app \
    && pip install --no-cache-dir poetry

USER granular

# install Python packages via Poetry
COPY --chown=granular:granular pyproject.toml poetry.lock README.md /app/

WORKDIR /app

RUN poetry install --no-root

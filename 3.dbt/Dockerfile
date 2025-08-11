FROM python:3.11.6-slim-bookworm

# Set working directory
WORKDIR /usr/app/dbt/
SHELL ["/bin/bash", "-c"]

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    git \
    vim \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install pip-tools

# Copy all files including .env
COPY . .

# Install dependencies
RUN pip-compile requirements.in
RUN pip-sync requirements.txt

ENV DBT_PROFILES_DIR=/usr/app/dbt/personal_project
ENV PYTHONUNBUFFERED=1

WORKDIR /usr/app/dbt/personal_project
RUN mkdir -p /root/.dbt
COPY personal_project/profiles.yml /root/.dbt/profiles.yml

# Source .env file (variables will be available for subsequent RUN commands)
RUN set -a && source .env && set +a && \
    dbt debug

ENTRYPOINT ["bash", "-c", "set -a && source .env && set +a && exec \"$@\"", "--"]
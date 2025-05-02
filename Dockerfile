FROM python:3.11

RUN mkdir /app && mkdir /app/docker && mkdir /app/src && mkdir /app/alembic
WORKDIR /app

RUN apt-get update && apt-get -y dist-upgrade
RUN apt install netcat-traditional
RUN pip install --upgrade pip poetry

RUN poetry config virtualenvs.create false --local
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root

COPY alembic.ini /app
COPY alembic /app/alembic
COPY src /app/src
COPY docker /app/docker

RUN chmod a+x docker/*.sh

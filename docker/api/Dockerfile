FROM python:3.12.12-slim-trixie

RUN apt-get update && apt-get install -y \
        git \
        libpq-dev \
        gcc \
        graphviz \
        libgraphviz-dev \
        pkg-config \
    && /usr/local/bin/python -m pip install --upgrade pip \
    && mkdir /usr/src/api
WORKDIR /usr/src/api
COPY requirements.txt /usr/src/api
RUN pip install -r /usr/src/api/requirements.txt

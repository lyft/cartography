FROM ubuntu:bionic

WORKDIR /srv/cartography

ENV PATH=/venv/bin:$PATH
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends python3.8-dev python3-pip python3-setuptools openssl libssl-dev gcc pkg-config libffi-dev libxml2-dev libxmlsec1-dev curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
COPY . /srv/cartography

# Installs pip supported by python3.8
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python3.8 get-pip.py

RUN pip install -e . && \
    pip install -r test-requirements.txt

RUN groupadd cartography && \
    useradd -s /bin/bash -d /home/cartography -m -g cartography cartography

USER cartography

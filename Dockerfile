FROM ubuntu:bionic

WORKDIR /srv/cartography

ENV PATH=/venv/bin:$PATH
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends python3-dev python3-pip python3-setuptools openssl libssl-dev gcc pkg-config libffi-dev libxml2-dev libxmlsec1-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY . /srv/cartography

RUN pip3 install -e . && \
    pip3 install -r test-requirements.txt

RUN groupadd cartography && \
    useradd -s /bin/bash -d /home/cartography -m -g cartography cartography

USER cartography

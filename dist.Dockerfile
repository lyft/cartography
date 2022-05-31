FROM python:3-alpine as builder

RUN apk --no-cache add \
    binutils \
    python3-dev \
    musl-dev \
    gcc \
    libffi-dev \
    openssl-dev \
    make

RUN pip install -U pyinstaller

COPY . /var/cartography
WORKDIR /var/cartography

RUN pip install -e .

RUN pyinstaller \
    --onefile \
    --name cartography \
    --collect-data policyuniverse \
    cartography/__main__.py

# verify that the binary at least runs
RUN dist/cartography -h


FROM alpine:3

# the UID and GID to run cartography as
# (https://github.com/hexops/dockerfile#do-not-use-a-uid-below-10000).
ARG uid=10001
ARG gid=10001

RUN apk --no-cache add ca-certificates

USER ${uid}:${gid}

COPY --from=builder /var/cartography/dist/cartography /bin/cartography

# verify that the binary at least runs
RUN cartography -h

ENTRYPOINT ["cartography"]
CMD ["-h"]

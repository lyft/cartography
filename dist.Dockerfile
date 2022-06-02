FROM python:3 as builder

RUN pip install -U pyinstaller

COPY . /var/cartography
WORKDIR /var/cartography

RUN pip install -e .

# Create a self-contained binary using pyinstaller.
RUN pyinstaller \
    --onefile \
    --name cartography \
    # include static data files from policyuniverse (policyuniverse/data.json)
    --collect-data policyuniverse \
    cartography/__main__.py

# verify that the binary at least runs
RUN dist/cartography -h


FROM python:3-slim

# the UID and GID to run cartography as
# (https://github.com/hexops/dockerfile#do-not-use-a-uid-below-10000).
ARG uid=10001
ARG gid=10001

USER ${uid}:${gid}

# Copy the built self-contained cartography binary
COPY --from=builder /var/cartography/dist/cartography /bin/cartography

# verify that the binary at least runs
RUN cartography -h

ENTRYPOINT ["cartography"]
CMD ["-h"]

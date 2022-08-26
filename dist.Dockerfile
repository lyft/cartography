FROM python:3.9-slim

# the UID and GID to run cartography as
# (https://github.com/hexops/dockerfile#do-not-use-a-uid-below-10000).
ARG uid=10001
ARG gid=10001

COPY . /var/cartography
WORKDIR /var/cartography

RUN apt-get update --fix-missing
RUN apt --allow-unauthenticated  update -y
RUN apt-get install vim telnet curl gcc -y

RUN pip install -U -e .

USER ${uid}:${gid}

# verify that the binary at least runs
RUN cartography -h

ENTRYPOINT ["cartography"]
#CMD ["-v", "--neo4j-uri=${NEO4J_URI}", "--aws-sync-all-profiles"]

CMD ["-v", "--neo4j-uri=bolt://neo4j:7687", "--aws-sync-all-profiles"]

FROM python:3.7-alpine3.8

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

ENV AWS_CONFIG_FILE=/root/.aws/config
ENV NEO4J_HOST=neo4j

ADD https://raw.githubusercontent.com/eficode/wait-for/master/wait-for .

CMD sh wait-for ${NEO4J_HOST}:7474 -- cartography --neo4j-uri bolt://${NEO4J_HOST}:7687 --aws-sync-all-profiles

FROM python:3.8

ARG SERVICE_APP_ENV=development
ENV SERVICE_APP_ENV=${SERVICE_APP_ENV}

ENV PYTHONUNBUFFERED 1

ADD config /root/.aws/

WORKDIR /sync

ADD app.py /sync

ADD requirements.txt /sync

COPY settings/ /sync/settings/

COPY cartography/ /sync/cartography/

RUN pip3 install -r requirements.txt

EXPOSE 7000

CMD [ "python3", "./app.py" ]
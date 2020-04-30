FROM python:3.7-alpine

ENV HOME /home
RUN mkdir ~/.aws && mkdir ~/app

## CONFIGURE AWS
#COPY config /home/.aws/

## CONFIGURE APP
WORKDIR /home/app

COPY setup.py .
RUN pip install -e .

COPY . ./

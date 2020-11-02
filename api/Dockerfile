FROM python:3.8-alpine

ENV SECRET_KEY=DEFAULT

WORKDIR /opt/app

COPY requirements.txt requirements.txt

RUN apk add --update --no-cache mariadb-client git curl tzdata gcc py3-gevent \
  && pip3 install -r ./requirements.txt \
  && adduser -D anubis \
  && ln -fs /usr/share/zoneinfo/America/New_York /etc/localtime


COPY . .
RUN chown -R root:root . && chmod +x docker-entrypoint.sh

USER anubis
ENTRYPOINT /opt/app/docker-entrypoint.sh

FROM python:3.8-alpine


RUN apk add --update --no-cache curl g++ \
  && pip3 install pyyaml requests parse redis
RUN adduser -D -H -u 1001 student \
  && mkdir -p /root/anubis/student \
  && chown student:student /root/anubis/student
WORKDIR /root/anubis

COPY pipeline.py pipeline.py
COPY utils.py utils.py
COPY assignment.yml assignment.yml
COPY assignment.py assignment.py

CMD python3 pipeline.py

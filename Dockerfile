# syntax=docker/dockerfile:1

FROM python:3.10-alpine3.15

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

RUN printf "0 8 * * * python3 /app/main.py\n" >> crontab-automation
RUN crontab crontab-automation

COPY main.py main.py
COPY modifiedSpotifyAuth.py modifiedSpotifyAuth.py
COPY new.png new.png
COPY shuffle.png shuffle.png

CMD python3 main.py && crond -f
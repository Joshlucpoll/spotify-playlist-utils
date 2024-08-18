# syntax=docker/dockerfile:1

FROM python:3.10-alpine3.15

# Install build dependencies for Pillow
RUN apk add --update --no-cache --virtual .build-deps \
  gcc libc-dev linux-headers zlib-dev jpeg-dev \
  && pip3 install Pillow \
  && apk del .build-deps

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY main.py main.py
COPY modifiedSpotifyAuth.py modifiedSpotifyAuth.py
COPY new.png new.png
COPY shuffle.png shuffle.png
COPY random_interval.png random_interval.png

CMD python3 main.py
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

RUN apt-get update && \
    apt-get install -yq \
        python3 \
        python3-pip \
        python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ADD requirements.txt /tmp/requirements.lock
RUN pip3 install -U pip
RUN pip3 install -r /tmp/requirements.lock

WORKDIR /app
ADD . .

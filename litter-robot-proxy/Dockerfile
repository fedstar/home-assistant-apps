ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-python:3.11-alpine3.18
FROM $BUILD_FROM

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY litter-robot-proxy.py .
COPY packet_capture.py .
COPY run.sh .

RUN chmod +x run.sh

CMD ["/app/run.sh"]

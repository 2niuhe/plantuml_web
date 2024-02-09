FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y default-jdk && \
    pip3 install --no-cache-dir nicegui && \
    apt clean && \
	rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . /app

CMD ["sh", "start.sh"]
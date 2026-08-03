FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir flask
#RUN apt-get update && apt-get install -y --no-install-recommends iputils-ping curl && rm -rf /var/lib/apt/lists/*

COPY scripts/mock_api.py .

EXPOSE 5000

CMD ["python", "mock_api.py"]

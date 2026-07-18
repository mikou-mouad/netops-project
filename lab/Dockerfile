FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir flask

COPY scripts/mock_api.py .

EXPOSE 5000

CMD ["python", "mock_api.py"]

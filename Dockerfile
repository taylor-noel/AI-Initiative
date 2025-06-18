# Use the official Python image from the Docker Hub
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install debugpy

COPY hello.py hello.py

CMD ["python", "-m", "debugpy", "--listen", "0.0.0.0:5678", "--wait-for-client", "hello.py"]

EXPOSE 5678

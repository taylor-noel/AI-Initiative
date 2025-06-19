FROM python:3.11-slim

WORKDIR /app/src

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
RUN pip install debugpy

COPY src/ /app/src/

CMD ["python", "-m", "debugpy", "--listen", "0.0.0.0:5678", "--wait-for-client", "hello"]

EXPOSE 5678

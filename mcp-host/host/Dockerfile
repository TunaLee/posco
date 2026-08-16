FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY host.py index.html ./
ENV HOST_BIND=0.0.0.0 PORT=8080
EXPOSE 8080
CMD ["python", "host.py"]

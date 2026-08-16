FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .
EXPOSE 8000
# 서버 파일은 mcp.run() 한 줄로 끝난다. 전송 방식은 여기서 준다.
CMD ["fastmcp", "run", "server.py", "--transport", "http", "--host", "0.0.0.0", "--port", "8000"]

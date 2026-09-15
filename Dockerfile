FROM python:3.12-slim
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
EXPOSE 8765
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8765","--workers","1","--no-access-log"]

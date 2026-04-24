# data/Dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PORT=5001
EXPOSE 5001
CMD ["python", "app.py"]
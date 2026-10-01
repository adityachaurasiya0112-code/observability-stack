FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir flask prometheus_client gunicorn
COPY app.py .
CMD ["gunicorn", "-b", "0.0.0.0:5000", "-w", "1", "--threads", "4", "app:app"]

FROM python:3.12-slim

WORKDIR /app

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

EXPOSE 8000

ENV APP_VERSION="v1" \
    APP_MESSAGE="Hello from Kubernetes v1"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

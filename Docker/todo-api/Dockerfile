# using official Python slim image as the base
FROM python:3.11-slim

# setting the working directory inside the container
WORKDIR /app

# copying requirements first to use Docker layer caching
COPY requirements.txt .

# installing all Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# copying the rest of the application code
COPY . .

# exposing port 8000 so the host can reach the API
EXPOSE 8000

# starting the FastAPI app using uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

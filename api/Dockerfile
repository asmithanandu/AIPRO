FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

EXPOSE 3001

# Command to run the application (will be overridden for celery in docker-compose)
CMD ["uvicorn", "main:socket_app", "--host", "0.0.0.0", "--port", "3001"]

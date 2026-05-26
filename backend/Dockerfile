# promptgram/backend/Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Install libmagic — the C library that python-magic needs on Linux
RUN apt-get update && apt-get install -y libmagic1 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Start the server. Ensure 'main:app' perfectly matches your Python file and app instance.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
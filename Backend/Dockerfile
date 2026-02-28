# Use official slim Python 3.13 image
FROM python:3.13-slim

# Set working directory inside container
WORKDIR /app

# Install system dependencies needed by psycopg2
RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (for layer caching)
COPY requirement.txt .
RUN pip install --no-cache-dir -r requirement.txt

# Copy the rest of the app
COPY . .

# Expose port for API
EXPOSE 8000

# Run API server
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

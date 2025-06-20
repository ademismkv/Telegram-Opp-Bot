# Use official Python image
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Expose port (if needed for Railway health checks)
EXPOSE 8000

# Set environment variables for Python
ENV PYTHONUNBUFFERED=1

# Run the main script (runs both bots)
CMD ["python", "main.py"] 
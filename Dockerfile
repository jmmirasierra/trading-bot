FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (needed for compiling pandas, numpy, ccxt if prebuilt wheels are not available)
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Create logs directory
RUN mkdir -p logs

# Run the bot
CMD ["python", "main.py"]

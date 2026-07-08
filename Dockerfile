FROM python:3.13-slim

WORKDIR /app

# Install system dependencies for Persian font support in PDF
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-dejavu \
    fonts-freefont-ttf \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY hesab/ ./hesab/
COPY .env .

WORKDIR /app/hesab

# Run the bot
CMD ["python", "main.py"]
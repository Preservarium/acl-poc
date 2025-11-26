FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /app/data

# Make init script executable and run it (it starts uvicorn at the end)
RUN chmod +x ./init_db.sh
CMD ["./init_db.sh"]

# Use a lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your code (main.py, resolver.py)
COPY . .

# Start the server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
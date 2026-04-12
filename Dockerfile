# Use a slim Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install basic system tools
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- THE MAGIC PART ---
# 1. Install Playwright's Chromium browser
RUN playwright install chromium
# 2. Tell Playwright to install all the Linux libraries Chromium needs
# This replaces that giant manual list and avoids "package not found" errors
RUN playwright install-deps chromium

# Copy the rest of your backend code
COPY . .

# Start the server (Port 10000 is Render's default for Docker)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
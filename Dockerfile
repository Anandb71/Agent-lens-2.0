# --- THIS IS THE FINAL FIX ---
# Use a specific, stable base image: python:3.11-bookworm (Debian 12)
# The "buster" (Debian 10) image is End-of-Life, and its package
# repositories are offline, which caused the "404 Not Found" error.
FROM python:3.11-bookworm

# Set the working directory
WORKDIR /app

# Install all system-level build tools (like gcc, make, etc.)
# This is still required.
RUN apt-get update && apt-get install -y build-essential

# Upgrade pip and setuptools first
RUN pip install --no-cache-dir --upgrade pip setuptools

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of our application code into the container
COPY . .

# Cloud Run sets a $PORT environment variable. We default to 8080 if it's not set.
ENV PORT 8080

# This command is correct.
CMD python -m gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT server:app
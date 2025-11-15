# Use an official lightweight Python image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system-level build tools (like gcc) that pip needs
# to compile some of the dependencies in google-adk.
RUN apt-get update && apt-get install -y build-essential

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of our application code into the container
COPY . .

# Cloud Run sets a $PORT environment variable. We default to 8080 if it's not set.
ENV PORT 8080

# --- THIS IS THE FINAL FIX ---
# The shell can't find the 'gunicorn' executable.
# We will use 'python -m gunicorn' to tell Python to run the gunicorn module directly.
# This bypasses all PATH issues.
CMD python -m gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT server:app
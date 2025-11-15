# --- THIS IS THE FIX ---
# Use the full, standard Python image instead of "slim".
# This image is more stable and includes all system libraries needed
# for complex packages like google-adk.
FROM python:3.11

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of our application code into the container
COPY . .

# Cloud Run sets a $PORT environment variable. We default to 8080 if it's not set.
ENV PORT 8080

# This command is correct. The problem was that gunicorn was never installed.
CMD python -m gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT server:app
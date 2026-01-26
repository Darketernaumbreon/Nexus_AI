
# Base image: python:3.11-slim
FROM python:3.11-slim

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies (if any needed for asyncpg/etc build, usually slim has enough for pure python wheels, 
# but sometimes we need build-essential. For now, simplest path.)
# We might need libpq-dev for psycopg2, but we are using asyncpg.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
# Group: appgroup (gid 1000)
# User: appuser (uid 1000)
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy application code
COPY . .

# Change ownership of the application code to the non-root user
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose port (documentary)
EXPOSE 8000

# Command to run the application
# Using uvicorn directly for now, usually behind gunicorn in prod but prompt asked for initializing FastAPI/Starlette
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

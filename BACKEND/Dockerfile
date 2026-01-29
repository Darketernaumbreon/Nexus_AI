
# Base image: python:3.11 (Full Bookworm version for better wheel compatibility)
FROM python:3.11-bookworm

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
# cmake: for xgboost
# gdal: for rasterio/fiona
# build-essential: for compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libpq-dev \
    libgdal-dev \
    gdal-bin \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set GDAL environment variables to help pip find headers
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# Update pip and install build seeds
RUN pip install --no-cache-dir --upgrade pip setuptools wheel numpy cython

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

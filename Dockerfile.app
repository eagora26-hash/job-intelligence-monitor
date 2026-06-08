# Image for the Job Intelligence Monitor (scheduler + dashboard share this image).
# Named Dockerfile.app to avoid clobbering the vendored Scrapling library's Dockerfile.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps for lxml / curl_cffi wheels are typically prebuilt; keep the image lean.
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (better layer caching). Dashboard layer = core + app + dashboard.
COPY requirements.txt requirements-dashboard.txt requirements-api.txt ./
RUN pip install --upgrade pip && pip install -r requirements-dashboard.txt -r requirements-api.txt

# Copy the vendored Scrapling engine, the application package, and entrypoints.
COPY scrapling ./scrapling
COPY job_monitor ./job_monitor
COPY main.py generate_demo_data.py ./

# Runtime data directories (also provided as volumes by docker-compose).
RUN mkdir -p database data logs backup exports

# Default: run the scheduler. docker-compose overrides this for the dashboard service.
CMD ["python", "main.py", "--loop"]

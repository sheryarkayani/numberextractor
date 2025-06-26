# --- Builder Stage ---
FROM python:3.9-slim as builder

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Final Stage ---
FROM python:3.9-slim

# Set non-interactive frontend for package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install Google Chrome and its dependencies from the official repository
RUN apt-get update && apt-get install -y --no-install-recommends wget gnupg && \
    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' && \
    apt-get update && \
    apt-get install -y google-chrome-stable --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed packages and executables from builder stage
COPY --from=builder /usr/local/lib/python3.9/site-packages/ /usr/local/lib/python3.9/site-packages/
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app/requirements.txt .

# Copy the rest of the application
COPY . .

# Set the HEADLESS environment variable
ENV HEADLESS=true

# Expose port and run the app
EXPOSE 5000
CMD gunicorn --bind "0.0.0.0:${PORT}" "app:app"
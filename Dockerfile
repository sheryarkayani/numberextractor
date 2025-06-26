# --- Builder Stage ---
FROM python:3.9-slim as builder

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Final Stage ---
FROM python:3.9-slim

# Install necessary dependencies for Chrome
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    fonts-liberation \
    libu2f-udev \
    libvulkan1 \
    pciutils \
    unzip \
    wget \
    xdg-utils && \
    rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get install -y ./google-chrome-stable_current_amd64.deb --no-install-recommends && \
    rm google-chrome-stable_current_amd64.deb

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.9/site-packages/ /usr/local/lib/python3.9/site-packages/
COPY --from=builder /app/requirements.txt .

# Copy the rest of the application
COPY . .

# Set the HEADLESS environment variable
ENV HEADLESS=true

# Expose port and run the app
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:${PORT}", "app:app"]
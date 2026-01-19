# Use Python 3.11 Slim (Stable & Small)
FROM python:3.11-slim-bookworm

# 1. Install System Dependencies for Firefox/Camoufox
# These are required for the browser to launch in Linux
RUN apt-get update && apt-get install -y \
    wget \
    xvfb \
    libgtk-3-0 \
    libdbus-glib-1-2 \
    libxt6 \
    libasound2 \
    libx11-xcb1 \
    && rm -rf /var/lib/apt/lists/*

# 2. Set up working directory
WORKDIR /app

# 3. Install Python Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Download the Camoufox Browser Binary
# This step is critical; otherwise it tries to download it every time you run the script
RUN python -m camoufox fetch

# 5. Copy your script
COPY scraper.py .

# 6. Run command
CMD ["python", "scraper.py"]
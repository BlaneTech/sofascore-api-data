FROM mcr.microsoft.com/playwright/python:v1.50.0-jammy

WORKDIR /app

# Playwright needs libs for Chromium. 'install-deps' handles most.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Chromium + system deps for Playwright
RUN python -m playwright install-deps chromium && python -m playwright install chromium

COPY . .

ENV APP_PORT=8000
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

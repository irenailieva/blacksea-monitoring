FROM python:3.10-slim

WORKDIR /app

# Install system dependencies including GDAL
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set GDAL environment variables to help pip find it
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# Копирай requirements и инсталирай Python пакети
COPY requirements.txt .
RUN pip3 install --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

# Копирай ETL кода
COPY . .

# Създай output директория
RUN mkdir -p /app/out

# CMD ще бъде override-нат от docker-compose
CMD ["python3", "-u", "flows/pipeline.py"]

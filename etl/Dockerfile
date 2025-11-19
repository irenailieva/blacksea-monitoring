FROM osgeo/gdal:ubuntu-full-3.6.2

WORKDIR /app

# Копирай requirements
COPY requirements.txt .

RUN apt-get update && apt-get install -y python3-pip python3-dev g++
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

# Копирай ETL кода
COPY . .

CMD ["python3", "-u", "flows/pipeline.py"]

FROM python:3.10-slim

WORKDIR /backend

# Fix: Changed libgl1-mesa-glx to libgl1 for the latest Debian versions
RUN apt-get update && apt-get install -y libgl1 libglib2.0-0 gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
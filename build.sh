#!/bin/bash
set -e
pip install --upgrade pip
pip install -r requirements.txt
# Make sure uvicorn is in the right place
cp /usr/local/bin/uvicorn /app/uvicorn || true

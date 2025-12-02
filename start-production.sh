#!/bin/bash
# Production startup script for Render
# This script is used by render.yaml

cd ai-worker
exec uvicorn app:app --host 0.0.0.0 --port ${PORT:-10000} --workers 1

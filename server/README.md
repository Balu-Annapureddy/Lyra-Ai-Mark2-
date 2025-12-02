# Lyra AI Mark2 - Server Deployment

This directory contains the production server code for Render deployment.

## Structure

```
server/
├── app.py              # Main FastAPI application
├── requirements.txt    # Python dependencies (Render-optimized)
├── runtime.txt         # Python 3.10.13
├── api/               # API routes
├── core/              # Core managers and systems
├── error/             # Error handling
├── skills/            # AI skills
├── tools/             # Utility tools
└── config/            # Configuration files
```

## Deployment

This directory is configured for Render deployment via `render.yaml` in the project root.

**Python Version**: 3.10.13 (specified in runtime.txt)

**Dependencies**: Optimized for Render with compatible versions:
- Pillow 10.2.0 (Python 3.10 compatible)
- opencv-python-headless (required for Render)
- numpy 1.26.2 (stable with Python 3.10)

## Local Development

```bash
cd server
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows
pip install -r requirements.txt
python app.py
```

## Production

Deployed automatically via Render when pushing to GitHub.

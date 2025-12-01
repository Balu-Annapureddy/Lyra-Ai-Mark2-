from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# Initialize minimal app
app = FastAPI(
    title="Lyra AI Worker (Lite)",
    description="Lightweight version for Railway deployment",
    version="2.0.0-lite"
)

# Configure CORS
origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Lyra AI worker running successfully"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/status")
async def status():
    """Minimal status endpoint"""
    return {
        "status": "online",
        "cpu_percent": 0,
        "ram_percent": 0,
        "gpu_available": False,
        "active_models": []
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))

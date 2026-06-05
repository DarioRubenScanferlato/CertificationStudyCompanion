import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Databricks DE Cert Study Companion API",
    description="Backend API for studying for Databricks Data Engineer certification",
    version="0.1.0"
)

# Enable CORS with environment-based origins
cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    """Health check endpoint."""
    return {
        "success": True,
        "data": {"status": "healthy", "version": "0.1.0"},
        "error": None
    }


@app.get("/api/health")
def api_health():
    """API health check endpoint."""
    return {
        "success": True,
        "data": {"status": "API healthy"},
        "error": None
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)

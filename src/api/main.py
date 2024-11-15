from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings
from .routers import emails

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="API for searching and indexing emails",
    version="1.0.0"
)

# CORS middleware for Electron app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your Electron app origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(emails.router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 
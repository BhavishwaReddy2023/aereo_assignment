from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.routes import jobs, certificates

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown initialization."""
    # Ensure database tables are created on startup
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API to validate recipient data, generate bulk PDF certificates in background, and track job progress.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for Swagger UI and local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(jobs.router)
app.include_router(certificates.router)

@app.get("/", tags=["Health"])
def health_check():
    """Root health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "docs": "/docs"
    }

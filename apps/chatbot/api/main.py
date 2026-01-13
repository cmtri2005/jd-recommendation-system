"""FastAPI Backend for JD Recommendation System."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from routers.router import router
from routers.dashboard import router as dashboard_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="JD Recommendation API",
    description="API for resume evaluation and learning resources",
    version="1.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)
app.include_router(dashboard_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)

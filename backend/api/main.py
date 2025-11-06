"""
Main FastAPI application for LCR Civil Drainage Automation System
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.core import settings, get_db
from backend.api.routes import area_calculation, spec_extraction, dia_report, qa_review, proposals

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-ready civil engineering automation platform for drainage analysis, regulatory compliance, and document generation",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for Docker"""
    return {"status": "healthy", "app": settings.APP_NAME, "version": settings.APP_VERSION}


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "modules": {
            "A": "Automated Area Calculation Engine",
            "B": "UDC & DOTD Specification Extraction",
            "C": "Drainage Impact Analysis (DIA) Report Generator",
            "D": "Plan Review & QA Automation",
            "E": "Proposal & Document Automation",
        },
    }


# Database test endpoint
@app.get(f"{settings.API_PREFIX}/db-test")
async def test_database(db: Session = Depends(get_db)):
    """Test database connection"""
    try:
        db.execute("SELECT 1")
        return {"database": "connected", "status": "ok"}
    except Exception as e:
        return {"database": "error", "status": "failed", "error": str(e)}


# Include routers
app.include_router(
    area_calculation.router,
    prefix=f"{settings.API_PREFIX}/area-calculation",
    tags=["Module A - Area Calculation"],
)

app.include_router(
    spec_extraction.router,
    prefix=f"{settings.API_PREFIX}/spec-extraction",
    tags=["Module B - Specification Extraction"],
)

app.include_router(
    dia_report.router,
    prefix=f"{settings.API_PREFIX}/dia-report",
    tags=["Module C - DIA Report Generator"],
)

app.include_router(
    qa_review.router,
    prefix=f"{settings.API_PREFIX}/qa-review",
    tags=["Module D - Plan Review & QA Automation"],
)

app.include_router(
    proposals.router,
    prefix=f"{settings.API_PREFIX}/proposals",
    tags=["Module E - Proposal & Document Automation"],
)


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'configured'}")
    print(f"Docs available at: /docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    print(f"Shutting down {settings.APP_NAME}")

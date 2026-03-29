from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.v1.router import api_router
from app.db.mysql import engine, Base
from app.db.mongo import get_mongo_client, close_mongo_connection

# Import all models so SQLAlchemy can discover them for table creation
from app.models import user, product, order, payment  # noqa: F401


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Ecommerce API...")

    # Create MySQL tables (use Alembic migrations in production)
    Base.metadata.create_all(bind=engine)
    print("✅ MySQL tables ready")

    # Warm-up MongoDB connection
    get_mongo_client()
    print("✅ MongoDB connected")

    yield

    # Shutdown
    await close_mongo_connection()
    print("👋 Shutting down...")


# ── App factory ───────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## Ecommerce REST API

Built with **FastAPI**, **MySQL** (SQLAlchemy), and **MongoDB** (Motor).

### Modules
| Module | Description |
|---|---|
| **Authentication** | JWT-based login, refresh tokens, social login |
| **User Management** | Registration, profile, password reset |
| **Product Catalog** | Browse, search, product details |
| **Cart** | Add/remove items (MongoDB), checkout |
| **Orders** | History, confirmation, tracking |
| **Payments** | Multi-method payment, receipts |

### Getting Started
1. Register via `POST /api/v1/users/register`
2. Login via `POST /api/v1/auth/login` to get a JWT
3. Click **Authorize** (🔓) and paste the access token
""",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global exception handler ──────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__},
    )

# ── Routes ────────────────────────────────────────────────────────────────────

app.include_router(api_router)


@app.get("/", tags=["Health"])
def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}

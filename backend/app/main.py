"""Thread It API — FastAPI application entrypoint.

v1 hello-world slice: a CORS-enabled app with a cheap /health endpoint. The
frontend pings /health on page load to warm Render's free tier out of cold
start while the user reads the page (see docs/ROADMAP.md).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import admin, cart, checkout, products

app = FastAPI(title=settings.app_name)

# Separated frontend + backend = cross-origin, so CORS is unavoidable.
# Allowlist the known frontend origin(s) only.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router)
app.include_router(cart.router)
app.include_router(admin.router)
app.include_router(checkout.router)


@app.get("/health")
def health() -> dict[str, str]:
    """Cheap liveness check. Also the cold-start warm-up ping target."""
    return {"status": "ok", "service": settings.app_name, "environment": settings.environment}


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Thread It API. See /docs for the OpenAPI spec."}

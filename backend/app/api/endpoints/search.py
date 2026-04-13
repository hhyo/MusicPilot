"""Search endpoints."""

from ..routes.jobs import router as jobs_router
from ..routes.search import router as router

__all__ = ["router", "jobs_router"]


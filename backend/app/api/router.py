"""Router registry for plugin APIs and probe APIs."""

from fastapi import APIRouter

from .health import router as health_router
from .routes.charts import router as charts_router
from .routes.dashboard import router as dashboard_router
from .routes.downloads import router as downloads_router
from .routes.jobs import router as jobs_router
from .routes.organize import router as organize_router
from .routes.probe import router as probe_router
from .routes.search import router as search_router
from .routes.settings import router as settings_router
from .routes.subscriptions import router as subscriptions_router

plugin_api_router = APIRouter()
plugin_api_router.include_router(health_router)
plugin_api_router.include_router(dashboard_router)
plugin_api_router.include_router(charts_router)
plugin_api_router.include_router(search_router)
plugin_api_router.include_router(subscriptions_router)
plugin_api_router.include_router(jobs_router)
plugin_api_router.include_router(downloads_router)
plugin_api_router.include_router(organize_router)
plugin_api_router.include_router(settings_router)

probe_api_router = APIRouter()
probe_api_router.include_router(probe_router)


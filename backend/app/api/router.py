"""Router registry for plugin APIs and probe APIs."""

from fastapi import APIRouter

from .health import router as health_router
from .endpoints.chart import router as charts_router
from .endpoints.dashboard import router as dashboard_router
from .endpoints.download import router as downloads_router
from .endpoints.media import router as media_router
from .endpoints.probe import router as probe_router
from .endpoints.search import jobs_router, router as search_router
from .endpoints.settings import router as settings_router
from .endpoints.subscribe import router as subscriptions_router
from .endpoints.transfer import router as organize_router

plugin_api_router = APIRouter()
plugin_api_router.include_router(health_router)
plugin_api_router.include_router(dashboard_router)
plugin_api_router.include_router(charts_router)
plugin_api_router.include_router(search_router)
plugin_api_router.include_router(media_router)
plugin_api_router.include_router(subscriptions_router)
plugin_api_router.include_router(jobs_router)
plugin_api_router.include_router(downloads_router)
plugin_api_router.include_router(organize_router)
plugin_api_router.include_router(settings_router)

probe_api_router = APIRouter()
probe_api_router.include_router(probe_router)

from fastapi import APIRouter

from .users.views import router as users_router
from .airports.views import router as airports_router

router = APIRouter(prefix="/api")
router.include_router(router=users_router)
router.include_router(router=airports_router)

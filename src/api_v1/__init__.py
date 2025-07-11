from fastapi import APIRouter

from .airports.views import router as airports_router
from .users.views import router as users_router
from .cities.views import router as cities_router

router = APIRouter(prefix="/api")
router.include_router(router=users_router)
router.include_router(router=airports_router)
router.include_router(router=cities_router)

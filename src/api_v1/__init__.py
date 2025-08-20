from fastapi import APIRouter

from .airports.views import router as airports_router
from .cities.views import router as cities_router
from .comments.views import router as comments_router
from .users.views import router as users_router

router = APIRouter(prefix="/api")
router.include_router(router=users_router)
router.include_router(router=airports_router)
router.include_router(router=cities_router)
router.include_router(router=comments_router)

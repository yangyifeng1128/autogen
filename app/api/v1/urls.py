from fastapi import APIRouter

from .endpoints.users import router as users_router

router = APIRouter(
    prefix="/v1",
)
sub_routers = [
    users_router,
]

for sub_router in sub_routers:
    sub_router.tags = router.tags.append("v1")
    router.include_router(sub_router)

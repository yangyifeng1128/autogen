"""路由"""

from fastapi import APIRouter

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.get("")
def get_users():
    """路由方法"""
    return []

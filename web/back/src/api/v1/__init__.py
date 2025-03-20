from fastapi import APIRouter
from .users import auth, ping, role, user
from .patients import patient

router = APIRouter()
router.include_router(ping.router, prefix="", tags=["ping"])
router.include_router(auth.router, prefix="", tags=["auth"])
router.include_router(user.router, prefix="/users", tags=["users"])
router.include_router(role.router, prefix="/roles", tags=["roles"])
# router.include_router(patients, prefix="/patients", tags=["patients"])
# router.include_router(parameters, prefix="/parameters", tags=["parameters"])
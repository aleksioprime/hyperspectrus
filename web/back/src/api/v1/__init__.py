from fastapi import APIRouter
from .users import auth, ping, role, user, organization
from .patients import patient, session
from .parameters import device

router = APIRouter()
router.include_router(ping.router, prefix="", tags=["ping"])
router.include_router(auth.router, prefix="", tags=["auth"])
router.include_router(user.router, prefix="/users", tags=["users"])
router.include_router(role.router, prefix="/roles", tags=["roles"])
router.include_router(organization.router, prefix="/organizations", tags=["organizations"])
router.include_router(patient.router, prefix="/patients", tags=["patients"])
router.include_router(session.router, prefix="/sessions", tags=["sessions"])
router.include_router(device.router, prefix="/devices", tags=["devices"])
from fastapi import APIRouter
from .users import auth, ping, role, user, organization
from .patients import patient, session, raw_image, result
from .parameters import device, spectrum, chromophore, overlap

router = APIRouter()
router.include_router(ping.router, prefix="", tags=["ping"])
router.include_router(auth.router, prefix="", tags=["auth"])
router.include_router(user.router, prefix="/users", tags=["users"])
router.include_router(role.router, prefix="/roles", tags=["roles"])
router.include_router(organization.router, prefix="/organizations", tags=["organizations"])
router.include_router(patient.router, prefix="/patients", tags=["patients"])
router.include_router(session.router, prefix="/patients/{patient_id}/sessions", tags=["sessions"])
router.include_router(raw_image.router, prefix="/raw_images", tags=["raw_image"])
router.include_router(result.router, prefix="/results", tags=["results"])
router.include_router(device.router, prefix="/devices", tags=["devices"])
router.include_router(spectrum.router, prefix="/spectra", tags=["spectra"])
router.include_router(chromophore.router, prefix="/chromophores", tags=["chromophores"])
router.include_router(overlap.router, prefix="/overlaps", tags=["overlaps"])
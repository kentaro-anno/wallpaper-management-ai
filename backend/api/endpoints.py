from fastapi import APIRouter
from .routes import system, duplicates, classify, settings, browser

router = APIRouter()

router.include_router(system.router, prefix="/system", tags=["system"])
router.include_router(duplicates.router, prefix="/duplicates", tags=["duplicates"])
router.include_router(classify.router, prefix="/classify", tags=["classify"])
router.include_router(settings.router, prefix="/settings", tags=["settings"])
router.include_router(browser.router, prefix="/browser", tags=["browser"])

# Backward compatibility or common image utility
router.include_router(classify.router, prefix="/images", tags=["images"]) # For /api/images/preview

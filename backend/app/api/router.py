from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["Health"])
def health_check():
    """
    Health check.

    Confirms the API process is running and able to respond to requests.
    """
    return {"status": "ok"}
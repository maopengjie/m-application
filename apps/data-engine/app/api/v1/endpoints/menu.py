from fastapi import APIRouter, Depends
from app.utils.responses import response_success
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/menu", tags=["menu"], dependencies=[Depends(get_current_user)])

@router.get("/all")
async def get_all_menus():
    """Return all menus for the user. Return an empty list if using frontend menus."""
    # Vben V3 can use either backend menus or frontend routes. 
    # Returning an empty list here to signal use of frontend-defined menus if that's the setup,
    # or return actual RouteRecord definitions.
    return response_success([])

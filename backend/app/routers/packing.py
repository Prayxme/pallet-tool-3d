from fastapi import APIRouter, HTTPException
from app.models.schemas import PackingRequest
from app.services.packing_service import optimizar_orden_pallets

router = APIRouter(prefix="/api", tags=["Pallet Packing Engine"])

@router.post("/pack")
async def calculate_packing(request: PackingRequest):
    try:
        return optimizar_orden_pallets(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el motor de optimización: {str(e)}")
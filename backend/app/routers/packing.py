from fastapi import APIRouter, HTTPException
from app.models.schemas import PackingRequest
from app.services.packing_service import optimizar_orden_pallets

router = APIRouter(prefix="/api", tags=["Pallet Packing Engine"])

@router.post("/pack")
async def calculate_packing(request: PackingRequest):
    try:
        resultado = optimizar_orden_pallets(request)
        if resultado is None:
            raise HTTPException(status_code=500, detail="El motor optimizador retornó None (posible fallo de tabulación en packing_service.py).")
        return resultado
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el motor de optimización: {str(e)}")
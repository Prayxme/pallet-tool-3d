from typing import List
from pydantic import BaseModel, Field

class Dimensions(BaseModel):
    length_in: float = Field(..., gt=0, description="Largo de la caja en pulgadas")
    width_in: float = Field(..., gt=0, description="Ancho de la caja en pulgadas")
    height_in: float = Field(..., gt=0, description="Alto de la caja en pulgadas")

class OrderItem(BaseModel):
    sku: str
    quantity: int = Field(..., gt=0, description="Cantidad de cartones/cajas")
    dimensions: Dimensions
    weight_lbs: float = Field(..., gt=0, description="Peso por caja en libras")

class PalletConfig(BaseModel):
    length_in: float = 48.0
    width_in: float = 40.0
    base_height_in: float = 5.5
    max_total_height_in: float = 85.0
    max_weight_lbs: float = 4500.0

class PackingRequest(BaseModel):
    order_id: str
    pallet_config: PalletConfig
    items: List[OrderItem]

class ParsedItem(BaseModel):
    sku: str
    qty: int
    l: float
    w: float
    h: float
    weight: float

class ParsedPdfResponse(BaseModel):
    company: str
    cust_no: str
    piktik: str
    po: str
    items: List[ParsedItem]
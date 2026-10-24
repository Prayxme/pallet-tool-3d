from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import ALLOWED_ORIGINS
from app.routers import packing, pdf

app = FastAPI(
    title="Golden State Pallet Tool 3D API",
    version="2.0.0",
    description="Motor industrial de estiba 3D, parsing de pick tickets y planificación de tráilers (WMS)."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusión de Routers Modulares
app.include_router(packing.router)
app.include_router(pdf.router)

@app.get("/health", tags=["Health Check"])
async def health_check():
    return {"status": "online", "system": "Golden State Pallet Engine"}
from typing import List

# Constantes del Servidor y CORS
ALLOWED_ORIGINS: List[str] = ["*"]

# Tolerancias del Motor Físico (Pulgadas)
TOLERANCIA_ALTURA_SOPORTE: float = 0.1
UMBRAL_MINIMO_SOPORTE: float = 0.75  # 75% de la base apoyada
TOLERANCIA_DESBALANCE_COG: float = 0.15  # Máximo 15% de desviación del centro

# Límites Operativos de Pallets por Defecto
DEFAULT_MAX_WEIGHT_LBS: float = 4500.0
DEFAULT_BASE_HEIGHT_IN: float = 5.5
DEFAULT_MAX_TOTAL_HEIGHT_IN: float = 85.0
import copy
from typing import Dict, Any, List
from py3dbp import Bin, Item, Packer
from app.models.schemas import PackingRequest
from app.services.physics_engine import aplicar_gravedad, construir_pallet_dict

def optimizar_orden_pallets(request: PackingRequest) -> Dict[str, Any]:
    """
    Motor de optimización en dos fases:
    1. Fase Homogénea: Calcula la estiba óptima unitaria por SKU y clona pallets completos instantáneamente.
    2. Fase Mixta: Consolida los residuos de todos los SKUs en pallets mixtos con caída por gravedad controlada.
    """
    config = request.pallet_config
    net_height = config.max_total_height_in - config.base_height_in
    response_pallets: List[Dict[str, Any]] = []
    pool_mixto: List[Dict[str, Any]] = []
    pallet_counter = 1

    # =========================================================================
    # FASE 1: PALLETS HOMOGÉNEOS (Cálculo unitario + clonación masiva)
    # =========================================================================
    for item in request.items:
        vol_caja = item.dimensions.length_in * item.dimensions.width_in * item.dimensions.height_in
        vol_util = config.width_in * config.length_in * net_height
        max_teorico = max(1, int(vol_util / vol_caja) + 6)
        candidatos = min(item.quantity, max_teorico)

        # Probar capacidad en 1 pallet de muestra
        test_packer = Packer()
        test_packer.add_bin(Bin('TEST', config.width_in, net_height, config.length_in, config.max_weight_lbs))
        for idx in range(candidatos):
            test_packer.add_item(Item(
                f"{item.sku}###{idx}",
                item.dimensions.width_in,
                item.dimensions.height_in,
                item.dimensions.length_in,
                item.weight_lbs
            ))
        test_packer.pack()

        test_bin = test_packer.bins[0]
        # Aplicar gravedad restringida a la altura neta permitida
        aplicar_gravedad(test_bin.items, max_h_util=net_height)
        capacidad_pallet = len(test_bin.items)

        # Si el lote llena al menos 1 pallet entero
        if capacidad_pallet > 0 and item.quantity >= capacidad_pallet:
            pallets_completos = item.quantity // capacidad_pallet
            remanente = item.quantity % capacidad_pallet

            # Construir plantilla del pallet homogéneo
            plantilla_dict = construir_pallet_dict(test_bin, config, "PALLET-TEMP")
            
            # Clonar los pallets idénticos en milisegundos
            for _ in range(pallets_completos):
                p_copy = copy.deepcopy(plantilla_dict)
                p_copy["pallet_id"] = f"PALLET-{pallet_counter}"
                response_pallets.append(p_copy)
                pallet_counter += 1

            # Las cajas sobrantes van al pool de empaque mixto
            for rem_idx in range(remanente):
                pool_mixto.append({
                    "sku": item.sku,
                    "w": item.dimensions.width_in,
                    "h": item.dimensions.height_in,
                    "d": item.dimensions.length_in,
                    "weight": item.weight_lbs,
                    "name": f"{item.sku}###REM_{rem_idx}"
                })
        else:
            # Si el SKU no alcanza a llenar ni un pallet completo, va al pool mixto
            for rem_idx in range(item.quantity):
                pool_mixto.append({
                    "sku": item.sku,
                    "w": item.dimensions.width_in,
                    "h": item.dimensions.height_in,
                    "d": item.dimensions.length_in,
                    "weight": item.weight_lbs,
                    "name": f"{item.sku}###REM_{rem_idx}"
                })

    # =========================================================================
    # FASE 2: PALLETS MIXTOS (Empaque de sobrantes consolidados)
    # =========================================================================
    if pool_mixto:
        mixed_packer = Packer()
        
        # Calcular dinámicamente cuántas posiciones de pallet mixto habilitar
        vol_cajas_mixtas = sum(c["w"] * c["h"] * c["d"] for c in pool_mixto)
        vol_pallet = config.width_in * config.length_in * net_height
        bins_necesarios = max(5, int((vol_cajas_mixtas / (vol_pallet * 0.65))) + 2)
        
        for i in range(bins_necesarios):
            mixed_packer.add_bin(Bin(
                f'MIXED-{i+1}', 
                config.width_in, 
                net_height, 
                config.length_in, 
                config.max_weight_lbs
            ))
        
        # Ordenar residuo por peso de mayor a menor para garantizar estabilidad física
        pool_mixto.sort(key=lambda x: x["weight"], reverse=True)
        for c in pool_mixto:
            mixed_packer.add_item(Item(c["name"], c["w"], c["h"], c["d"], c["weight"]))
            
        mixed_packer.pack()

        for mb in mixed_packer.bins:
            if mb.items:
                # Gravedad y validación estricta de altura
                aplicar_gravedad(mb.items, max_h_util=net_height)
                
                # Solo guardar si quedaron
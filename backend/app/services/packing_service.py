import copy
from typing import Dict, Any
from py3dbp import Bin, Item, Packer
from app.models.schemas import PackingRequest
from app.services.physics_engine import aplicar_gravedad, construir_pallet_dict

def optimizar_orden_pallets(request: PackingRequest) -> Dict[str, Any]:
    config = request.pallet_config
    net_height = config.max_total_height_in - config.base_height_in
    response_pallets = []
    pool_mixto = []
    pallet_counter = 1

    # FASE 1: Cálculo de capacidad y clonación de pallets homogéneos
    for item in request.items:
        vol_caja = item.dimensions.length_in * item.dimensions.width_in * item.dimensions.height_in
        vol_util = config.width_in * config.length_in * net_height
        max_teorico = max(1, int(vol_util / vol_caja) + 6)
        candidatos = min(item.quantity, max_teorico)

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
        capacidad_pallet = len(test_bin.items)

        if capacidad_pallet > 0 and item.quantity >= capacidad_pallet:
            aplicar_gravedad(test_bin.items)
            pallets_completos = item.quantity // capacidad_pallet
            remanente = item.quantity % capacidad_pallet

            plantilla_dict = construir_pallet_dict(test_bin, config, "PALLET-TEMP")
            for _ in range(pallets_completos):
                p_copy = copy.deepcopy(plantilla_dict)
                p_copy["pallet_id"] = f"PALLET-{pallet_counter}"
                response_pallets.append(p_copy)
                pallet_counter += 1

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
            for rem_idx in range(item.quantity):
                pool_mixto.append({
                    "sku": item.sku,
                    "w": item.dimensions.width_in,
                    "h": item.dimensions.height_in,
                    "d": item.dimensions.length_in,
                    "weight": item.weight_lbs,
                    "name": f"{item.sku}###REM_{rem_idx}"
                })

    # FASE 2: Empaque de remanentes en pallets mixtos
    if pool_mixto:
        mixed_packer = Packer()
        for i in range(5):
            mixed_packer.add_bin(Bin(f'MIXED-{i+1}', config.width_in, net_height, config.length_in, config.max_weight_lbs))
        
        pool_mixto.sort(key=lambda x: x["weight"], reverse=True)
        for c in pool_mixto:
            mixed_packer.add_item(Item(c["name"], c["w"], c["h"], c["d"], c["weight"]))
            
        mixed_packer.pack()

        for mb in mixed_packer.bins:
            if mb.items:
                aplicar_gravedad(mb.items)
                pallet_dict = construir_pallet_dict(mb, config, f"PALLET-{pallet_counter}")
                response_pallets.append(pallet_dict)
                pallet_counter += 1

    return {
        "order_id": request.order_id,
        "pallets": response_pallets,
        "unplaced_boxes": 0
    }
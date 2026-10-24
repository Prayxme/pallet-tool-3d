from decimal import Decimal
from typing import List, Tuple, Dict, Any
from app.core.config import (
    TOLERANCIA_ALTURA_SOPORTE,
    UMBRAL_MINIMO_SOPORTE,
    TOLERANCIA_DESBALANCE_COG,
)

def aplicar_gravedad(b_items: list) -> None:
    """Proyecta cada caja hacia abajo en el eje Y hasta colisionar con otra o tocar el suelo."""
    b_items.sort(key=lambda item: float(item.position[1]))
    
    for i in range(len(b_items)):
        caja = b_items[i]
        pos_x = float(caja.position[0])
        pos_z = float(caja.position[2])
        w, _, d = [float(val) for val in caja.get_dimension()]
        
        max_y_debajo = 0.0
        for j in range(i):
            otra = b_items[j]
            ox = float(otra.position[0])
            oy = float(otra.position[1])
            oz = float(otra.position[2])
            ow, oh, od = [float(val) for val in otra.get_dimension()]
            
            superpone_x = (pos_x < ox + ow) and (pos_x + w > ox)
            superpone_z = (pos_z < oz + od) and (pos_z + d > oz)
            if superpone_x and superpone_z:
                techo = oy + oh
                if techo > max_y_debajo:
                    max_y_debajo = techo
                    
        caja.position[1] = Decimal(str(max_y_debajo))

def calcular_area_interseccion(caja_arriba, caja_abajo) -> float:
    x1_arriba, _, z1_arriba = [float(val) for val in caja_arriba.position]
    w_arriba, _, d_arriba = [float(val) for val in caja_arriba.get_dimension()]
    x2_arriba, z2_arriba = x1_arriba + w_arriba, z1_arriba + d_arriba

    x1_abajo, _, z1_abajo = [float(val) for val in caja_abajo.position]
    w_abajo, _, d_abajo = [float(val) for val in caja_abajo.get_dimension()]
    x2_abajo, z2_abajo = x1_abajo + w_abajo, z1_abajo + d_abajo

    ix_izq, ix_der = max(x1_arriba, x1_abajo), min(x2_arriba, x2_abajo)
    iz_front, iz_tras = max(z1_arriba, z1_abajo), min(z2_arriba, z2_abajo)

    if ix_der > ix_izq and iz_tras > iz_front:
        return (ix_der - ix_izq) * (iz_tras - iz_front)
    return 0.0

def analizar_soporte(b_items: list) -> List[Dict[str, str]]:
    warnings = []
    for caja in b_items:
        _, pos_y, _ = [float(val) for val in caja.position]
        w, _, d = [float(val) for val in caja.get_dimension()]
        if pos_y <= TOLERANCIA_ALTURA_SOPORTE:
            continue
            
        area_base = w * d
        area_soportada = 0.0
        for otra in b_items:
            _, y_ab, _ = [float(val) for val in otra.position]
            _, h_ab, _ = [float(val) for val in otra.get_dimension()]
            if abs((y_ab + h_ab) - pos_y) <= TOLERANCIA_ALTURA_SOPORTE:
                area_soportada += calcular_area_interseccion(caja, otra)

        pct = area_soportada / area_base if area_base > 0 else 1.0
        if pct < UMBRAL_MINIMO_SOPORTE:
            sku_limpio = caja.name.split('###')[0]
            warnings.append({
                "sku": sku_limpio,
                "mensaje": f"Soporte bajo en {sku_limpio}: {round(pct * 100, 1)}% apoyado."
            })
    return warnings

def analizar_equilibrio(b_items: list, pallet_w: float = 40.0, pallet_l: float = 48.0) -> Tuple[Dict[str, float], str, List[str]]:
    total_w, sum_x, sum_z = 0.0, 0.0, 0.0
    for item in b_items:
        peso = float(item.weight)
        fw, _, fd = [float(val) for val in item.get_dimension()]
        px, _, pz = [float(val) for val in item.position]
        sum_x += (px + fw / 2.0) * peso
        sum_z += (pz + fd / 2.0) * peso
        total_w += peso

    if total_w == 0:
        return {"x": 0.0, "z": 0.0}, "VACIA", []

    cog_x = sum_x / total_w
    cog_z = sum_z / total_w
    ideal_x, ideal_z = pallet_w / 2.0, pallet_l / 2.0
    warnings = []
    status = "ESTABLE"

    if abs(cog_x - ideal_x) > (pallet_w * TOLERANCIA_DESBALANCE_COG):
        status = "INESTABLE"
        warnings.append(f"Desbalance lateral (CoG X: {cog_x:.1f} in).")
    if abs(cog_z - ideal_z) > (pallet_l * TOLERANCIA_DESBALANCE_COG):
        status = "INESTABLE"
        warnings.append(f"Desbalance frontal (CoG Z: {cog_z:.1f} in).")

    return {"x": round(cog_x, 2), "z": round(cog_z, 2)}, status, warnings

def construir_pallet_dict(bin_obj, config, pallet_id_str: str) -> Dict[str, Any]:
    cog, status_eq, warn_eq = analizar_equilibrio(bin_obj.items, config.width_in, config.length_in)
    warn_sop = analizar_soporte(bin_obj.items)
    alertas = warn_eq + [w["mensaje"] for w in warn_sop]

    pallet_data = {
        "pallet_id": pallet_id_str,
        "metrics": {
            "total_weight_lbs": round(sum(float(item.weight) for item in bin_obj.items), 2),
            "boxes_count": len(bin_obj.items),
            "balance_status": status_eq,
            "center_of_gravity": cog,
            "voladizos_peligrosos": len(warn_sop),
            "alertas": alertas
        },
        "placed_items": []
    }

    for idx, item in enumerate(bin_obj.items):
        fw, fh, fd = [float(v) for v in item.get_dimension()]
        px, py, pz = [float(v) for v in item.position]
        pallet_data["placed_items"].append({
            "step_order": idx + 1,
            "sku": item.name.split('###')[0],
            "position": {"x": px, "y": py + config.base_height_in, "z": pz},
            "rendered_dimensions": {"width_in": fw, "height_in": fh, "length_in": fd}
        })
    return pallet_data
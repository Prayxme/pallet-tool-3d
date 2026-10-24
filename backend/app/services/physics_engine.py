def aplicar_gravedad(b_items: list, max_h_util: float = 79.5) -> list:
    """
    Aplica gravedad física estable a las cajas.
    Garantiza que ninguna caja flote en el aire y que ninguna sobrepase la altura máxima permitida.
    """
    # Ordenar por elevación original para asentar las capas inferiores primero
    b_items.sort(key=lambda item: float(item.position[1]))
    
    items_validos = []
    
    for i in range(len(b_items)):
        caja = b_items[i]
        pos_x = float(caja.position[0])
        pos_z = float(caja.position[2])
        w, h, d = [float(val) for val in caja.get_dimension()]
        
        max_y_debajo = 0.0
        for j in range(len(items_validos)):
            otra = items_validos[j]
            ox = float(otra.position[0])
            oy = float(otra.position[1])
            oz = float(otra.position[2])
            ow, oh, od = [float(val) for val in otra.get_dimension()]
            
            # Verificar si hay solapamiento en el plano horizontal X-Z con tolerancia
            superpone_x = (pos_x < ox + ow - 0.2) and (pos_x + w > ox + 0.2)
            superpone_z = (pos_z < oz + od - 0.2) and (pos_z + d > oz + 0.2)
            
            if superpone_x and superpone_z:
                techo = oy + oh
                if techo > max_y_debajo:
                    max_y_debajo = techo
                    
        # Validar que al asentar la caja no exceda el límite estructural de la paleta
        if max_y_debajo + h <= max_h_util + 0.5:
            caja.position[1] = Decimal(str(round(max_y_debajo, 2)))
            items_validos.append(caja)

    b_items.clear()
    b_items.extend(items_validos)
    return b_items
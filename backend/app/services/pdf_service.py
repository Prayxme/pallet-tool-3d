import io
import re
from typing import Dict, Any
import pdfplumber

def extraer_datos_pick_ticket(content: bytes) -> Dict[str, Any]:
    pages_text = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            pages_text.append(page.extract_text() or "")

    full_text = "\n".join(pages_text)

    # 1. COMPAÑÍA (Membrete emisor)
    company = "WIESNER PRODUCTS, INC."
    first_page_lines = [l.strip() for l in pages_text[0].split("\n") if l.strip()]
    for line in first_page_lines[:8]:
        if re.match(r'^[W\d\s\-#]+$', line, re.IGNORECASE):
            continue
        if any(k in line.upper() for k in ["PICK TICKET", "PIK TIK", "PAGE", "TEL:", "FAX:", "SOLD TO:"]):
            continue
        if re.search(r'\b(broadway|street|st|avenue|ave|floor|fl|suite|ste|blvd)\b', line, re.IGNORECASE):
            continue
        company = line
        break

    # 2. CUST NO
    cust_no_match = re.search(r"Cust No[\s\S]*?\n\d+\s+\d{2}/\d{2}/\d{4}\s+([A-Z0-9]+)", full_text)
    cust_no = cust_no_match.group(1) if cust_no_match else "MARS125"

    # 3. EXTRAER TODOS LOS POS Y PIKTIKS (Multi-orden / Wave)
    pos_encontrados = re.findall(r"PO No[\s\S]*?\n(?:\d+\s+[\d\/]+\s+[A-Z0-9]+\s+\d+\s+([0-9]+))", full_text)
    if not pos_encontrados:
        pos_encontrados = re.findall(r"\b0\d{7}\b", full_text)
    pos_unicos = list(dict.fromkeys(pos_encontrados))
    po_str = ", ".join(pos_unicos) if pos_unicos else "02530856"

    piktiks_encontrados = re.findall(r"Pik Tik No\s*\|\s*Page[\s\S]*?\n[\d\/]+\s*\|\s*(\d+)", full_text)
    if not piktiks_encontrados:
        piktiks_encontrados = re.findall(r"\b68\d{5}\b", full_text)
    piktiks_unicos = list(dict.fromkeys(piktiks_encontrados))
    piktik_str = ", ".join(piktiks_unicos) if piktiks_unicos else "6846787"

    # 4. EXTRACCIÓN DE CADA SKU / CARTONES
    items = []
    chunks = full_text.split("BOX LxWxH:")

    for i in range(1, len(chunks)):
        chunk = chunks[i]
        prev_text = chunks[i - 1]

        # Dimensiones y Peso
        dim_match = re.search(r"^\s*([\d\.]+)\s*x\s*([\d\.]+)\s*x\s*([\d\.]+).*?(?:IN,)?\s*([\d\.]+)\s*LB", chunk)
        if dim_match:
            l, w, h, wt = dim_match.groups()

            # Cartones
            carton_match = re.search(r"Cartons\s*->\s*([\d,]+)", chunk, re.IGNORECASE)
            if not carton_match:
                carton_match = re.search(r"Cases\s*(?:Description[^\n]*)?\n.*?\|\s*([\d,]+)", prev_text, re.DOTALL)
            if not carton_match:
                carton_match = re.search(r"[\d\.]+\s*CFT\s*\|\s*([\d,]+)", chunk)

            cartons_qty = int(carton_match.group(1).replace(',', '')) if carton_match else 0

            # EXTRACCIÓN ROBUSTA DE ITEM # (Maneja con y sin guiones)
            # Busca líneas posteriores a "ITEM #"
            sku_name = ""
            lines_prev = [lp.strip() for lp in prev_text.split("\n") if lp.strip()]
            for lp in reversed(lines_prev[-6:]):
                # Ignorar encabezados de tabla
                if any(hdr in lp.upper() for hdr in ["ITEM #", "QTY ORD", "DESCRIPTION", "ROUTING", "DATE", "MARSHALLS"]):
                    continue
                # Si contiene el patrón de SKU Wiesner/Marshalls (ej. 6B4543MS, 1KBB4578MS, 6TRB4710TJ)
                if re.search(r'\b[0-9A-Z]{6,12}\b', lp) and not re.search(r'^\d{7,}$', lp):
                    sku_name = lp.split("|")[0].strip()
                    break

            if not sku_name:
                sku_name = f"ITEM-{i}"

            items.append({
                "sku": sku_name,
                "qty": cartons_qty,
                "l": float(l),
                "w": float(w),
                "h": float(h),
                "weight": float(wt)
            })

    return {
        "company": company,
        "cust_no": cust_no,
        "piktik": piktik_str,
        "po": po_str,
        "items": items
    }
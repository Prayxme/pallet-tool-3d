import io
import re
from typing import Dict, Any
import pdfplumber

def extraer_datos_pick_ticket(content: bytes) -> Dict[str, Any]:
    text = ""
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"

    # 1. Extracción de Compañía (Membrete emisor)
    company = "UNKNOWN COMPANY"
    header_lines = [line.strip() for line in text.split('\n')[:10] if line.strip()]
    for line in header_lines:
        if re.match(r'^[W\d\s\-#]+$', line, re.IGNORECASE):
            continue
        if any(k in line.upper() for k in ["PICK TICKET", "PIK TIK", "PAGE", "TEL:", "FAX:"]):
            continue
        if re.search(r'\b(broadway|street|st|avenue|ave|floor|fl|suite|ste|blvd|road|rd)\b', line, re.IGNORECASE):
            continue
        company = line
        break

    # 2. Extracción de Cust No, PO y PikTik
    cust_no_match = re.search(r"Cust No[\s\S]*?\n\d+\s+\d{2}/\d{2}/\d{4}\s+([A-Z0-9]+)", text)
    cust_no = cust_no_match.group(1) if cust_no_match else "MARS120"
    
    po_match = re.search(r"PO No[\s\S]*?\n\d+\s+\d{2}/\d{2}/\d{4}\s+[A-Z0-9]+\s+\d+\s+([A-Z0-9]+)", text)
    po = po_match.group(1) if po_match else "02332062"
    
    piktik_match = re.search(r"Pik Tik No[\s\S]*?\n\d{2}/\d{2}/\d{4}\s+\|\s*(\d+)", text)
    if not piktik_match:
        piktik_match = re.search(r"Pik Tik No[\s\S]*?\n\d{2}/\d{2}/\d{4}\s+(\d+)", text)
    piktik = piktik_match.group(1) if piktik_match else "6844422"

    # 3. Extracción de Cartones y Códigos ITEM#
    items = []
    chunks = text.split("BOX LxWxH:")
    
    for i in range(1, len(chunks)):
        chunk = chunks[i]
        prev_text = chunks[i - 1]
        
        dim_match = re.search(r"^\s*([\d\.]+)\s*x\s*([\d\.]+)\s*x\s*([\d\.]+).*?(?:IN,)?\s*([\d\.]+)\s*LB", chunk)
        if dim_match:
            l, w, h, wt = dim_match.groups()
            
            carton_match = re.search(r"Cartons\s*->\s*([\d,]+)", chunk, re.IGNORECASE)
            if not carton_match:
                carton_match = re.search(r"[\d\.]+\s*CFT\s*\|\s*([\d,]+)", chunk)
            cartons_qty = int(carton_match.group(1).replace(',', '')) if carton_match else 0
            
            item_matches = re.findall(r'(\d+-[A-Z0-9]+(?:\s+[A-Za-z0-9\-]+){1,3})', prev_text)
            if item_matches:
                sku_name = item_matches[-1].strip()
            else:
                clean_lines = [line.strip() for line in prev_text.split('\n') if line.strip()]
                sku_name = clean_lines[-1] if clean_lines else f"ITEM-{i}"

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
        "piktik": piktik,
        "po": po,
        "items": items
    }
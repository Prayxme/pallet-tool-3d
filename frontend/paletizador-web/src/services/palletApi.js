const BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api";

export async function parsePdfTicket(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${BASE_URL}/parse-pdf`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    let errorDetail = "Error analizando el PDF.";
    try {
      const err = await response.json();
      errorDetail = err.detail || errorDetail;
    } catch (_) {}
    throw new Error(errorDetail);
  }
  return await response.json();
}

export async function packOrder(payload) {
  let response;
  try {
    response = await fetch(`${BASE_URL}/pack`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch (netErr) {
    throw new Error("No se pudo conectar con el servidor backend (revisa que Uvicorn esté activo).");
  }

  if (!response.ok) {
    let errorDetail = "Error del motor de optimización.";
    try {
      const err = await response.json();
      errorDetail = err.detail || JSON.stringify(err);
    } catch (_) {
      errorDetail = await response.text();
    }
    throw new Error(errorDetail);
  }

  const data = await response.json();
  if (!data) {
    throw new Error("El motor backend devolvió una respuesta vacía (null).");
  }
  return data;
}
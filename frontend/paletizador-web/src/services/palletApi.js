const BASE_URL = "http://127.0.0.1:8000/api";

export async function parsePdfTicket(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${BASE_URL}/parse-pdf`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error("Error al analizar el PDF en el servidor.");
  }
  return await response.json();
}

export async function packOrder(payload) {
  const response = await fetch(`${BASE_URL}/pack`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error("Error al calcular el empaque de pallets.");
  }
  return await response.json();
}
export function agruparPallets(palletsArray) {
  const grupos = [];
  palletsArray.forEach((pallet) => {
    const firma = JSON.stringify(
      pallet.placed_items.map((i) => ({ sku: i.sku, pos: i.position }))
    );
    const grupoExistente = grupos.find((g) => g.firma === firma);
    if (grupoExistente) {
      grupoExistente.cantidad += 1;
    } else {
      grupos.push({ firma, cantidad: 1, data: pallet });
    }
  });
  return grupos;
}

export function calculateCenteredOffsets(palletData, palletWidth = 40, palletLength = 48) {
  if (!palletData || !palletData.placed_items.length) {
    return { x: 0, z: 0 };
  }
  let maxX = 0;
  let maxZ = 0;
  palletData.placed_items.forEach((item) => {
    const endX = item.position.x + item.rendered_dimensions.width_in;
    const endZ = item.position.z + item.rendered_dimensions.length_in;
    if (endX > maxX) maxX = endX;
    if (endZ > maxZ) maxZ = endZ;
  });
  return {
    x: Math.max(0, (palletWidth - maxX) / 2),
    z: Math.max(0, (palletLength - maxZ) / 2),
  };
}
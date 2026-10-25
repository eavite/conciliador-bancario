"""Exporta resultados de la demostración sin modificar las fuentes."""
import json
from pathlib import Path
import shutil


def exportar(resultado, resumen, servicios, fuentes, destino, banco, cierre):
    carpeta = Path(destino) / banco.lower().replace(" ", "-") / cierre.isoformat()
    cuadre = carpeta / "Cuadre"
    reportes = carpeta / "Reportes"
    if carpeta.exists():
        raise FileExistsError("Ya existe ese resultado. Elige otra carpeta de salida para conservarlo.")
    cuadre.mkdir(parents=True)
    reportes.mkdir()
    resultado.to_csv(cuadre / "conciliacion.csv", index=False)
    resultado.loc[resultado.estado != "Conciliado"].to_csv(cuadre / "por_revisar.csv", index=False)
    servicios.to_csv(cuadre / "coincidencias_servicios.csv", index=False)
    (cuadre / "resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for numero, fuente in enumerate(fuentes, start=1):
        shutil.copy2(fuente, reportes / f"{numero}_{Path(fuente).name}")
    return carpeta

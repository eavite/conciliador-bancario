"""Conciliación de ejemplo. Todos los archivos incluidos son sintéticos."""
from datetime import datetime, time, timedelta
from decimal import Decimal, InvalidOperation

import pandas as pd

HORAS_CORTE = {"Banco A": 17, "Banco B": 20}
CLAVES = ["cliente_id", "referencia"]
ESTADOS = ["Conciliado", "Diferencia de importe", "Solo en sistema", "Solo en banco"]


def leer_reporte(ruta, banco):
    datos = pd.read_csv(ruta, dtype=str, keep_default_na=False)
    columnas = ["banco", "cliente_id", "referencia", "fecha", "importe"]
    if not set(columnas).issubset(datos.columns):
        raise ValueError("El CSV debe incluir: " + ", ".join(columnas))
    datos = datos.loc[datos["banco"].str.strip() == banco, columnas].copy()
    datos["cliente_id"] = datos["cliente_id"].str.strip().str.upper()
    datos["referencia"] = datos["referencia"].str.strip()
    if (datos["cliente_id"] == "").any() or datos.empty:
        raise ValueError("El reporte no tiene filas válidas para el banco seleccionado.")
    if (datos["referencia"] == "").any():
        raise ValueError("Hay referencias vacías en el reporte.")
    datos["referencia"] = datos["referencia"].str.lstrip("0").replace("", "0")
    datos["fecha"] = pd.to_datetime(datos["fecha"], format="%Y-%m-%d %H:%M:%S", errors="raise")
    if datos["fecha"].isna().any():
        raise ValueError("Hay fechas vacías en el reporte.")
    datos["centavos"] = datos["importe"].map(a_centavos)
    return datos


def a_centavos(texto):
    try:
        valor = Decimal(str(texto))
    except InvalidOperation:
        raise ValueError("Hay un importe inválido.") from None
    if not valor.is_finite() or valor * 100 != (valor * 100).to_integral_value():
        raise ValueError("Los importes deben ser finitos y tener como máximo dos decimales.")
    return int(valor * 100)


def importe_texto(centavos):
    return f"{Decimal(int(centavos)) / 100:.2f}"


def conciliar(ruta_sistema, ruta_banco, banco, apertura, cierre):
    if banco not in HORAS_CORTE or apertura >= cierre:
        raise ValueError("Selecciona un banco válido y una apertura anterior al cierre.")
    inicio = datetime.combine(apertura, time(HORAS_CORTE[banco]))
    fin = datetime.combine(cierre, time(HORAS_CORTE[banco]))
    medianoche = datetime.combine(cierre + timedelta(days=1), time())
    sistema = leer_reporte(ruta_sistema, banco)
    bancario = leer_reporte(ruta_banco, banco)
    posteriores = sistema.loc[(sistema.fecha >= fin) & (sistema.fecha < medianoche)]
    sistema = sistema.loc[(sistema.fecha >= inicio) & (sistema.fecha < fin)].copy()
    # Banco B entrega el archivo del cierre completo. Se usa sin filtro horario.
    if banco == "Banco A":
        bancario = bancario.loc[(bancario.fecha >= inicio) & (bancario.fecha < fin)].copy()
    for nombre, datos in [("sistema", sistema), ("banco", bancario)]:
        if datos.duplicated(CLAVES).any():
            raise ValueError(f"Hay claves repetidas en {nombre}; revisa antes de conciliar.")
    cruce = sistema[CLAVES + ["centavos"]].merge(
        bancario[CLAVES + ["centavos"]], on=CLAVES, how="outer",
        suffixes=("_sistema", "_banco"), indicator=True, validate="one_to_one",
    )
    cruce["diferencia_centavos"] = (
        cruce.centavos_sistema.fillna(0).astype("int64")
        - cruce.centavos_banco.fillna(0).astype("int64")
    )
    cruce["estado"] = "Conciliado"
    cruce.loc[(cruce._merge == "both") & (cruce.diferencia_centavos != 0), "estado"] = ESTADOS[1]
    cruce.loc[cruce._merge == "left_only", "estado"] = ESTADOS[2]
    cruce.loc[cruce._merge == "right_only", "estado"] = ESTADOS[3]
    for origen in ["sistema", "banco"]:
        cruce["importe_" + origen] = cruce["centavos_" + origen].map(
            lambda valor: "" if pd.isna(valor) else importe_texto(valor)
        )
    cruce["diferencia"] = cruce.diferencia_centavos.map(importe_texto)
    resultado = cruce[CLAVES + ["importe_sistema", "importe_banco", "diferencia", "estado"]]
    resumen = {estado: int((resultado.estado == estado).sum()) for estado in ESTADOS}
    resumen["total_sistema"] = importe_texto(sistema.centavos.sum())
    resumen["total_banco"] = importe_texto(bancario.centavos.sum())
    resumen["posterior_al_corte"] = importe_texto(posteriores.centavos.sum())
    return resultado, resumen

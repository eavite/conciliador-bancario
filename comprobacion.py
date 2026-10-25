"""Consulta SQL local: no se conecta a servidores ni requiere credenciales."""
from pathlib import Path
import sqlite3

import pandas as pd


def comprobar_servicios(pendientes, ruta_servicios):
    servicios = pd.read_csv(ruta_servicios, dtype=str, keep_default_na=False)
    servicios["cliente_id"] = servicios.cliente_id.str.strip().str.upper()
    servicios["referencia"] = servicios.referencia.str.strip().str.lstrip("0").replace("", "0")
    consulta = (Path(__file__).parent / "sql" / "comprobar_servicios.sql").read_text(encoding="utf-8")
    conexion = sqlite3.connect(":memory:")
    try:
        pendientes[["cliente_id", "referencia"]].drop_duplicates().to_sql("pendientes", conexion, index=False)
        servicios.to_sql("servicios_demo", conexion, index=False)
        return pd.read_sql_query(consulta, conexion)
    finally:
        conexion.close()

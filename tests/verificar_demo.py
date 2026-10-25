"""Ejecutar desde la carpeta del proyecto: python tests/verificar_demo.py."""
import hashlib
from datetime import date
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

import pandas as pd

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from app import procesar
from conciliacion import a_centavos, conciliar


def verificar():
    fuentes = list((BASE / "datos").glob("*.csv"))
    huellas = {p: hashlib.sha256(p.read_bytes()).digest() for p in fuentes}
    for banco, archivo, conteos, total, filas in [
        ("Banco A", "banco_a.csv", [3, 1, 2, 1], "40.00", 7),
        ("Banco B", "banco_b.csv", [2, 1, 1, 1], "20.00", 5),
    ]:
        argumentos = [banco, date(2030, 4, 14), date(2030, 4, 15), BASE / "datos/sistema.csv", BASE / "datos" / archivo, BASE / "datos/servicios.csv"]
        with TemporaryDirectory() as temporal:
            carpeta, resumen = procesar(*argumentos, temporal)
            assert list(resumen.values())[:4] == conteos
            assert resumen["posterior_al_corte"] == total
            resultado = pd.read_csv(carpeta / "Cuadre/conciliacion.csv", dtype=str, keep_default_na=False)
            assert len(resultado) == filas
            assert len(pd.read_csv(carpeta / "Cuadre/coincidencias_servicios.csv")) == 1
            assert len(pd.read_csv(carpeta / "Cuadre/por_revisar.csv")) == sum(conteos[1:])
            assert not resultado.duplicated(["cliente_id", "referencia"]).any()
            for numero, fuente in enumerate(argumentos[3:], start=1):
                assert (carpeta / "Reportes" / f"{numero}_{fuente.name}").read_bytes() == fuente.read_bytes()
            try:
                procesar(*argumentos, temporal)
            except FileExistsError:
                pass
            else:
                raise AssertionError("Se sobrescribió un cierre existente")
    with TemporaryDirectory() as temporal:
        sistema = pd.read_csv(BASE / "datos/sistema.csv", dtype=str)
        duplicado = pd.concat([sistema, sistema.iloc[[0]]], ignore_index=True)
        ruta = Path(temporal) / "duplicado.csv"
        duplicado.to_csv(ruta, index=False)
        try:
            conciliar(ruta, BASE / "datos/banco_a.csv", "Banco A", date(2030,4,14), date(2030,4,15))
        except ValueError as error:
            assert "repetidas" in str(error)
        else:
            raise AssertionError("Se aceptó una clave duplicada")
    for importe in ["", "NaN", "Infinity", "1.001"]:
        try:
            a_centavos(importe)
        except ValueError:
            pass
        else:
            raise AssertionError("Se aceptó un importe inválido")
    assert a_centavos("0.10") + a_centavos("0.20") == 30
    assert a_centavos("-1.25") == -125
    assert all(hashlib.sha256(p.read_bytes()).digest() == huella for p, huella in huellas.items())
    print("OK: resultados, cortes, referencias repetidas entre clientes, control de duplicados, SQL local, importes, exportación y fuentes intactas.")


if __name__ == "__main__":
    verificar()

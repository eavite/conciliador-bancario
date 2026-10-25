"""Demo pública: CSV ficticios, revisión de diferencias y exportación local."""
import argparse
from datetime import date
from pathlib import Path

from conciliacion import conciliar, HORAS_CORTE
from comprobacion import comprobar_servicios
from exportacion import exportar

BASE = Path(__file__).resolve().parent
APERTURA_DEMO = date(2030, 4, 14)
CIERRE_DEMO = date(2030, 4, 15)


def procesar(banco, apertura, cierre, sistema, bancario, servicios, destino):
    resultado, resumen = conciliar(sistema, bancario, banco, apertura, cierre)
    pendientes = resultado.loc[resultado.estado == "Solo en sistema"]
    comprobados = comprobar_servicios(pendientes, servicios)
    carpeta = exportar(resultado, resumen, comprobados, [sistema, bancario, servicios], destino, banco, cierre)
    return carpeta, resumen


def ejecutar_demo(destino):
    for banco, archivo in [("Banco A", "banco_a.csv"), ("Banco B", "banco_b.csv")]:
        carpeta, resumen = procesar(
            banco, APERTURA_DEMO, CIERRE_DEMO, BASE / "datos" / "sistema.csv",
            BASE / "datos" / archivo, BASE / "datos" / "servicios.csv", destino,
        )
        print(banco, resumen)
        print("Archivos guardados en:", carpeta)


def abrir_ventana():
    import tkinter as tk
    from tkinter import filedialog, messagebox, simpledialog
    ventana = tk.Tk()
    ventana.withdraw()
    try:
        opcion = simpledialog.askinteger("Conciliador · DEMO", "Datos ficticios. Selecciona:\n1. Banco A (corte 17:00)\n2. Banco B (corte 20:00)", minvalue=1, maxvalue=2, parent=ventana)
        if opcion is None:
            return
        banco = "Banco A" if opcion == 1 else "Banco B"
        usar_demo = messagebox.askyesnocancel("Origen de datos", "¿Usar los archivos ficticios incluidos?\nSí: demo del 14 al 15 de abril de 2030.\nNo: seleccionar CSV con el formato del ejemplo.", parent=ventana)
        if usar_demo is None:
            return
        if usar_demo:
            apertura, cierre = APERTURA_DEMO, CIERRE_DEMO
            rutas = [BASE / "datos" / "sistema.csv", BASE / "datos" / ("banco_a.csv" if opcion == 1 else "banco_b.csv"), BASE / "datos" / "servicios.csv"]
        else:
            fechas = []
            for nombre in ["apertura", "cierre"]:
                texto = simpledialog.askstring("Fecha", f"Fecha de {nombre} (AAAA-MM-DD):", parent=ventana)
                if texto is None:
                    return
                fechas.append(date.fromisoformat(texto.strip()))
            apertura, cierre = fechas
            rutas = []
            for nombre in ["sistema", "banco", "servicios ficticios"]:
                ruta = filedialog.askopenfilename(title=f"Selecciona el reporte de {nombre}", filetypes=[("CSV", "*.csv")], parent=ventana)
                if not ruta:
                    return
                rutas.append(Path(ruta))
        destino = filedialog.askdirectory(title="Carpeta para los resultados", parent=ventana)
        if not destino:
            return
        carpeta, resumen = procesar(banco, apertura, cierre, *rutas, destino)
        messagebox.showinfo("Resultado de la conciliación", f"Conciliados: {resumen['Conciliado']}\nDiferencias de importe: {resumen['Diferencia de importe']}\nSolo en sistema: {resumen['Solo en sistema']}\nSolo en banco: {resumen['Solo en banco']}\n\nPosterior al corte ({HORAS_CORTE[banco]}:00 a 23:59:59): ${resumen['posterior_al_corte']}\n\nArchivos: {carpeta}\nLas partidas pendientes requieren revisión; no se anula ningún pago.", parent=ventana)
    except (ValueError, OSError, KeyError) as error:
        messagebox.showerror("Revisa los datos", str(error), parent=ventana)
    finally:
        ventana.destroy()


if __name__ == "__main__":
    argumentos = argparse.ArgumentParser(description=__doc__)
    argumentos.add_argument("--demo", action="store_true", help="Ejecutar los dos bancos ficticios sin ventanas")
    argumentos.add_argument("--salida", type=Path, default=BASE / "salidas")
    opciones = argumentos.parse_args()
    if opciones.demo:
        ejecutar_demo(opciones.salida)
    else:
        abrir_ventana()

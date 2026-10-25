"""Vista de escritorio del ejemplo público; solo lee los CSV ficticios incluidos."""
from datetime import date
from pathlib import Path
import argparse
import tkinter as tk
from tkinter import ttk

from conciliacion import conciliar, ESTADOS, HORAS_CORTE
from comprobacion import comprobar_servicios

BASE = Path(__file__).resolve().parent


def abrir_demo(idioma="es"):
    ingles = idioma == "en"

    def texto(es, en):
        return en if ingles else es

    ventana = tk.Tk()
    ventana.title(texto("Conciliador bancario — Demostración", "Bank reconciliation — Demo"))
    ventana.geometry("1000x660+5+5")
    ventana.resizable(False, False)
    ventana.configure(bg="#f4f3f6")
    estilo = ttk.Style(ventana)
    if "vista" in estilo.theme_names():
        estilo.theme_use("vista")
    estilo.configure("Treeview", font=("Segoe UI", 11), rowheight=31)
    estilo.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
    estilo.configure("TButton", font=("Segoe UI", 10), padding=(12, 7))

    def etiqueta(padre, contenido, tamano=11, color="#272430", fondo="#f4f3f6", negrita=False):
        return tk.Label(padre, text=contenido, font=("Segoe UI", tamano, "bold" if negrita else "normal"),
                        fg=color, bg=fondo, anchor="w")

    cabecera = tk.Frame(ventana, bg="white", padx=24, pady=14)
    cabecera.pack(fill="x")
    etiqueta(cabecera, texto("Conciliación de pagos", "Payment reconciliation"), 23,
             fondo="white", negrita=True).pack(anchor="w")
    etiqueta(cabecera, texto("DEMO PÚBLICA  ·  DATOS FICTICIOS  ·  CIERRE 15 ABR 2030",
                             "PUBLIC DEMO  ·  FICTIONAL DATA  ·  CLOSING 15 APR 2030"),
             10, "#67577c", "white").pack(anchor="w", pady=(3, 0))

    cuerpo = tk.Frame(ventana, bg="#f4f3f6", padx=24, pady=12)
    cuerpo.pack(fill="both", expand=True)
    pasos = tk.Frame(cuerpo, bg="#f4f3f6")
    pasos.pack(fill="x")
    botones = []
    for numero, titulo in enumerate([
        texto("1. Comparar pagos", "1. Compare payments"),
        texto("2. Revisar diferencias", "2. Review differences"),
        texto("3. Consultar servicios", "3. Look up services"),
        texto("4. Ver Banco B", "4. View Bank B"),
    ]):
        boton = ttk.Button(pasos, text=titulo, command=lambda paso=numero: mostrar(paso))
        boton.pack(side="left", padx=(0, 10))
        botones.append(boton)

    contexto = etiqueta(cuerpo, "", 11, "#665f70")
    contexto.pack(anchor="w", pady=(12, 8))
    tarjetas = tk.Frame(cuerpo, bg="#f4f3f6")
    tarjetas.pack(fill="x")
    valores = []
    for titulo, color in [
        (texto("Pagos conciliados", "Matched payments"), "#5c358c"),
        (texto("Por revisar", "To review"), "#9a5810"),
        (texto("Total del sistema", "System total"), "#272430"),
        (texto("Después del corte", "After cutoff"), "#665f70"),
    ]:
        tarjeta = tk.Frame(tarjetas, bg="white", padx=15, pady=8, highlightthickness=1,
                           highlightbackground="#e2dfe7")
        tarjeta.pack(side="left", fill="x", expand=True, padx=(0, 8))
        valor = etiqueta(tarjeta, "", 24, color, "white", True)
        valor.pack(anchor="w")
        etiqueta(tarjeta, titulo, 10, "#665f70", "white").pack(anchor="w")
        valores.append(valor)

    titulo_tabla = etiqueta(cuerpo, "", 12, negrita=True)
    titulo_tabla.pack(anchor="w", pady=(12, 6))
    tabla = ttk.Treeview(cuerpo, show="headings", height=7, selectmode="browse")
    tabla.pack(fill="x")
    tabla.tag_configure("par", background="#f7f6fa")
    tabla.tag_configure("diferencia", background="#fff0d8", foreground="#75450d")
    tabla.tag_configure("servicio", background="#eee6f8", foreground="#51357a")
    nota = etiqueta(cuerpo, "", 11, "#5c358c")
    nota.configure(wraplength=940, justify="left")
    nota.pack(anchor="w", pady=(12, 0))
    pie = etiqueta(ventana, texto("  Archivos locales de ejemplo  |  Sin conexiones externas  |  Importes en USD",
                                 "  Local sample files  |  No external connections  |  Amounts in USD"),
                  9, "#665f70", "#eae7ee")
    pie.pack(side="bottom", fill="x", ipady=5)

    def mostrar(paso):
        banco = "Banco B" if paso == 3 else "Banco A"
        nombre_banco = banco.replace("Banco", "Bank") if ingles else banco
        resultado, resumen = conciliar(BASE / "datos/sistema.csv",
                                       BASE / ("datos/banco_b.csv" if paso == 3 else "datos/banco_a.csv"),
                                       banco, date(2030, 4, 14), date(2030, 4, 15))
        pendientes = resultado.loc[resultado.estado != ESTADOS[0]]
        contexto.configure(text=texto(
            f"{banco}  /  Cierre del 15 de abril de 2030  /  Corte del sistema: {HORAS_CORTE[banco]}:00",
            f"{nombre_banco}  /  Closing 15 April 2030  /  System cutoff: {HORAS_CORTE[banco]}:00"))
        for control, valor in zip(valores, [resumen[ESTADOS[0]], len(pendientes),
                                            "$" + resumen["total_sistema"], "$" + resumen["posterior_al_corte"]]):
            control.configure(text=str(valor))
        for numero, boton in enumerate(botones):
            boton.state(["disabled"] if numero == paso else ["!disabled"])
        tabla.delete(*tabla.get_children())
        if paso == 2:
            filas = comprobar_servicios(pendientes, BASE / "datos/servicios.csv")
            columnas = ["cliente_id", "referencia", "servicio", "importe", "seguimiento"]
            titulos = [texto("Cliente ficticio", "Fictional customer"), texto("Referencia", "Reference"),
                       texto("Servicio relacionado", "Related service"), texto("Importe", "Amount"),
                       texto("Seguimiento", "Follow-up")]
            anchos = [160, 130, 340, 140, 230]
            titulo_tabla.configure(text=texto("03  /  Una pista para investigar el pago", "03  /  A clue to investigate the payment"))
            nota.configure(text=texto("La consulta encuentra un servicio relacionado. El pago continúa pendiente de revisión.",
                                      "The lookup finds a related service. The payment remains pending review."))
            datos = [(fila.cliente_id, fila.referencia,
                      "Fictional service A" if ingles else fila.servicio, "$" + fila.importe,
                      texto("Pendiente de revisión", "Pending review")) for fila in filas.itertuples()]
        else:
            filas = pendientes if paso == 1 else resultado
            columnas = list(resultado.columns)
            titulos = [texto("Cliente ficticio", "Fictional customer"), texto("Referencia", "Reference"),
                       texto("Sistema", "System"), texto("Banco", "Bank"), texto("Diferencia", "Difference"),
                       texto("Estado", "Status")]
            anchos = [160, 120, 130, 130, 130, 330]
            titulo_tabla.configure(text=texto("02  /  Diferencias separadas para revisión" if paso == 1 else
                                              "04  /  Otro banco, el mismo proceso" if paso == 3 else
                                              "01  /  Comparación del sistema y el banco",
                                              "02  /  Differences ready for review" if paso == 1 else
                                              "04  /  Another bank, the same process" if paso == 3 else
                                              "01  /  System and bank comparison"))
            nota.configure(text=texto(
                f"{len(filas)} pagos visibles. Cada pago se cruza por cliente y referencia; las diferencias quedan a la vista.",
                f"{len(filas)} visible payments. Each payment is matched by customer and reference; differences stay visible."))
            estados_en = dict(zip(ESTADOS, ["Matched", "Amount difference", "System only", "Bank only"]))
            datos = []
            for fila in filas.itertuples(index=False, name=None):
                datos.append((*fila[:2], *("$" + valor if valor else "—" for valor in fila[2:5]),
                              estados_en[fila[5]] if ingles else fila[5]))
        tabla.configure(columns=columnas)
        for columna, titulo, ancho in zip(columnas, titulos, anchos):
            tabla.heading(columna, text=titulo, anchor="w")
            tabla.column(columna, width=ancho, stretch=True, anchor="w")
        for indice, fila in enumerate(datos):
            tag = "servicio" if paso == 2 else "diferencia" if fila[-1] in (ESTADOS[1], "Amount difference") else "par" if indice % 2 == 0 else ""
            tabla.insert("", "end", values=fila, tags=(tag,))

    mostrar(0)
    ventana.mainloop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vista del ejemplo ficticio incluido.")
    parser.add_argument("--idioma", choices=["es", "en"], default="es")
    abrir_demo(parser.parse_args().idioma)

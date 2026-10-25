# Reglas y datos de la demostración

Los cuatro CSV de `datos/` fueron escritos desde cero. `DEMO-A01` y `DEMO-B01` son identificadores inventados; no proceden de clientes reales ni son seudónimos de personas.

## Entrada

Los reportes de sistema y banco tienen cinco columnas:

| Columna | Ejemplo ficticio | Uso |
|---|---|---|
| banco | Banco A | Seleccionar la entidad. |
| cliente_id | DEMO-A01 | Distinguir clientes de la muestra. |
| referencia | 000101 | Identificar el pago junto con el cliente. |
| fecha | 2030-04-15 10:00:00 | Aplicar el cierre local. |
| importe | 100.00 | Comparar valores en USD. |

Los ceros iniciales de la referencia se normalizan. No se convierte el identificador de cliente a número. Los importes se validan y se calculan en centavos enteros.

## Horarios

Banco A: desde las 17:00 del día de apertura hasta antes de las 17:00 del cierre. El total posterior toma las 17:00 del cierre hasta antes de la medianoche siguiente.

Banco B: desde las 20:00 del día de apertura hasta antes de las 20:00 del cierre para el sistema. Su archivo bancario se utiliza completo porque representa el cierre seleccionado. El total posterior toma las 20:00 del cierre hasta antes de la medianoche siguiente.

La muestra incluye filas inmediatamente antes de la apertura, en el corte y en la medianoche siguiente para comprobar estos límites.

## Casos incluidos en el ejemplo

1. `DEMO-A03`: el sistema registra 80 y el banco 75. La diferencia es 5 y la fila queda para revisión.
2. `DEMO-A01` y `DEMO-A06` comparten la referencia 101. Al usar también el cliente, cada pago se cruza una sola vez.
3. `DEMO-A04` aparece solo en el sistema y tiene un servicio ficticio asociado. La consulta lo identifica, pero no lo elimina de los pendientes.
4. `DEMO-A07` ocurre a las 17:00 del cierre. Queda fuera del cuadre y dentro del total posterior.

La diferencia se calcula como sistema menos banco. Una casilla vacía significa ausencia en esa fuente; el cero solo se utiliza para calcular la diferencia. La suma neta puede ocultar diferencias que se compensan: la revisión se hace por fila y estado.

## Recorrido del código

`app.py` recoge la selección y llama a `procesar`. Esa función concilia, consulta los pendientes y exporta, en ese orden.

`leer_reporte` comprueba las columnas, selecciona el banco, limpia las claves y valida fechas e importes. `conciliar` separa el período y los pagos posteriores, rechaza claves repetidas y realiza un cruce completo para conservar ambas fuentes. El estado explica por qué cada fila coincide o necesita revisión.

`comprobar_servicios` crea dos tablas temporales en una base SQLite en memoria, ejecuta la consulta genérica y cierra la conexión en `finally`. No utiliza red ni credenciales.

`exportar` comprueba que el destino no exista, crea las carpetas, guarda los resultados y finalmente copia las fuentes. `shutil.copy2` copia los archivos; no los mueve.

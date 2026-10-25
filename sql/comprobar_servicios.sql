-- Tablas y campos ficticios. Una coincidencia es una pista para revisar.
SELECT p.cliente_id, p.referencia, s.servicio, s.importe
FROM pendientes AS p
INNER JOIN servicios_demo AS s
    ON p.cliente_id = s.cliente_id
    AND p.referencia = s.referencia
ORDER BY p.cliente_id, p.referencia;

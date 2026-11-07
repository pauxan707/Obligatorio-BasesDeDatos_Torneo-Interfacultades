
USE torneo_f5;

CREATE OR REPLACE VIEW v_resultado_partido AS
SELECT p.id_torneo,
       p.id_partido,
       p.numero_fecha,
       p.id_equipo_local,
       p.id_equipo_visitante,
       COALESCE(SUM(CASE
                 WHEN (g.autogol = 0 AND pl.id_equipo = p.id_equipo_local)
                   OR (g.autogol = 1 AND pl.id_equipo = p.id_equipo_visitante)
                 THEN 1 ELSE 0 END), 0) AS goles_local,
       COALESCE(SUM(CASE
                 WHEN (g.autogol = 0 AND pl.id_equipo = p.id_equipo_visitante)
                   OR (g.autogol = 1 AND pl.id_equipo = p.id_equipo_local)
                 THEN 1 ELSE 0 END), 0) AS goles_visitante
  FROM partido p
  LEFT JOIN gol g
         ON g.id_partido = p.id_partido
  LEFT JOIN planilla_partido pl
         ON pl.id_partido = g.id_partido
        AND pl.ci_jugador = g.ci_jugador
 WHERE p.estado = 'jugado'
 GROUP BY p.id_torneo, p.id_partido, p.numero_fecha,
          p.id_equipo_local, p.id_equipo_visitante;

CREATE OR REPLACE VIEW v_posiciones AS
WITH a_favor AS (
    SELECT id_torneo, id_partido, id_equipo_local  AS id_equipo,
           goles_local      AS gf, goles_visitante AS gc
      FROM v_resultado_partido
    UNION ALL
    SELECT id_torneo, id_partido, id_equipo_visitante AS id_equipo,
           goles_visitante AS gf, goles_local         AS gc
      FROM v_resultado_partido
)
SELECT e.id_torneo,
       e.id_equipo,
       e.nombre AS equipo,
       COUNT(a.id_partido)                    AS pj,
       COALESCE(SUM(a.gf > a.gc), 0)          AS pg,
       COALESCE(SUM(a.gf = a.gc), 0)          AS pe,
       COALESCE(SUM(a.gf < a.gc), 0)          AS perdidos,
       COALESCE(SUM(a.gf), 0)                 AS gf,
       COALESCE(SUM(a.gc), 0)                 AS gc,
       COALESCE(SUM(a.gf) - SUM(a.gc), 0)     AS dg,
       3 * COALESCE(SUM(a.gf > a.gc), 0)
           + COALESCE(SUM(a.gf = a.gc), 0)    AS puntos
  FROM equipo e
  LEFT JOIN a_favor a
         ON a.id_equipo = e.id_equipo
        AND a.id_torneo = e.id_torneo
 GROUP BY e.id_torneo, e.id_equipo, e.nombre;

CREATE OR REPLACE VIEW v_goleadores AS
SELECT p.id_torneo,
       j.ci,
       j.nombre,
       j.apellido,
       f.nombre AS facultad,
       e.nombre AS equipo,
       COUNT(*) AS goles
  FROM gol g
  JOIN partido p           ON p.id_partido = g.id_partido
  JOIN planilla_partido pl ON pl.id_partido = g.id_partido
                          AND pl.ci_jugador = g.ci_jugador
  JOIN jugador j           ON j.ci  = g.ci_jugador
  JOIN facultad f          ON f.id_facultad = j.id_facultad
  JOIN equipo e            ON e.id_equipo = pl.id_equipo
 WHERE g.autogol = 0
 GROUP BY p.id_torneo, j.ci, j.nombre, j.apellido, f.nombre, e.nombre;

CREATE OR REPLACE VIEW v_fair_play AS
SELECT e.id_torneo,
       e.id_equipo,
       e.nombre AS equipo,
       COALESCE(SUM(t.color = 'amarilla'), 0) AS amarillas,
       COALESCE(SUM(t.color = 'roja'), 0)     AS rojas,
       COALESCE(SUM(t.color = 'amarilla'), 0)
         + 3 * COALESCE(SUM(t.color = 'roja'), 0) AS puntos_fair_play
  FROM equipo e
  LEFT JOIN planilla_partido pl
         ON pl.id_equipo = e.id_equipo
        AND pl.id_torneo = e.id_torneo
  LEFT JOIN tarjeta t
         ON t.id_partido = pl.id_partido
        AND t.ci_jugador = pl.ci_jugador
 GROUP BY e.id_torneo, e.id_equipo, e.nombre;

CREATE OR REPLACE VIEW v_promedio_goles AS
WITH goles_partido AS (
    SELECT p.id_torneo,
           p.numero_fecha,
           p.id_partido,
           COUNT(g.id_gol) AS goles
      FROM partido p
      LEFT JOIN gol g ON g.id_partido = p.id_partido
     WHERE p.estado = 'jugado'
     GROUP BY p.id_torneo, p.numero_fecha, p.id_partido
)
SELECT id_torneo,
       numero_fecha AS fecha,
       'fecha'      AS alcance,
       COUNT(*)     AS partidos,
       SUM(goles)   AS goles,
       ROUND(SUM(goles) / COUNT(*), 2) AS promedio_goles
  FROM goles_partido
 GROUP BY id_torneo, numero_fecha
UNION ALL
SELECT id_torneo,
       NULL,
       'edicion',
       COUNT(*),
       SUM(goles),
       ROUND(SUM(goles) / COUNT(*), 2)
  FROM goles_partido
 GROUP BY id_torneo;

CREATE OR REPLACE VIEW v_canchas_turnos AS
SELECT p.id_torneo,
       'cancha' AS tipo,
       p.nombre_cancha AS concepto,
       c.nombre AS detalle,
       COUNT(*) AS partidos
  FROM partido p
  JOIN complejo c ON c.id_complejo = p.id_complejo
 WHERE p.estado <> 'cancelado'
 GROUP BY p.id_torneo, p.nombre_cancha, c.nombre
UNION ALL
SELECT p.id_torneo,
       'turno' AS tipo,
       CONCAT(t.hora_inicio, ' a ', t.hora_fin) AS concepto,
       CONCAT('Turno ', t.id_turno) AS detalle,
       COUNT(*) AS partidos
  FROM partido p
  JOIN turno t ON t.id_turno = p.id_turno
 WHERE p.estado <> 'cancelado'
 GROUP BY p.id_torneo, t.id_turno, t.hora_inicio, t.hora_fin;

CREATE OR REPLACE VIEW v_jugadores_facultad AS
SELECT f.id_facultad,
       f.nombre AS facultad,
       j.tipo,
       COUNT(j.ci) AS jugadores
  FROM facultad f
  LEFT JOIN jugador j ON j.id_facultad = f.id_facultad
 GROUP BY f.id_facultad, f.nombre, j.tipo;

CREATE OR REPLACE VIEW v_jugadores_sin_planilla AS
SELECT ejt.id_torneo,
       ejt.id_equipo,
       e.nombre AS equipo,
       ejt.numero_camiseta,
       j.ci,
       j.nombre,
       j.apellido,
       j.tipo,
       f.nombre AS facultad
  FROM equipo_jugador_torneo ejt
  JOIN equipo e    ON e.id_equipo = ejt.id_equipo
  JOIN jugador j   ON j.ci = ejt.ci_jugador
  JOIN facultad f  ON f.id_facultad = j.id_facultad
 WHERE NOT EXISTS (
        SELECT 1 FROM planilla_partido pl
         WHERE pl.ci_jugador = ejt.ci_jugador
           AND pl.id_torneo  = ejt.id_torneo
       );

CREATE OR REPLACE VIEW v_sanciones_equipo AS
SELECT s.id_torneo,
       ejt.id_equipo,
       e.nombre AS equipo,
       s.motivo,
       COUNT(*) AS sanciones,
       SUM(s.cantidad_fechas) AS fechas_sancionadas
  FROM sancion_jugador s
  JOIN equipo_jugador_torneo ejt
       ON ejt.ci_jugador = s.ci_jugador
      AND ejt.id_torneo  = s.id_torneo
  JOIN equipo e
       ON e.id_equipo = ejt.id_equipo
      AND e.id_torneo = ejt.id_torneo
 GROUP BY s.id_torneo, ejt.id_equipo, e.nombre, s.motivo;

CREATE OR REPLACE VIEW v_porcentaje_partidos AS
SELECT x.id_torneo,
       x.estado,
       x.cantidad,
       ROUND(100.0 * x.cantidad / t.total, 1) AS porcentaje
  FROM ( SELECT id_torneo, estado, COUNT(*) AS cantidad
           FROM partido
          GROUP BY id_torneo, estado ) x
  JOIN ( SELECT id_torneo, COUNT(*) AS total
           FROM partido
          GROUP BY id_torneo ) t
    ON t.id_torneo = x.id_torneo;

--extra 1: cuántos partidos terminó cada equipo sin recibir ningún gol 
CREATE OR REPLACE VIEW v_vallas_invictas AS
SELECT e.id_torneo,
       e.id_equipo,
       e.nombre AS equipo,
       COUNT(r.id_partido) AS pj,
       SUM(CASE
             WHEN r.id_equipo_local = e.id_equipo AND r.goles_visitante = 0 THEN 1
             WHEN r.id_equipo_visitante = e.id_equipo AND r.goles_local = 0 THEN 1
             ELSE 0
           END) AS vallas_invictas
  FROM equipo e
  LEFT JOIN v_resultado_partido r
         ON e.id_equipo IN (r.id_equipo_local, r.id_equipo_visitante)
 GROUP BY e.id_torneo, e.id_equipo, e.nombre;


--extra 2: tarjetas de cada jugador, para poder ver quiénes tienen más en cada facultad

CREATE OR REPLACE VIEW v_tarjetas_facultad AS
SELECT p.id_torneo,
       f.id_facultad,
       f.nombre AS facultad,
       j.ci,
       j.nombre,
       j.apellido,
       SUM(t.color = 'amarilla') AS amarillas,
       SUM(t.color = 'roja')     AS rojas,
       COUNT(*)                  AS tarjetas
  FROM tarjeta t
  JOIN partido p  ON p.id_partido = t.id_partido
  JOIN jugador j  ON j.ci = t.ci_jugador
  JOIN facultad f ON f.id_facultad = j.id_facultad
 GROUP BY p.id_torneo, f.id_facultad, f.nombre, j.ci, j.nombre, j.apellido;

CREATE OR REPLACE VIEW v_ocupacion_complejo AS
SELECT p.id_torneo,
       p.id_complejo,
       c.nombre AS complejo,
       p.dia,
       COUNT(*) AS partidos,
       COUNT(DISTINCT p.id_turno)        AS turnos_ocupados,
       COUNT(DISTINCT p.nombre_cancha)   AS canchas_usadas
  FROM partido p
  JOIN complejo c ON c.id_complejo = p.id_complejo
 WHERE p.estado <> 'cancelado'
 GROUP BY p.id_torneo, p.id_complejo, c.nombre, p.dia;

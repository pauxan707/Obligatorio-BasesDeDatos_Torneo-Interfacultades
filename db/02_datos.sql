USE torneo_f5;
SET NAMES utf8mb4;

-- Facultades
INSERT INTO facultad (id_facultad, nombre) VALUES
(1, 'Derecho'),
(2, 'Ingeniería'),
(3, 'Medicina'),
(4, 'Ciencias Económicas'),
(5, 'Psicología'),
(6, 'Comunicación');

-- Jugadores

INSERT INTO jugador (ci, nombre, apellido, email, fecha_nacimiento, id_facultad, tipo) VALUES
('10000001', 'Santiago',  'Pérez',      'santiago.perez@ucu.edu.uy',      '2003-04-12', 1, 'grado'),
('10000002', 'Valentina', 'Rodríguez',  'valentina.rodriguez@ucu.edu.uy', '2002-11-03', 1, 'grado'),
('10000003', 'Mateo',     'Fernández',  'mateo.fernandez@ucu.edu.uy',     '2004-01-25', 1, 'grado'),
('10000004', 'Agustina',  'Lopez',      'agustina.lopez@ucu.edu.uy',      '2003-07-19', 1, 'grado'),
('10000005', 'Nicolas',   'Martinez',   'nicolas.martinez@ucu.edu.uy',    '2002-09-08', 1, 'grado'),
('10000006', 'Camila',    'González',   'camila.gonzalez@ucu.edu.uy',     '2004-03-30', 1, 'grado'),
('10000007', 'Joaquin',   'Silva',      'joaquin.silva@ucu.edu.uy',       '1995-06-14', 1, 'posgrado'),
('10000008', 'Lucia',     'Ramirez',    'lucia.ramirez@ucu.edu.uy',       '1985-12-02', 1, 'docente'),
('10000009', 'Bruno',     'Castro',     'bruno.castro@ucu.edu.uy',        '2003-05-16', 2, 'grado'),
('10000010', 'Martina',   'Díaz',       'martina.diaz@ucu.edu.uy',        '2002-08-21', 2, 'grado'),
('10000011', 'Facundo',   'Romero',     'facundo.romero@ucu.edu.uy',      '2004-02-11', 2, 'grado'),
('10000012', 'Sofía',     'Herrera',    'sofia.herrera@ucu.edu.uy',       '2003-10-05', 2, 'grado'),
('10000013', 'Tomás',     'Vázquez',    'tomas.vazquez@ucu.edu.uy',       '2002-12-27', 2, 'grado'),
('10000014', 'Julieta',   'Morales',    'julieta.morales@ucu.edu.uy',     '2004-06-09', 2, 'grado'),
('10000015', 'Gonzalo',   'Ortiz',      'gonzalo.ortiz@ucu.edu.uy',       '1994-03-18', 2, 'posgrado'),
('10000016', 'Andrea',    'Suárez',     'andrea.suarez@ucu.edu.uy',       '1987-07-07', 2, 'funcionario'),
('10000017', 'Diego',     'Acosta',     'diego.acosta@ucu.edu.uy',        '2003-01-14', 3, 'grado'),
('10000018', 'Paula',     'Benítez',    'paula.benitez@ucu.edu.uy',       '2002-04-26', 3, 'grado'),
('10000019', 'Lucas',     'Cabrera',    'lucas.cabrera@ucu.edu.uy',       '2004-09-02', 3, 'grado'),
('10000020', 'Florencia', 'Núñez',      'florencia.nunez@ucu.edu.uy',     '2003-11-23', 3, 'grado'),
('10000021', 'Martín',    'Iglesias',   'martin.iglesias@ucu.edu.uy',     '2002-06-30', 3, 'grado'),
('10000022', 'Celeste',   'Pereira',    'celeste.pereira@ucu.edu.uy',     '2004-08-17', 3, 'grado'),
('10000023', 'Rodrigo',   'Fagúndez',   'rodrigo.fagundez@ucu.edu.uy',    '1996-02-08', 3, 'posgrado'),
('10000024', 'Gabriela',  'Techera',    'gabriela.techera@ucu.edu.uy',    '1983-10-29', 3, 'docente'),
('10000025', 'Emiliano',  'Sosa',       'emiliano.sosa@ucu.edu.uy',       '2003-03-07', 4, 'grado'),
('10000026', 'Rocío',     'Medina',     'rocio.medina@ucu.edu.uy',        '2002-07-12', 4, 'grado'),
('10000027', 'Leandro',   'Correa',     'leandro.correa@ucu.edu.uy',      '2004-05-24', 4, 'grado'),
('10000028', 'Mariana',   'Rojas',      'mariana.rojas@ucu.edu.uy',       '2003-09-15', 4, 'grado'),
('10000029', 'Sebastián', 'Prieto',     'sebastian.prieto@ucu.edu.uy',    '2002-11-28', 4, 'grado'),
('10000030', 'Antonella', 'Ferreyra',   'antonella.ferreyra@ucu.edu.uy',  '2004-04-04', 4, 'grado'),
('10000031', 'Federico',  'Bentancor',  'federico.bentancor@ucu.edu.uy',  '1993-08-20', 4, 'posgrado'),
('10000032', 'Verónica',  'Larrañaga',  'veronica.larranaga@ucu.edu.uy',  '1986-01-31', 4, 'funcionario'),
('10000033', 'Joaquín',   'Olivera',    'joaquin.olivera@ucu.edu.uy',     '2003-06-11', 5, 'grado'),
('10000034', 'Micaela',   'Duarte',     'micaela.duarte@ucu.edu.uy',      '2002-10-19', 5, 'grado'),
('10000035', 'Santiago',  'Almeida',    'santiago.almeida@ucu.edu.uy',    '2004-07-01', 5, 'grado'),
('10000036', 'Valentina', 'Correa',     'valentina.correa@ucu.edu.uy',    '2003-12-08', 5, 'grado'),
('10000037', 'Bruno',     'Salgado',    'bruno.salgado@ucu.edu.uy',       '2002-02-22', 5, 'grado'),
('10000038', 'Agustina',  'Cardozo',    'agustina.cardozo@ucu.edu.uy',    '2004-11-13', 5, 'grado'),
('10000039', 'Nicolás',   'Barrios',    'nicolas.barrios@ucu.edu.uy',     '1995-05-27', 5, 'posgrado'),
('10000040', 'Lucía',     'Machado',    'lucia.machado@ucu.edu.uy',       '1984-09-06', 5, 'docente'),
('10000041', 'Mateo',     'Ribeiro',    'mateo.ribeiro@ucu.edu.uy',       '2003-08-03', 6, 'grado'),
('10000042', 'Camila',    'Píriz',      'camila.piriz@ucu.edu.uy',        '2002-03-16', 6, 'grado'),
('10000043', 'Facundo',   'Echeverría', 'facundo.echeverria@ucu.edu.uy',  '2004-10-21', 6, 'grado'),
('10000044', 'Sofía',     'Cabrera',    'sofia.cabrera@ucu.edu.uy',       '2003-01-09', 6, 'grado'),
('10000045', 'Tomás',     'Olivera',    'tomas.olivera@ucu.edu.uy',       '2002-05-31', 6, 'grado'),
('10000046', 'Julieta',   'Núñez',      'julieta.nunez@ucu.edu.uy',       '2004-12-04', 6, 'grado'),
('10000047', 'Gonzalo',   'Viera',      'gonzalo.viera@ucu.edu.uy',       '1994-07-25', 6, 'posgrado'),
('10000048', 'Andrea',    'Techera',    'andrea.techera@ucu.edu.uy',      '1988-02-17', 6, 'funcionario');

-- Torneo
INSERT INTO torneo (id_torneo, nombre, anio, semestre, fecha_inicio, fecha_fin, estado) VALUES
(1, 'Torneo Interfacultades de Fútbol 5', 2026, 2, '2026-08-01', '2026-11-30', 'en_curso');

-- Equipos
INSERT INTO equipo (id_equipo, nombre, id_torneo, id_facultad, ci_capitan) VALUES
(1, 'Derecho FC',       1, 1, '10000001'),
(2, 'Ingeniería FC',    1, 2, '10000009'),
(3, 'Medicina FC',      1, 3, '10000017'),
(4, 'Económicas FC',    1, 4, '10000025'),
(5, 'Psicología FC',    1, 5, '10000033'),
(6, 'Comunicación FC',  1, 6, '10000041');

-- Planteles (8 jugadores por equipo)
INSERT INTO equipo_jugador_torneo (id_equipo, ci_jugador, id_torneo, numero_camiseta) VALUES
(1, '10000001', 1, 1), (1, '10000002', 1, 2), (1, '10000003', 1, 3), (1, '10000004', 1, 4),
(1, '10000005', 1, 5), (1, '10000006', 1, 6), (1, '10000007', 1, 7), (1, '10000008', 1, 8),
(2, '10000009', 1, 1), (2, '10000010', 1, 2), (2, '10000011', 1, 3), (2, '10000012', 1, 4),
(2, '10000013', 1, 5), (2, '10000014', 1, 6), (2, '10000015', 1, 7), (2, '10000016', 1, 8),
(3, '10000017', 1, 1), (3, '10000018', 1, 2), (3, '10000019', 1, 3), (3, '10000020', 1, 4),
(3, '10000021', 1, 5), (3, '10000022', 1, 6), (3, '10000023', 1, 7), (3, '10000024', 1, 8),
(4, '10000025', 1, 1), (4, '10000026', 1, 2), (4, '10000027', 1, 3), (4, '10000028', 1, 4),
(4, '10000029', 1, 5), (4, '10000030', 1, 6), (4, '10000031', 1, 7), (4, '10000032', 1, 8),
(5, '10000033', 1, 1), (5, '10000034', 1, 2), (5, '10000035', 1, 3), (5, '10000036', 1, 4),
(5, '10000037', 1, 5), (5, '10000038', 1, 6), (5, '10000039', 1, 7), (5, '10000040', 1, 8),
(6, '10000041', 1, 1), (6, '10000042', 1, 2), (6, '10000043', 1, 3), (6, '10000044', 1, 4),
(6, '10000045', 1, 5), (6, '10000046', 1, 6), (6, '10000047', 1, 7), (6, '10000048', 1, 8);

-- Complejos y canchas
INSERT INTO complejo (id_complejo, nombre, direccion, departamento) VALUES
(1, 'Complejo UCU Centro',  'Av. 8 de Octubre 2738', 'Montevideo'),
(2, 'Complejo UCU Pocitos', 'Av. Brasil 2840',       'Montevideo');

INSERT INTO cancha (nombre_cancha, id_complejo, superficie, techada) VALUES
('Cancha 1', 1, 'sintetico', TRUE),
('Cancha 2', 1, 'sintetico', FALSE),
('Cancha 1', 2, 'parquet',   TRUE);

-- Partidos
INSERT INTO partido (id_partido, id_torneo, numero_fecha, id_equipo_local, id_equipo_visitante, dia, id_turno, nombre_cancha, id_complejo, estado) VALUES
(1,  1, 1, 1, 6, '2026-09-12', 1, 'Cancha 1', 1, 'jugado'),
(2,  1, 1, 2, 5, '2026-09-12', 2, 'Cancha 2', 1, 'jugado'),
(3,  1, 1, 3, 4, '2026-09-12', 3, 'Cancha 1', 2, 'jugado'),
(4,  1, 2, 1, 5, '2026-09-19', 1, 'Cancha 1', 1, 'jugado'),
(5,  1, 2, 6, 4, '2026-09-19', 2, 'Cancha 1', 1, 'jugado'),
(6,  1, 2, 2, 3, '2026-09-19', 3, 'Cancha 1', 2, 'jugado'),
(7,  1, 3, 1, 4, '2026-09-26', 1, 'Cancha 1', 1, 'jugado'),
(8,  1, 3, 5, 3, '2026-09-26', 2, 'Cancha 2', 1, 'jugado'),
(9,  1, 3, 6, 2, '2026-09-26', 3, 'Cancha 1', 2, 'jugado'),
(10, 1, 4, 1, 3, '2026-10-03', 1, 'Cancha 1', 1, 'postergado'),
(11, 1, 4, 4, 2, '2026-10-03', 2, 'Cancha 1', 1, 'programado'),
(12, 1, 4, 5, 6, '2026-10-03', 3, 'Cancha 1', 2, 'programado'),
(13, 1, 5, 1, 2, '2026-10-10', 1, 'Cancha 1', 1, 'cancelado'),
(14, 1, 5, 3, 6, '2026-10-10', 2, 'Cancha 2', 1, 'programado'),
(15, 1, 5, 4, 5, '2026-10-10', 3, 'Cancha 1', 2, 'programado');


-- Planillas de los partidos jugados
INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo, id_torneo)
SELECT p.id_partido, ejt.ci_jugador, ejt.id_equipo, p.id_torneo
FROM partido p
JOIN equipo_jugador_torneo ejt
  ON ejt.id_torneo = p.id_torneo
 AND ejt.id_equipo IN (p.id_equipo_local, p.id_equipo_visitante)
 AND ejt.numero_camiseta <= 6
WHERE p.estado = 'jugado'
ORDER BY p.id_partido, ejt.id_equipo, ejt.numero_camiseta;

-- Goles
INSERT INTO gol (id_gol, id_partido, ci_jugador, minuto, autogol) VALUES
(1,  1, '10000004', 23, 0),
(2,  2, '10000012', 10, 0),
(3,  2, '10000013', 40, 0),
(4,  2, '10000036', 15, 0),
(5,  2, '10000037', 55, 0),
(6,  3, '10000020',  5, 0),
(7,  3, '10000021', 30, 0),
(8,  3, '10000022', 50, 0),
(9,  3, '10000028', 20, 0),
(10, 4, '10000036', 12, 0),
(11, 4, '10000038', 45, 0),
(12, 5, '10000044', 33, 0),
(13, 5, '10000045', 22, 1),
(14, 6, '10000012', 18, 0),
(15, 7, '10000004', 10, 0),
(16, 7, '10000005', 44, 0),
(17, 7, '10000029', 38, 0),
(18, 8, '10000037', 25, 0),
(19, 8, '10000020',  8, 0),
(20, 8, '10000021', 19, 0),
(21, 8, '10000022', 57, 0),
(22, 9, '10000013', 14, 0),
(23, 9, '10000014', 49, 0);

-- Tarjetas
INSERT INTO tarjeta (id_tarjeta, id_partido, ci_jugador, minuto, color) VALUES
(1,  1, '10000046', 30, 'amarilla'),
(2,  2, '10000010', 25, 'amarilla'),
(3,  2, '10000035', 50, 'amarilla'),
(4,  3, '10000018', 12, 'amarilla'),
(5,  3, '10000030', 44, 'amarilla'),
(6,  4, '10000002', 20, 'amarilla'),
(7,  4, '10000035', 35, 'amarilla'),
(8,  5, '10000043', 18, 'amarilla'),
(9,  5, '10000027', 28, 'amarilla'),
(10, 6, '10000011', 22, 'amarilla'),
(11, 6, '10000019', 55, 'amarilla'),
(12, 7, '10000003', 15, 'amarilla'),
(13, 7, '10000026', 41, 'amarilla'),
(14, 8, '10000033',  9, 'amarilla'),
(15, 8, '10000035', 33, 'amarilla'), 
(16, 8, '10000037', 58, 'roja'),
(17, 9, '10000042', 11, 'amarilla'),
(18, 9, '10000014', 27, 'amarilla');

-- Sanciones
INSERT INTO sancion_jugador (id_sancion, ci_jugador, id_torneo, motivo, numero_fecha_inicio, cantidad_fechas, id_tarjeta) VALUES
(1, '10000035', 1, 'acumulacion_amarillas', 4, 1, 15),
(2, '10000037', 1, 'roja',                   4, 1, 16),
(3, '10000028', 1, 'disciplinaria',          4, 2, NULL),
(4, '10000004', 1, 'disciplinaria',          5, 1, NULL);

-- Segunda edición, todavía en inscripción
-- Sirve para probar el CRUD de planteles, que solo se puede usar en esta etapa
INSERT INTO torneo (id_torneo, nombre, anio, semestre, fecha_inicio, fecha_fin, estado) VALUES
(2, 'Torneo Interfacultades de Fútbol 5', 2027, 1, '2027-03-01', '2027-06-30', 'inscripcion');

INSERT INTO equipo (id_equipo, nombre, id_torneo, id_facultad, ci_capitan) VALUES
(7, 'Derecho FC',     2, 1, '10000001'),
(8, 'Ingeniería FC',  2, 2, '10000009'),
(9, 'Medicina FC',    2, 3, '10000017');

INSERT INTO equipo_jugador_torneo (id_equipo, ci_jugador, id_torneo, numero_camiseta) VALUES
(7, '10000001', 2, 1), (7, '10000002', 2, 2), (7, '10000003', 2, 3), (7, '10000004', 2, 4), (7, '10000005', 2, 5),
(8, '10000009', 2, 1), (8, '10000010', 2, 2), (8, '10000011', 2, 3), (8, '10000012', 2, 4), (8, '10000013', 2, 5),
(9, '10000017', 2, 1), (9, '10000018', 2, 2), (9, '10000019', 2, 3), (9, '10000020', 2, 4), (9, '10000021', 2, 5);

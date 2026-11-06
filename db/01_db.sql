CREATE DATABASE IF NOT EXISTS torneo_f5;
USE torneo_f5;


CREATE TABLE login (
    correo VARCHAR(100) PRIMARY KEY,
    contrasena VARCHAR(255) NOT NULL,
    rol ENUM ('administrador','planillero') NOT NULL
);

CREATE TABLE facultad (
    id_facultad INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE jugador (
    ci VARCHAR(8)  PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    apellido VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    fecha_nacimiento DATE NOT NULL,
    id_facultad INT NOT NULL,
    tipo ENUM('grado','posgrado','docente','funcionario') NOT NULL,
    CONSTRAINT fk_jugador_facultad FOREIGN KEY (id_facultad) REFERENCES facultad(id_facultad)
);

CREATE TABLE torneo (
    id_torneo    INT AUTO_INCREMENT PRIMARY KEY,
    nombre       VARCHAR(100) NOT NULL,
    anio         SMALLINT NOT NULL,
    semestre     TINYINT  NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin    DATE NOT NULL,
    estado ENUM('inscripcion','en_curso','finalizado') NOT NULL DEFAULT 'inscripcion',
    UNIQUE KEY uk_torneo_anio_semestre (anio, semestre)
);

CREATE TABLE equipo (
    id_equipo   INT AUTO_INCREMENT PRIMARY KEY,
    nombre      VARCHAR(60) NOT NULL,
    id_torneo   INT NOT NULL,
    id_facultad INT NOT NULL,
    ci_capitan  VARCHAR(8) NULL,
    UNIQUE KEY uk_equipo_nombre    (id_torneo, nombre),
    UNIQUE KEY uk_equipo_id_torneo (id_equipo, id_torneo),
    CONSTRAINT fk_equipo_torneo   FOREIGN KEY (id_torneo)   REFERENCES torneo(id_torneo),
    CONSTRAINT fk_equipo_facultad FOREIGN KEY (id_facultad) REFERENCES facultad(id_facultad),
    CONSTRAINT fk_equipo_jugador  FOREIGN KEY (ci_capitan)  REFERENCES jugador(ci)
);

CREATE TABLE equipo_jugador_torneo (
    id_equipo       INT NOT NULL,
    ci_jugador      VARCHAR(8) NOT NULL,
    id_torneo       INT NOT NULL,
    numero_camiseta TINYINT UNSIGNED NOT NULL,
    PRIMARY KEY (id_equipo, ci_jugador, id_torneo),
    UNIQUE KEY uk_ejt_jugador  (id_torneo, ci_jugador),
    UNIQUE KEY uk_ejt_camiseta (id_equipo, numero_camiseta),
    CONSTRAINT fk_ejt_equipo  FOREIGN KEY (id_equipo, id_torneo) REFERENCES equipo(id_equipo, id_torneo),
    CONSTRAINT fk_ejt_jugador FOREIGN KEY (ci_jugador) REFERENCES jugador(ci)
);

CREATE TABLE complejo (
    id_complejo  INT AUTO_INCREMENT PRIMARY KEY,
    nombre       VARCHAR(100) NOT NULL UNIQUE,
    direccion    VARCHAR(150) NOT NULL,
    departamento VARCHAR(50)  NOT NULL
);

CREATE TABLE cancha (
    nombre_cancha VARCHAR(50) NOT NULL,
    id_complejo   INT NOT NULL,
    superficie    ENUM('sintetico','parquet') NOT NULL,
    techada       BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (nombre_cancha, id_complejo),
    CONSTRAINT fk_cancha_complejo FOREIGN KEY (id_complejo) REFERENCES complejo(id_complejo)
);

CREATE TABLE turno (
    id_turno    TINYINT PRIMARY KEY,
    hora_inicio TIME NOT NULL UNIQUE,
    hora_fin    TIME NOT NULL,
    CONSTRAINT chk_turno_horas CHECK (hora_fin > hora_inicio AND hora_inicio >= '18:00:00' AND hora_fin <= '23:00:00')
);

CREATE TABLE partido (
    id_partido          INT AUTO_INCREMENT PRIMARY KEY,
    id_torneo           INT NOT NULL,
    numero_fecha        TINYINT UNSIGNED NOT NULL,
    id_equipo_local     INT NOT NULL,
    id_equipo_visitante INT NOT NULL,
    dia                 DATE NOT NULL,
    id_turno            TINYINT NOT NULL,
    nombre_cancha       VARCHAR(50) NOT NULL,
    id_complejo         INT NOT NULL,
    estado              ENUM('programado','jugado','postergado','cancelado') NOT NULL DEFAULT 'programado',
    CONSTRAINT fk_partido_local     FOREIGN KEY (id_equipo_local, id_torneo)     REFERENCES equipo(id_equipo, id_torneo),
    CONSTRAINT fk_partido_visitante FOREIGN KEY (id_equipo_visitante, id_torneo) REFERENCES equipo(id_equipo, id_torneo),
    CONSTRAINT fk_partido_turno     FOREIGN KEY (id_turno) REFERENCES turno(id_turno),
    CONSTRAINT fk_partido_cancha    FOREIGN KEY (nombre_cancha, id_complejo) REFERENCES cancha(nombre_cancha, id_complejo),
    CONSTRAINT chk_partido_equipos CHECK (id_equipo_local <> id_equipo_visitante),
    CONSTRAINT chk_partido_fecha   CHECK (numero_fecha >= 1),
    KEY idx_partido_torneo_fecha (id_torneo, numero_fecha),
    KEY idx_partido_cancha_dia (dia, id_turno, nombre_cancha, id_complejo),
    UNIQUE KEY uk_partido_id_torneo (id_partido, id_torneo)
);

CREATE TABLE planilla_partido (
    id_partido INT NOT NULL,
    ci_jugador VARCHAR(8) NOT NULL,
    id_equipo  INT NOT NULL,
    id_torneo  INT NOT NULL,
    PRIMARY KEY (id_partido, ci_jugador),
    CONSTRAINT fk_planilla_ejt FOREIGN KEY (id_equipo, ci_jugador, id_torneo)
        REFERENCES equipo_jugador_torneo(id_equipo, ci_jugador, id_torneo),
    CONSTRAINT fk_planilla_partido FOREIGN KEY (id_partido, id_torneo)
        REFERENCES partido(id_partido, id_torneo)
);

CREATE TABLE gol (
    id_gol     INT AUTO_INCREMENT PRIMARY KEY,
    id_partido INT NOT NULL,
    ci_jugador VARCHAR(8) NOT NULL,
    minuto     TINYINT UNSIGNED NOT NULL,
    autogol    BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_gol_planilla FOREIGN KEY (id_partido, ci_jugador) REFERENCES planilla_partido(id_partido, ci_jugador),
    CONSTRAINT chk_gol_minuto  CHECK (minuto BETWEEN 1 AND 60)
);

CREATE TABLE tarjeta (
    id_tarjeta INT AUTO_INCREMENT PRIMARY KEY,
    id_partido INT NOT NULL,
    ci_jugador VARCHAR(8) NOT NULL,
    minuto     TINYINT UNSIGNED NOT NULL,
    color      ENUM('amarilla','roja') NOT NULL,
    CONSTRAINT fk_tarjeta_planilla FOREIGN KEY (id_partido, ci_jugador) REFERENCES planilla_partido(id_partido, ci_jugador),
    CONSTRAINT chk_tarjeta_minuto  CHECK (minuto BETWEEN 1 AND 60)
);

CREATE TABLE sancion_jugador (
    id_sancion          INT AUTO_INCREMENT PRIMARY KEY,
    ci_jugador          VARCHAR(8) NOT NULL,
    id_torneo           INT NOT NULL,
    motivo              ENUM('roja','acumulacion_amarillas','disciplinaria') NOT NULL,
    numero_fecha_inicio TINYINT UNSIGNED NOT NULL,
    cantidad_fechas     TINYINT UNSIGNED NOT NULL,
    id_tarjeta          INT NULL,
    CONSTRAINT fk_sancion_ejt     FOREIGN KEY (id_torneo, ci_jugador) REFERENCES equipo_jugador_torneo(id_torneo, ci_jugador),
    CONSTRAINT fk_sancion_tarjeta FOREIGN KEY (id_tarjeta) REFERENCES tarjeta(id_tarjeta) ON DELETE CASCADE,
    CONSTRAINT chk_sancion_valores CHECK (numero_fecha_inicio >= 1 AND cantidad_fechas >= 1)
);


INSERT INTO turno (id_turno, hora_inicio, hora_fin) VALUES
 (1,'18:00:00','19:00:00'), (2,'19:00:00','20:00:00'), (3,'20:00:00','21:00:00'),
 (4,'21:00:00','22:00:00'), (5,'22:00:00','23:00:00');

INSERT INTO login (correo, contrasena, rol) VALUES
('admin@ucu.uy',
 '$2b$12$swSMNIOTAHxvDfcU9/Kbc.Wy4vjxBMXWAPRKOHpZYqhyMB2FO96K6',
 'administrador'),
('planillero@ucu.uy',
 '$2b$12$gNGn6ncWVSxpnBeiyVNjZeWuBfs/CJsFgk2asJpzzEGPfnyaKdGt2',
 'planillero');


CREATE USER IF NOT EXISTS 'login_app'@'%'      IDENTIFIED BY 'Login';
CREATE USER IF NOT EXISTS 'admin_app'@'%'      IDENTIFIED BY 'Admin';
CREATE USER IF NOT EXISTS 'planillero_app'@'%' IDENTIFIED BY 'Planillero';

GRANT SELECT ON torneo_f5.login TO 'login_app'@'%';

GRANT SELECT, INSERT, UPDATE, DELETE ON torneo_f5.* TO 'admin_app'@'%';

GRANT SELECT ON torneo_f5.* TO 'planillero_app'@'%';
GRANT INSERT, UPDATE, DELETE ON torneo_f5.planilla_partido TO 'planillero_app'@'%';
GRANT INSERT, UPDATE, DELETE ON torneo_f5.gol TO 'planillero_app'@'%';
GRANT INSERT, UPDATE, DELETE ON torneo_f5.tarjeta TO 'planillero_app'@'%';
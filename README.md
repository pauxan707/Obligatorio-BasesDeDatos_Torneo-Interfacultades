# Obligatorio-BasesDeDatos_Torneo-Interfacultades - Sistema de Gestión del Torneo Interfacultades de Fútbol 5
Sistema de información para la gestión del Torneo Interfacultades de Fútbol 5 de la universidad. El sistema permite la organización del fixture, el registro de resultados y sanciones, y la generación de reportes que apoyan tanto a la organización del torneo como a la toma de decisiones.

## Requisitos para correrlo
- Docker Desktop instalado y abierto (con 'Engine running')
- Clonar repo.
Py y SQL corren en el docker, no es necesario instalarlos

1. Clonar el repositorio y entrar a la carpeta:

   ```
   git clone <URL_DEL_REPOSITORIO>
   cd <CARPETA_DEL_REPOSITORIO>
   ```

2. Crear el archivo de config a partir del ejemplo dejado en la carpeta:

   - Windows: `copy .env.example .env`
   - Mac / Linux: `cp .env.example .env`

   Con los valores de ejemplo funciona, se puede editar si se desea

3. Levantar el docker:

   ```
   docker compose up --build
   ```

Esperas: `Running on http://0.0.0.0:5000` en la terminal

4. Abrir en el navegador:

   - `http://localhost:5000` -- la app
   
Si no anda se puede tratar de reiniciarla con `docker compose down -v` y después `docker compose up --build`
En la app de Docker se debe poder observar algo de esta manera
<img width="765" height="356" alt="image" src="https://github.com/user-attachments/assets/d5502103-8dfa-431f-a8b2-8d9bcbcb3556" />


## Usuarios MySQL
| Usuario | Permisos | Contraseña |
|---|---|---|
| `admin_app` | Lectura y escritura sobre todo el torneo | `Admin` |
| `planillero_app` | Solo registra planillas, goles y tarjetas (el resto es lectura) | `Planillero` |
| `login_app` | Solo lee la tabla `login` | `Login` |
| `root` | `Administra en consola` | `12345` |

## Usuarios del sistema
En la tabla login se encuentran los users de la app con bcrypt

| Rol | Correo | Contraseña | Qué puede hacer |
|---|---|---|---|
| **administrador** | `admin@ucu.uy` | `Admin2026` | Puede administrar jugadores, equipos, planteles, complejos, canchas, partidos y sanciones; también planillas, goles, tarjetas y reportes. |
| **planillero** | `planillero@ucu.uy` | `Planillero2026` | Consulta general, y registra planillas, goles y tarjetas. No puede borrar jugadores, equipos, partidos o sanciones. |

El usuario se elije según como te loguees, si se intenta hacer algo con el usuario incorrecto da error, para poder entrar a MySQL desde el host:

```
docker compose exec db mysql -uroot -p12345 torneo_f5
```

## Reportes
Los reportes solicitados se pueden encontrar en cada una de estas vistas, las últimas tres siendo las extras:

| Reporte | Vista |
|---|---|
| Tabla de posiciones | `v_posiciones` |
| Top 10 goleadores (autogoles no suman) | `v_goleadores` |
| Fair play por equipo (1 por amarilla, 3 por roja) | `v_fair_play` |
| Promedio de goles por partido | `v_promedio_goles` |
| Canchas y turnos más utilizados (sin contar cancelados) | `v_canchas_turnos` |
| Jugadores por facultad y tipo | `v_jugadores_facultad` |
| Inscriptos que nunca aparecieron en una planilla | `v_jugadores_sin_planilla` |
| Sanciones por equipo y motivo | `v_sanciones_equipo` |
| Porcentaje de partidos por estado | `v_porcentaje_partidos` |
| Partidos sin recibir goles| `v_vallas_invictas` |
| Jugadores con más tarjetas por facultad | `v_tarjetas_facultad` |
| Ocupación de cada complejo por día (turnos y canchas usadas) | `v_ocupacion_complejo` |

Hay una tabla extra (v_resultado_partido) que calcula el marcador en base a los goles, se usa en varias vistas como auxiliar de consultas.







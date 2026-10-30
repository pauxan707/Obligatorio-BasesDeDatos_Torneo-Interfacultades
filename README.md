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


## Usuarios
| Usuario | Permisos |
|---|---|
| `admin_app` | Lectura y escritura sobre todo el torneo |
| `planillero_app` | Solo registra planillas, goles y tarjetas (el resto es lectura) |
| `login_app` | Solo lee la tabla `login` |


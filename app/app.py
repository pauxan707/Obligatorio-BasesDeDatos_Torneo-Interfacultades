#Archivo principal de la aplicación en sí, punto de entrada. Maneja enrutamiento, control de acceso, 
#delega lógica de negocio, etc.

import functools
import os

import bcrypt
import pymysql
from flask import (Flask, abort, flash, redirect, render_template, request,
                   session, url_for)

import db
import reglas
import validacion

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "torneo-f5-2026-clave-secreta")

PLANILLERO_PUEDE = "/partidos/"


def usuario_db():
    # Qué usuario de MySQL usar según el rol de quien inició sesión
    return db.usuario_para(session.get("rol", "administrador"))


def login_requerido(fn):
    @functools.wraps(fn)
    def interno(*args, **kwargs):
        if "rol" not in session:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return interno


def admin_requerido(fn):
    @functools.wraps(fn)
    def interno(*args, **kwargs):
        if "rol" not in session:
            return redirect(url_for("login"))
        if session["rol"] != "administrador":
            abort(403)
        return fn(*args, **kwargs)
    return interno


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        errores = validacion.credenciales(request.form)
        if not errores:
            correo = request.form["correo"].strip().lower()
            contrasena = request.form["contrasena"]
            filas = db.consultar(
                "SELECT contrasena, rol FROM login WHERE correo = %s",
                (correo,), como="login")
            coincide = False
            if filas:
                try:
                    coincide = bcrypt.checkpw(
                        contrasena.encode("utf-8"),
                        filas[0]["contrasena"].encode("utf-8"))
                except ValueError:
                    coincide = False
            if coincide:
                session["correo"] = correo
                session["rol"] = filas[0]["rol"]
                return redirect(url_for("index"))
            errores = ["El email o la contraseña no son correctos."]
        return render_template("login.html", errores=errores)
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.context_processor
def globales():
    if "rol" not in session:
        return {}
    return {
        "rol": session.get("rol"),
        "correo": session.get("correo"),
        "es_admin": session.get("rol") == "administrador",
        "torneos": db.consultar(
            "SELECT id_torneo, nombre, estado FROM torneo "
            "ORDER BY anio DESC, semestre DESC", como=usuario_db()),
    }


@app.route("/")
@login_requerido
def index():
    como = usuario_db()
    consulta = """
        SELECT (SELECT COUNT(*) FROM equipo)        AS equipos,
               (SELECT COUNT(*) FROM jugador)       AS jugadores,
               (SELECT COUNT(*) FROM partido)       AS partidos,
               (SELECT COUNT(*) FROM partido WHERE estado = 'jugado') AS jugados,
               (SELECT COUNT(*) FROM sancion_jugador) AS sanciones,
               (SELECT COUNT(*) FROM cancha)        AS canchas
    """
    totales = db.consultar(consulta, como=como)[0]
    return render_template("index.html", totales=totales)


@app.route("/jugadores")
@login_requerido
def jugadores():
    como = usuario_db()
    filtro = request.args.get("q", "").strip()
    facultad = request.args.get("facultad", "")
    sql = """
        SELECT j.ci, j.nombre, j.apellido, j.email, j.fecha_nacimiento, j.tipo,
               f.nombre AS facultad,
               (SELECT COUNT(*) FROM equipo_jugador_torneo ejt
                 WHERE ejt.ci_jugador = j.ci) AS ediciones
        FROM jugador j JOIN facultad f ON f.id_facultad = j.id_facultad
        WHERE 1 = 1
    """
    params = []
    if filtro:
        sql += " AND (j.ci LIKE %s OR j.nombre LIKE %s OR j.apellido LIKE %s)"
        like = "%" + filtro + "%"
        params += [like, like, like]
    if facultad:
        sql += " AND j.id_facultad = %s"
        params.append(facultad)
    sql += " ORDER BY j.apellido, j.nombre"
    return render_template(
        "jugadores.html",
        filas=db.consultar(sql, params, como=como),
        facultades=db.consultar("SELECT id_facultad, nombre FROM facultad "
                                "ORDER BY nombre", como=como),
        q=filtro, facultad=facultad)


@app.route("/jugadores/nuevo")
@admin_requerido
def jugador_nuevo():
    return render_template("jugador_form.html", jugador=None,
                           facultades=db.consultar(
                               "SELECT id_facultad, nombre FROM facultad "
                               "ORDER BY nombre", como=usuario_db()))


@app.route("/jugadores", methods=["POST"])
@admin_requerido
def jugador_crear():
    errores = validacion.jugador(request.form)
    if errores:
        return render_template("jugador_form.html", jugador=request.form,
                               errores=errores, facultades=db.consultar(
                                   "SELECT id_facultad, nombre FROM facultad "
                                   "ORDER BY nombre", como=usuario_db())), 400
    with db.transaccion(usuario_db()) as cur:
        cur.execute(
            "INSERT INTO jugador (ci, nombre, apellido, email, fecha_nacimiento, "
            "id_facultad, tipo) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (request.form["ci"].strip(), request.form["nombre"].strip(),
             request.form["apellido"].strip(), request.form["email"].strip(),
             request.form["fecha_nacimiento"], request.form["id_facultad"],
             request.form["tipo"]))
    flash("Jugador creado correctamente.")
    return redirect(url_for("jugadores"))


@app.route("/jugadores/<ci>")
@admin_requerido
def jugador_editar(ci):
    filas = db.consultar("SELECT * FROM jugador WHERE ci = %s", (ci,),
                         como=usuario_db())
    if not filas:
        abort(404)
    return render_template("jugador_form.html", jugador=filas[0],
                           facultades=db.consultar(
                               "SELECT id_facultad, nombre FROM facultad "
                               "ORDER BY nombre", como=usuario_db()))


@app.route("/jugadores/<ci>", methods=["POST"])
@admin_requerido
def jugador_guardar(ci):
    datos = dict(request.form)
    datos["ci"] = ci
    errores = validacion.jugador(datos)
    if errores:
        return render_template("jugador_form.html", jugador=datos,
                               errores=errores, facultades=db.consultar(
                                   "SELECT id_facultad, nombre FROM facultad "
                                   "ORDER BY nombre", como=usuario_db())), 400
    with db.transaccion(usuario_db()) as cur:
        cur.execute(
            "UPDATE jugador SET nombre=%s, apellido=%s, email=%s, "
            "fecha_nacimiento=%s, id_facultad=%s, tipo=%s WHERE ci=%s",
            (datos["nombre"].strip(), datos["apellido"].strip(),
             datos["email"].strip(), datos["fecha_nacimiento"],
             datos["id_facultad"], datos["tipo"], ci))
    flash("Jugador actualizado.")
    return redirect(url_for("jugadores"))


@app.route("/jugadores/<ci>/borrar", methods=["POST"])
@admin_requerido
def jugador_borrar(ci):
    with db.transaccion(usuario_db()) as cur:
        cur.execute("DELETE FROM jugador WHERE ci = %s", (ci,))
    flash("Jugador eliminado.")
    return redirect(url_for("jugadores"))


@app.route("/equipos")
@login_requerido
def equipos():
    como = usuario_db()
    torneo = request.args.get("torneo", "")
    sql = """
        SELECT e.id_equipo, e.nombre, e.ci_capitan, e.id_torneo,
               f.nombre AS facultad, t.nombre AS edicion, t.estado,
               (SELECT COUNT(*) FROM equipo_jugador_torneo ejt
                 WHERE ejt.id_equipo = e.id_equipo) AS plantel,
               CONCAT(j.nombre, ' ', j.apellido) AS capitan
        FROM equipo e
        JOIN facultad f ON f.id_facultad = e.id_facultad
        JOIN torneo t   ON t.id_torneo = e.id_torneo
        LEFT JOIN jugador j ON j.ci = e.ci_capitan
        WHERE 1 = 1
    """
    params = []
    if torneo:
        sql += " AND e.id_torneo = %s"
        params.append(torneo)
    sql += " ORDER BY e.id_torneo DESC, e.nombre"
    return render_template("equipos.html", filas=db.consultar(sql, params, como=como),
                           torneo=torneo)


@app.route("/equipos/nuevo")
@admin_requerido
def equipo_nuevo():
    return render_template("equipo_form.html", equipo=None,
                           torneos=db.consultar("SELECT id_torneo, nombre, estado "
                                                "FROM torneo ORDER BY id_torneo DESC",
                                                como=usuario_db()),
                           facultades=db.consultar("SELECT id_facultad, nombre "
                                                   "FROM facultad ORDER BY nombre",
                                                   como=usuario_db()))


@app.route("/equipos", methods=["POST"])
@admin_requerido
def equipo_crear():
    errores = validacion.equipo(request.form)
    if errores:
        return render_template("equipo_form.html", equipo=request.form,
                               errores=errores,
                               torneos=db.consultar("SELECT id_torneo, nombre, "
                                                    "estado FROM torneo "
                                                    "ORDER BY id_torneo DESC",
                                                    como=usuario_db()),
                               facultades=db.consultar("SELECT id_facultad, nombre "
                                                       "FROM facultad ORDER BY nombre",
                                                       como=usuario_db())), 400
    with db.transaccion(usuario_db()) as cur:
        cur.execute(
            "INSERT INTO equipo (nombre, id_torneo, id_facultad, ci_capitan) "
            "VALUES (%s,%s,%s,NULL)",
            (request.form["nombre"].strip(), request.form["id_torneo"],
             request.form["id_facultad"]))
    flash("Equipo creado. Ahora cargá su plantel.")
    return redirect(url_for("equipos", torneo=request.form["id_torneo"]))


@app.route("/equipos/<int:id_equipo>")
@login_requerido
def equipo_detalle(id_equipo):
    como = usuario_db()
    filas = db.consultar(
        """SELECT e.*, f.nombre AS facultad, t.nombre AS edicion, t.estado,
                  CONCAT(j.nombre, ' ', j.apellido) AS capitan
             FROM equipo e
             JOIN facultad f ON f.id_facultad = e.id_facultad
             JOIN torneo t   ON t.id_torneo = e.id_torneo
             LEFT JOIN jugador j ON j.ci = e.ci_capitan
            WHERE e.id_equipo = %s""", (id_equipo,), como=como)
    if not filas:
        abort(404)
    plantel = db.consultar(        """SELECT ejt.ci_jugador, ejt.numero_camiseta, j.nombre, j.apellido,
                  j.tipo, j.email, f.nombre AS facultad
             FROM equipo_jugador_torneo ejt
             JOIN jugador j  ON j.ci = ejt.ci_jugador
             JOIN facultad f ON f.id_facultad = j.id_facultad
            WHERE ejt.id_equipo = %s
            ORDER BY ejt.numero_camiseta""", (id_equipo,), como=como)
    disponibles = db.consultar(
        """SELECT j.ci, CONCAT(j.nombre, ' ', j.apellido, ' (', j.tipo, ')') AS etiqueta
             FROM jugador j
             JOIN torneo t ON t.id_torneo = %s
            WHERE j.id_facultad = (SELECT id_facultad FROM equipo WHERE id_equipo = %s)
              AND j.ci NOT IN (SELECT ci_jugador FROM equipo_jugador_torneo
                                WHERE id_torneo = %s)
            ORDER BY j.apellido, j.nombre""",
        (filas[0]["id_torneo"], id_equipo, filas[0]["id_torneo"]), como=como)
    facultades = db.consultar(
        "SELECT id_facultad, nombre FROM facultad ORDER BY nombre", como=como)
    return render_template("equipo_detalle.html", equipo=filas[0], plantel=plantel,
                           disponibles=disponibles, facultades=facultades,
                           inscripcion=filas[0]["estado"] == "inscripcion")


@app.route("/equipos/<int:id_equipo>", methods=["POST"])
@admin_requerido
def equipo_guardar(id_equipo):
    datos = request.form
    errores = validacion.equipo(datos)
    if errores:
        flash(" ".join(errores), "error")
        return redirect(url_for("equipo_detalle", id_equipo=id_equipo))
    with db.transaccion(usuario_db()) as cur:
        reglas.modificar_equipo(cur, id_equipo, datos["id_facultad"])
        cur.execute("UPDATE equipo SET nombre=%s, id_facultad=%s "
                    "WHERE id_equipo=%s",
                    (datos["nombre"].strip(), datos["id_facultad"], id_equipo))
    flash("Equipo actualizado.")
    return redirect(url_for("equipo_detalle", id_equipo=id_equipo))


@app.route("/equipos/<int:id_equipo>/plantel", methods=["POST"])
@admin_requerido
def plantel_agregar(id_equipo):
    datos = request.form
    errores = validacion.plantel(datos)
    if errores:
        flash(" ".join(errores), "error")
        return redirect(url_for("equipo_detalle", id_equipo=id_equipo))
    with db.transaccion(usuario_db()) as cur:
        cur.execute("SELECT id_torneo FROM equipo WHERE id_equipo = %s",
                    (id_equipo,))
        fila = cur.fetchone()
        if fila is None:
            abort(404)
        reglas.agregar_al_plantel(cur, id_equipo, datos["ci_jugador"].strip(),
                                  fila["id_torneo"],
                                  int(datos["numero_camiseta"]))
        cur.execute(
            "INSERT INTO equipo_jugador_torneo "
            "(id_equipo, ci_jugador, id_torneo, numero_camiseta) "
            "VALUES (%s,%s,%s,%s)",
            (id_equipo, datos["ci_jugador"].strip(), fila["id_torneo"],
             int(datos["numero_camiseta"])))
    flash("Jugador agregado al plantel.")
    return redirect(url_for("equipo_detalle", id_equipo=id_equipo))


@app.route("/equipos/<int:id_equipo>/plantel/<ci>/borrar", methods=["POST"])
@admin_requerido
def plantel_quitar(id_equipo, ci):
    with db.transaccion(usuario_db()) as cur:
        cur.execute("SELECT id_torneo FROM equipo WHERE id_equipo = %s",
                    (id_equipo,))
        fila = cur.fetchone()
        if fila is None:
            abort(404)
        reglas.quitar_del_plantel(cur, id_equipo, ci, fila["id_torneo"])
        cur.execute("DELETE FROM equipo_jugador_torneo "
                    "WHERE id_equipo = %s AND ci_jugador = %s AND id_torneo = %s",
                    (id_equipo, ci, fila["id_torneo"]))
    flash("Jugador quitado del plantel.")
    return redirect(url_for("equipo_detalle", id_equipo=id_equipo))


@app.route("/equipos/<int:id_equipo>/capitan", methods=["POST"])
@admin_requerido
def capitan_asignar(id_equipo):
    ci = request.form.get("ci_capitan", "").strip()
    with db.transaccion(usuario_db()) as cur:
        cur.execute("SELECT id_torneo FROM equipo WHERE id_equipo = %s",
                    (id_equipo,))
        fila = cur.fetchone()
        if fila is None:
            abort(404)
        reglas.asignar_capitan(cur, id_equipo, ci, fila["id_torneo"])
        cur.execute("UPDATE equipo SET ci_capitan = %s WHERE id_equipo = %s",
                    (ci, id_equipo))
    flash("Capitán asignado.")
    return redirect(url_for("equipo_detalle", id_equipo=id_equipo))


@app.route("/equipos/<int:id_equipo>/borrar", methods=["POST"])
@admin_requerido
def equipo_borrar(id_equipo):
    with db.transaccion(usuario_db()) as cur:
        cur.execute("DELETE FROM equipo WHERE id_equipo = %s", (id_equipo,))
    flash("Equipo eliminado.")
    return redirect(url_for("equipos"))


@app.route("/complejos")
@login_requerido
def complejos():
    como = usuario_db()
    filas = db.consultar(
        """SELECT c.*, (SELECT COUNT(*) FROM cancha k
                         WHERE k.id_complejo = c.id_complejo) AS canchas
             FROM complejo c ORDER BY c.nombre""", como=como)
    canchas = db.consultar(
        "SELECT nombre_cancha, id_complejo, superficie, techada FROM cancha "
        "ORDER BY id_complejo, nombre_cancha", como=como)
    return render_template("complejos.html", filas=filas, canchas=canchas)


@app.route("/complejos/nuevo")
@admin_requerido
def complejo_nuevo():
    return render_template("complejo_form.html", complejo=None)


@app.route("/complejos", methods=["POST"])
@admin_requerido
def complejo_crear():
    errores = validacion.complejo(request.form)
    if errores:
        return render_template("complejo_form.html", complejo=request.form,
                               errores=errores), 400
    with db.transaccion(usuario_db()) as cur:
        cur.execute("INSERT INTO complejo (nombre, direccion, departamento) "
                    "VALUES (%s,%s,%s)",
                    (request.form["nombre"].strip(),
                     request.form["direccion"].strip(),
                     request.form["departamento"].strip()))
    flash("Complejo creado.")
    return redirect(url_for("complejos"))


@app.route("/complejos/<int:id_complejo>", methods=["POST"])
@admin_requerido
def complejo_guardar(id_complejo):
    errores = validacion.complejo(request.form)
    if errores:
        flash(" ".join(errores), "error")
        return redirect(url_for("complejos"))
    with db.transaccion(usuario_db()) as cur:
        cur.execute("UPDATE complejo SET nombre=%s, direccion=%s, "
                    "departamento=%s WHERE id_complejo=%s",
                    (request.form["nombre"].strip(),
                     request.form["direccion"].strip(),
                     request.form["departamento"].strip(), id_complejo))
    flash("Complejo actualizado.")
    return redirect(url_for("complejos"))


@app.route("/complejos/<int:id_complejo>/canchas", methods=["POST"])
@admin_requerido
def cancha_crear(id_complejo):
    datos = dict(request.form)
    datos["id_complejo"] = id_complejo
    errores = validacion.cancha(datos)
    if errores:
        flash(" ".join(errores), "error")
        return redirect(url_for("complejos"))
    with db.transaccion(usuario_db()) as cur:
        cur.execute("INSERT INTO cancha (nombre_cancha, id_complejo, superficie, "
                    "techada) VALUES (%s,%s,%s,%s)",
                    (datos["nombre_cancha"].strip(), id_complejo,
                     datos["superficie"], 1 if datos.get("techada") else 0))
    flash("Cancha agregada.")
    return redirect(url_for("complejos"))


@app.route("/complejos/<int:id_complejo>/canchas/<nombre>/borrar",
           methods=["POST"])
@admin_requerido
def cancha_borrar(id_complejo, nombre):
    with db.transaccion(usuario_db()) as cur:
        cur.execute("DELETE FROM cancha WHERE nombre_cancha = %s AND "
                    "id_complejo = %s", (nombre, id_complejo))
    flash("Cancha eliminada.")
    return redirect(url_for("complejos"))


@app.route("/complejos/<int:id_complejo>/borrar", methods=["POST"])
@admin_requerido
def complejo_borrar(id_complejo):
    with db.transaccion(usuario_db()) as cur:
        cur.execute("DELETE FROM complejo WHERE id_complejo = %s", (id_complejo,))
    flash("Complejo eliminado.")
    return redirect(url_for("complejos"))


_SQL_PARTIDO = """
    SELECT p.*, el.nombre AS local, ev.nombre AS visitante,
           co.nombre AS complejo, tn.nombre AS edicion, tn.estado AS estado_torneo,
           CONCAT(tu.hora_inicio, ' a ', tu.hora_fin) AS turno
      FROM partido p
      JOIN equipo el   ON el.id_equipo = p.id_equipo_local
      JOIN equipo ev   ON ev.id_equipo = p.id_equipo_visitante
      JOIN complejo co ON co.id_complejo = p.id_complejo
      JOIN turno tu    ON tu.id_turno = p.id_turno
      JOIN torneo tn   ON tn.id_torneo = p.id_torneo
"""


def _combo_partido(como, torneo=""):
    # Listas que necesitan los formularios de partido (equipos, turnos, canchas)
    equipos = db.consultar(
        "SELECT e.id_equipo, e.nombre, e.id_torneo, f.nombre AS facultad "
        "FROM equipo e JOIN facultad f ON f.id_facultad = e.id_facultad "
        "ORDER BY e.id_torneo DESC, e.nombre", como=como)
    canchas = db.consultar(
        "SELECT k.nombre_cancha, k.id_complejo, c.nombre AS complejo "
        "FROM cancha k JOIN complejo c ON c.id_complejo = k.id_complejo "
        "ORDER BY c.nombre, k.nombre_cancha", como=como)
    return {
        "equipos": equipos,
        "turnos": db.consultar("SELECT id_turno, hora_inicio, hora_fin FROM turno "
                               "ORDER BY id_turno", como=como),
        "canchas": canchas,
        "complejos": db.consultar("SELECT id_complejo, nombre FROM complejo "
                                  "ORDER BY nombre", como=como),
        "torneo": torneo,
    }


@app.route("/partidos")
@login_requerido
def partidos():
    como = usuario_db()
    torneo = request.args.get("torneo", "")
    fecha = request.args.get("fecha", "")
    sql = _SQL_PARTIDO + " WHERE 1 = 1"
    params = []
    if torneo:
        sql += " AND p.id_torneo = %s"
        params.append(torneo)
    if fecha:
        sql += " AND p.numero_fecha = %s"
        params.append(fecha)
    sql += " ORDER BY p.dia, p.id_turno, p.id_partido"
    return render_template("partidos.html",
                           filas=db.consultar(sql, params, como=como),
                           torneo=torneo, fecha=fecha)


@app.route("/partidos/nuevo")
@admin_requerido
def partido_nuevo():
    return render_template("partido_form.html", partido=None,
                           **_combo_partido(usuario_db(),
                                            request.args.get("torneo", "")))


@app.route("/partidos", methods=["POST"])
@admin_requerido
def partido_crear():
    datos = request.form
    errores = validacion.partido(datos)
    if not errores:
        with db.transaccion(usuario_db()) as cur:
            reglas.programar_partido(cur, datos)
            cur.execute(
                "INSERT INTO partido (id_torneo, numero_fecha, id_equipo_local, "
                "id_equipo_visitante, dia, id_turno, nombre_cancha, id_complejo, "
                "estado) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (datos["id_torneo"], datos["numero_fecha"],
                 datos["id_equipo_local"], datos["id_equipo_visitante"],
                 datos["dia"], datos["id_turno"], datos["nombre_cancha"],
                 datos["id_complejo"], datos["estado"]))
        flash("Partido programado.")
        return redirect(url_for("partidos", torneo=datos["id_torneo"]))
    return render_template("partido_form.html", partido=datos, errores=errores,
                           **_combo_partido(usuario_db())), 400


@app.route("/partidos/<int:id_partido>")
@login_requerido
def partido_detalle(id_partido):
    como = usuario_db()
    filas = db.consultar(_SQL_PARTIDO + " WHERE p.id_partido = %s",
                         (id_partido,), como=como)
    if not filas:
        abort(404)
    partido = filas[0]
    res = db.consultar(
        "SELECT goles_local, goles_visitante FROM v_resultado_partido "
        "WHERE id_partido = %s", (id_partido,), como=como)
    resultado = res[0] if res else None
    planilla = db.consultar(
        "SELECT pl.ci_jugador, pl.id_equipo, e.nombre AS equipo, "
        "CONCAT(j.nombre, ' ', j.apellido) AS jugador, "
        "(SELECT COUNT(*) FROM gol g WHERE g.id_partido = pl.id_partido "
        "   AND g.ci_jugador = pl.ci_jugador) AS goles, "
        "(SELECT COUNT(*) FROM tarjeta t WHERE t.id_partido = pl.id_partido "
        "   AND t.ci_jugador = pl.ci_jugador) AS tarjetas "
        "FROM planilla_partido pl "
        "JOIN equipo e ON e.id_equipo = pl.id_equipo "
        "JOIN jugador j ON j.ci = pl.ci_jugador "
        "WHERE pl.id_partido = %s ORDER BY e.nombre, j.apellido",
        (id_partido,), como=como)
    goles = db.consultar(
        "SELECT g.id_gol, g.minuto, g.autogol, g.ci_jugador, "
        "CONCAT(j.nombre, ' ', j.apellido) AS jugador, e.nombre AS equipo "
        "FROM gol g "
        "JOIN jugador j ON j.ci = g.ci_jugador "
        "LEFT JOIN planilla_partido pl ON pl.id_partido = g.id_partido "
        " AND pl.ci_jugador = g.ci_jugador "
        "LEFT JOIN equipo e ON e.id_equipo = pl.id_equipo "
        "WHERE g.id_partido = %s ORDER BY g.minuto, g.id_gol",
        (id_partido,), como=como)
    tarjetas = db.consultar(
        "SELECT t.id_tarjeta, t.minuto, t.color, t.ci_jugador, "
        "CONCAT(j.nombre, ' ', j.apellido) AS jugador, e.nombre AS equipo "
        "FROM tarjeta t "
        "JOIN jugador j ON j.ci = t.ci_jugador "
        "LEFT JOIN planilla_partido pl ON pl.id_partido = t.id_partido "
        " AND pl.ci_jugador = t.ci_jugador "
        "LEFT JOIN equipo e ON e.id_equipo = pl.id_equipo "
        "WHERE t.id_partido = %s ORDER BY t.minuto, t.id_tarjeta",
        (id_partido,), como=como)
    sanciones = db.consultar(
        "SELECT s.*, CONCAT(j.nombre, ' ', j.apellido) AS jugador "
        "FROM sancion_jugador s JOIN jugador j ON j.ci = s.ci_jugador "
        "WHERE s.id_torneo = %s ORDER BY s.numero_fecha_inicio",
        (partido["id_torneo"],), como=como)
    return render_template("partido_detalle.html", partido=partido,
                           resultado=resultado, planilla=planilla, goles=goles,
                           tarjetas=tarjetas, sanciones=sanciones)


@app.route("/partidos/<int:id_partido>", methods=["POST"])
@admin_requerido
def partido_guardar(id_partido):
    datos = request.form
    errores = validacion.partido(datos)
    if errores:
        flash(" ".join(errores), "error")
        return redirect(url_for("partido_detalle", id_partido=id_partido))
    with db.transaccion(usuario_db()) as cur:
        reglas.modificar_partido(cur, id_partido, datos)
        reglas.programar_partido(cur, datos, excluir_id=id_partido)
        cur.execute(
            "UPDATE partido SET numero_fecha=%s, id_equipo_local=%s, "
            "id_equipo_visitante=%s, dia=%s, id_turno=%s, nombre_cancha=%s, "
            "id_complejo=%s, estado=%s WHERE id_partido=%s",
            (datos["numero_fecha"], datos["id_equipo_local"],
             datos["id_equipo_visitante"], datos["dia"], datos["id_turno"],
             datos["nombre_cancha"], datos["id_complejo"], datos["estado"],
             id_partido))
    flash("Partido actualizado.")
    return redirect(url_for("partido_detalle", id_partido=id_partido))


@app.route("/partidos/<int:id_partido>/editar")
@admin_requerido
def partido_editar(id_partido):
    filas = db.consultar(_SQL_PARTIDO + " WHERE p.id_partido = %s",
                         (id_partido,), como=usuario_db())
    if not filas:
        abort(404)
    return render_template("partido_form.html", partido=filas[0],
                           **_combo_partido(usuario_db()))


@app.route("/partidos/<int:id_partido>/estado", methods=["POST"])
@admin_requerido
def partido_estado(id_partido):
    nuevo = request.form.get("estado", "")
    if nuevo not in validacion.ESTADOS_PARTIDO:
        abort(400)
    with db.transaccion(usuario_db()) as cur:
        reglas.cambiar_estado(cur, id_partido, nuevo)
        cur.execute("UPDATE partido SET estado = %s WHERE id_partido = %s",
                    (nuevo, id_partido))
    flash("Estado del partido actualizado a: {}.".format(nuevo))
    return redirect(url_for("partido_detalle", id_partido=id_partido))


@app.route("/partidos/<int:id_partido>/borrar", methods=["POST"])
@admin_requerido
def partido_borrar(id_partido):
    with db.transaccion(usuario_db()) as cur:
        reglas.borrar_partido(cur, id_partido)
        cur.execute("DELETE FROM partido WHERE id_partido = %s", (id_partido,))
    flash("Partido eliminado.")
    return redirect(url_for("partidos"))


@app.route("/partidos/<int:id_partido>/planilla")
@login_requerido
def planilla_form(id_partido):
    como = usuario_db()
    filas = db.consultar(_SQL_PARTIDO + " WHERE p.id_partido = %s",
                         (id_partido,), como=como)
    if not filas:
        abort(404)
    partido = filas[0]
    plantel = db.consultar(
        "SELECT ejt.ci_jugador, ejt.numero_camiseta, ejt.id_equipo, "
        "e.nombre AS equipo, CONCAT(j.nombre, ' ', j.apellido) AS jugador, j.tipo "
        "FROM equipo_jugador_torneo ejt "
        "JOIN jugador j ON j.ci = ejt.ci_jugador "
        "JOIN equipo e  ON e.id_equipo = ejt.id_equipo "
        "WHERE ejt.id_torneo = %s AND ejt.id_equipo IN (%s, %s) "
        "ORDER BY ejt.id_equipo, ejt.numero_camiseta",
        (partido["id_torneo"], partido["id_equipo_local"],
         partido["id_equipo_visitante"]), como=como)
    en_linea = {r["ci_jugador"] for r in db.consultar(
        "SELECT ci_jugador FROM planilla_partido WHERE id_partido = %s",
        (id_partido,), como=como)}
    suspendidos = {r["ci_jugador"] for r in db.consultar(
        "SELECT ci_jugador FROM sancion_jugador "
        "WHERE id_torneo = %s "
        "AND %s BETWEEN numero_fecha_inicio "
        "         AND numero_fecha_inicio + cantidad_fechas - 1",
        (partido["id_torneo"], partido["numero_fecha"]), como=como)}
    con_datos = {r["ci_jugador"] for r in db.consultar(
        "SELECT ci_jugador FROM gol WHERE id_partido = %s "
        "UNION SELECT ci_jugador FROM tarjeta WHERE id_partido = %s",
        (id_partido, id_partido), como=como)}
    return render_template("planilla_form.html", partido=partido,
                           plantel=plantel, en_linea=en_linea,
                           suspendidos=suspendidos, con_datos=con_datos)


@app.route("/partidos/<int:id_partido>/planilla", methods=["POST"])
@login_requerido
def planilla_guardar(id_partido):
    elegidos = set(request.form.getlist("jugador"))
    with db.transaccion(usuario_db()) as cur:
        cur.execute("SELECT estado, id_torneo FROM partido WHERE id_partido = %s",
                    (id_partido,))
        datos = cur.fetchone()
        if datos is None:
            abort(404)
        reglas.exigir_registrable(cur, id_partido)
        cur.execute("SELECT ci_jugador FROM planilla_partido "
                    "WHERE id_partido = %s", (id_partido,))
        actuales = {r["ci_jugador"] for r in cur.fetchall()}

        for ci in sorted(elegidos - actuales):
            equipo = reglas.agregar_a_planilla(cur, id_partido, ci)
            cur.execute(
                "INSERT INTO planilla_partido "
                "(id_partido, ci_jugador, id_equipo, id_torneo) "
                "VALUES (%s,%s,%s,%s)",
                (id_partido, ci, equipo, datos["id_torneo"]))

        if actuales - elegidos:
            reglas.exigir_corregible(cur, id_partido)
        for ci in sorted(actuales - elegidos):
            cur.execute("SELECT COUNT(*) AS n FROM gol "
                        "WHERE id_partido = %s AND ci_jugador = %s",
                        (id_partido, ci))
            if cur.fetchone()["n"]:
                raise reglas.Rechazo(
                    "No se puede quitar a un jugador de la planilla porque ya "
                    "le convirtió goles.")
            cur.execute("SELECT COUNT(*) AS n FROM tarjeta "
                        "WHERE id_partido = %s AND ci_jugador = %s",
                        (id_partido, ci))
            if cur.fetchone()["n"]:
                raise reglas.Rechazo(
                    "No se puede quitar a un jugador de la planilla porque ya "
                    "recibió tarjetas.")
            cur.execute("DELETE FROM planilla_partido "
                        "WHERE id_partido = %s AND ci_jugador = %s",
                        (id_partido, ci))
        reglas.exigir_planilla_completa(cur, id_partido)
    flash("Planilla guardada.")
    return redirect(url_for("partido_detalle", id_partido=id_partido))


@app.route("/partidos/<int:id_partido>/goles", methods=["POST"])
@login_requerido
def gol_crear(id_partido):
    datos = request.form
    errores = validacion.gol(datos)
    if errores:
        flash(" ".join(errores), "error")
        return redirect(url_for("partido_detalle", id_partido=id_partido))
    with db.transaccion(usuario_db()) as cur:
        reglas.exigir_en_planilla(cur, id_partido, datos["ci_jugador"])
        cur.execute(
            "INSERT INTO gol (id_partido, ci_jugador, minuto, autogol) "
            "VALUES (%s,%s,%s,%s)",
            (id_partido, datos["ci_jugador"], int(datos["minuto"]),
             1 if datos.get("autogol") else 0))
    flash("Gol registrado.")
    return redirect(url_for("partido_detalle", id_partido=id_partido))


@app.route("/partidos/<int:id_partido>/goles/<int:id_gol>/borrar",
           methods=["POST"])
@login_requerido
def gol_borrar(id_partido, id_gol):
    with db.transaccion(usuario_db()) as cur:
        reglas.exigir_corregible(cur, id_partido)
        cur.execute("DELETE FROM gol WHERE id_gol = %s AND id_partido = %s",
                    (id_gol, id_partido))
    flash("Gol eliminado.")
    return redirect(url_for("partido_detalle", id_partido=id_partido))


@app.route("/partidos/<int:id_partido>/tarjetas", methods=["POST"])
@login_requerido
def tarjeta_crear(id_partido):
    datos = request.form
    errores = validacion.tarjeta(datos)
    if errores:
        flash(" ".join(errores), "error")
        return redirect(url_for("partido_detalle", id_partido=id_partido))
    with db.transaccion(usuario_db()) as cur:
        reglas.exigir_en_planilla(cur, id_partido, datos["ci_jugador"])
        cur.execute(
            "INSERT INTO tarjeta (id_partido, ci_jugador, minuto, color) "
            "VALUES (%s,%s,%s,%s)",
            (id_partido, datos["ci_jugador"], int(datos["minuto"]),
             datos["color"]))
        reglas.sancion_automatica(cur, cur.lastrowid, id_partido,
                                 datos["ci_jugador"], datos["color"])
    flash("Tarjeta registrada.")
    return redirect(url_for("partido_detalle", id_partido=id_partido))


@app.route("/partidos/<int:id_partido>/tarjetas/<int:id_tarjeta>/borrar",
           methods=["POST"])
@login_requerido
def tarjeta_borrar(id_partido, id_tarjeta):
    with db.transaccion(usuario_db()) as cur:
        reglas.exigir_corregible(cur, id_partido)
        cur.execute("DELETE FROM tarjeta WHERE id_tarjeta = %s AND id_partido = %s",
                    (id_tarjeta, id_partido))
    flash("Tarjeta eliminada.")
    return redirect(url_for("partido_detalle", id_partido=id_partido))


@app.route("/sanciones")
@login_requerido
def sanciones():
    como = usuario_db()
    torneo = request.args.get("torneo", "")
    sql = ("SELECT s.*, CONCAT(j.nombre, ' ', j.apellido) AS jugador, "
           "t.nombre AS edicion, s.id_tarjeta IS NOT NULL AS automatica "
           "FROM sancion_jugador s "
           "JOIN jugador j ON j.ci = s.ci_jugador "
           "JOIN torneo t  ON t.id_torneo = s.id_torneo "
           "WHERE 1 = 1")
    params = []
    if torneo:
        sql += " AND s.id_torneo = %s"
        params.append(torneo)
    sql += " ORDER BY s.id_torneo DESC, s.numero_fecha_inicio, jugador"
    return render_template("sanciones.html", filas=db.consultar(sql, params, como=como),
                           torneo=torneo)


@app.route("/sanciones/nueva")
@admin_requerido
def sancion_nueva():
    return render_template("sancion_form.html",
                           jugadores=db.consultar(
                               "SELECT ci, CONCAT(nombre, ' ', apellido, ' - facultad ', "
                               "(SELECT nombre FROM facultad WHERE id_facultad = j.id_facultad)) "
                               "AS etiqueta FROM jugador j ORDER BY apellido",
                               como=usuario_db()))


@app.route("/sanciones", methods=["POST"])
@admin_requerido
def sancion_crear():
    datos = request.form
    errores = validacion.sancion(datos)
    if errores:
        flash(" ".join(errores), "error")
        return redirect(url_for("sancion_nueva"))
    with db.transaccion(usuario_db()) as cur:
        reglas.sancion_manual(cur, datos)
        cur.execute(
            "INSERT INTO sancion_jugador (ci_jugador, id_torneo, motivo, "
            "numero_fecha_inicio, cantidad_fechas, id_tarjeta) "
            "VALUES (%s,%s,%s,%s,%s,NULL)",
            (datos["ci_jugador"], datos["id_torneo"], datos["motivo"],
             int(datos["numero_fecha_inicio"]), int(datos["cantidad_fechas"])))
    flash("Sanción registrada.")
    return redirect(url_for("sanciones", torneo=datos["id_torneo"]))


@app.route("/sanciones/<int:id_sancion>/borrar", methods=["POST"])
@admin_requerido
def sancion_borrar(id_sancion):
    with db.transaccion(usuario_db()) as cur:
        cur.execute("SELECT id_tarjeta FROM sancion_jugador WHERE id_sancion = %s",
                    (id_sancion,))
        fila = cur.fetchone()
        if fila is None:
            abort(404)
        if fila["id_tarjeta"] is not None:
            raise reglas.Rechazo(
                "Esa sanción la generó el sistema a partir de una tarjeta. "
                "Para quitarla hay que eliminar la tarjeta que la originó.")
        cur.execute("DELETE FROM sancion_jugador WHERE id_sancion = %s",
                    (id_sancion,))
    flash("Sanción eliminada.")
    return redirect(url_for("sanciones"))


REPORTES = {
    "posiciones": {
        "titulo": "Tabla de posiciones",
        "origen": "enunciado",
        "nota": "Puntos, diferencia de goles y goles a favor definen el orden.",
        "sql": "SELECT equipo AS Equipo, pj AS PJ, pg AS G, pe AS E, "
               "perdidos AS P, gf AS GF, gc AS GC, dg AS DG, puntos AS Pts "
               "FROM v_posiciones WHERE id_torneo = %s "
               "ORDER BY puntos DESC, dg DESC, gf DESC",
        "torneo": True,
    },
    "goleadores": {
        "titulo": "Goleadores",
        "origen": "enunciado",
        "nota": "Los 10 jugadores con más goles. Los autogoles no suman.",
        "sql": "SELECT nombre AS Nombre, apellido AS Apellido, "
               "facultad AS Facultad, equipo AS Equipo, goles AS Goles "
               "FROM v_goleadores WHERE id_torneo = %s "
               "ORDER BY goles DESC, apellido, nombre LIMIT 10",
        "torneo": True,
    },
    "fair-play": {
        "titulo": "Fair play por equipo",
        "origen": "enunciado",
        "nota": "1 punto por amarilla y 3 por roja. Gana el que tiene menos.",
        "sql": "SELECT equipo AS Equipo, amarillas AS Amarillas, rojas AS Rojas, "
               "puntos_fair_play AS Puntos "
               "FROM v_fair_play WHERE id_torneo = %s "
               "ORDER BY puntos_fair_play ASC, equipo ASC",
        "torneo": True,
    },
    "promedio-goles": {
        "titulo": "Promedio de goles por partido",
        "origen": "enunciado",
        "nota": "Una fila por fecha y una fila con el total de la edición.",
        "sql": "SELECT CASE WHEN fecha IS NULL THEN 'Toda la edición' "
               "ELSE CONCAT('Fecha ', fecha) END AS Fecha, "
               "partidos AS Partidos, goles AS Goles, promedio_goles AS Promedio "
               "FROM v_promedio_goles WHERE id_torneo = %s "
               "ORDER BY alcance DESC, fecha",
        "torneo": True,
    },
    "canchas-turnos": {
        "titulo": "Canchas y turnos más utilizados",
        "origen": "enunciado",
        "nota": "Los partidos cancelados no ocuparon turno, así que no cuentan.",
        "sql": "SELECT CASE WHEN tipo = 'cancha' THEN 'Cancha' ELSE 'Turno' END "
               "AS Tipo, concepto AS Concepto, detalle AS Detalle, "
               "partidos AS Partidos FROM v_canchas_turnos WHERE id_torneo = %s "
               "ORDER BY partidos DESC, tipo",
        "torneo": True,
    },
    "jugadores-facultad": {
        "titulo": "Jugadores por facultad y tipo",
        "origen": "enunciado",
        "nota": "Sobre todos los jugadores registrados en el sistema.",
        "sql": "SELECT facultad AS Facultad, tipo AS Tipo, jugadores AS Jugadores "
               "FROM v_jugadores_facultad ORDER BY id_facultad, tipo",
        "torneo": False,
    },
    "sin-planilla": {
        "titulo": "Inscriptos que nunca figuraron en una planilla",
        "origen": "enunciado",
        "nota": "Jugadores en un plantel que no jugaron ningún partido.",
        "sql": "SELECT equipo AS Equipo, numero_camiseta AS Camiseta, "
               "nombre AS Nombre, apellido AS Apellido, tipo AS Tipo, "
               "facultad AS Facultad FROM v_jugadores_sin_planilla "
               "WHERE id_torneo = %s ORDER BY equipo, numero_camiseta",
        "torneo": True,
    },
    "sanciones": {
        "titulo": "Sanciones por equipo y motivo",
        "origen": "enunciado",
        "nota": "Agrupa por equipo y motivo las sanciones de la edición.",
        "sql": "SELECT equipo AS Equipo, motivo AS Motivo, "
               "sanciones AS Sanciones, fechas_sancionadas AS Fechas "
               "FROM v_sanciones_equipo WHERE id_torneo = %s "
               "ORDER BY equipo, motivo",
        "torneo": True,
    },
    "porcentaje-partidos": {
        "titulo": "Porcentaje de partidos por estado",
        "origen": "enunciado",
        "nota": "Jugados contra postergados, cancelados y programados.",
        "sql": "SELECT estado AS Estado, cantidad AS Partidos, "
               "CONCAT(porcentaje, ' %%') AS Porcentaje "
               "FROM v_porcentaje_partidos WHERE id_torneo = %s "
               "ORDER BY cantidad DESC",
        "torneo": True,
    },
    "vallas-invictas": {
        "titulo": "Vallas invictas por equipo",
        "origen": "extra",
        "nota": "Partidos jugados en los que el equipo no recibió goles.",
        "sql": "SELECT equipo AS Equipo, pj AS PJ, "
               "vallas_invictas AS 'Vallas invictas' "
               "FROM v_vallas_invictas WHERE id_torneo = %s "
               "ORDER BY vallas_invictas DESC, equipo",
        "torneo": True,
    },
    "tarjetas-facultad": {
        "titulo": "Jugadores con más tarjetas por facultad",
        "origen": "extra",
        "nota": "Dentro de cada facultad, primero los que tienen más tarjetas.",
        "sql": "SELECT facultad AS Facultad, nombre AS Nombre, apellido AS Apellido, "
               "amarillas AS Amarillas, rojas AS Rojas, tarjetas AS Total "
               "FROM v_tarjetas_facultad WHERE id_torneo = %s "
               "ORDER BY facultad, tarjetas DESC, apellido, nombre",
        "torneo": True,
    },
    "ocupacion-complejo": {
        "titulo": "Ocupación de cada complejo",
        "origen": "extra",
        "nota": "Partidos por complejo y día, con turnos y canchas usados.",
        "sql": "SELECT complejo AS Complejo, dia AS Día, partidos AS Partidos, "
               "turnos_ocupados AS Turnos, canchas_usadas AS Canchas "
               "FROM v_ocupacion_complejo WHERE id_torneo = %s "
               "ORDER BY dia, complejo",
        "torneo": True,
    },
}


@app.route("/reportes")
@login_requerido
def reportes():
    return render_template("reportes.html", reportes=REPORTES)


@app.route("/reportes/<nombre>")
@login_requerido
def reporte(nombre):
    config = REPORTES.get(nombre)
    if config is None:
        abort(404)
    como = usuario_db()
    torneo = request.args.get("torneo", "")
    if not torneo:
        filas = db.consultar(
            "SELECT id_torneo FROM torneo "
            "ORDER BY (estado = 'en_curso') DESC, id_torneo LIMIT 1", como=como)
        torneo = filas[0]["id_torneo"] if filas else 0
    columnas, filas = [], []
    if config["torneo"]:
        filas = db.consultar(config["sql"], (torneo,), como=como)
    else:
        filas = db.consultar(config["sql"], como=como)
    if filas:
        columnas = list(filas[0].keys())
    return render_template("reporte.html", nombre=nombre, config=config,
                           columnas=columnas, filas=filas, torneo=torneo)


@app.errorhandler(reglas.Rechazo)
def _rechazo(e):
    # Si no se cumple una regla, se vuelve al formulario mostrando el error
    if request.method == "POST" and request.referrer:
        flash(str(e), "error")
        return redirect(request.referrer)
    return render_template("error.html", mensaje=str(e)), 400


@app.errorhandler(pymysql.err.MySQLError)
def _error_mysql(e):
    # Errores que devuelve MySQL (la validación de la base). Los más comunes  se traducen a un mensaje que sea legible
    codigos = {
        1062: "Ya existe un registro con esos datos (valor duplicado).",
        1048: "Falta un dato obligatorio.",
        1264: "Uno de los valores numérico está fuera de rango.",
        1265: "Uno de los valores no está permitido para ese campo.",
        1406: "Uno de los datos es demasiado largo para su campo.",
        1451: "No se puede eliminar: otro registro depende de este.",
        1452: "No se puede guardar: el registro que se quiere referenciar no existe.",
        1142: "Tu usuario de base de datos no tiene permiso para esta operación.",
    }
    codigo = e.args[0] if e.args else None
    mensaje = codigos.get(codigo, "Error de base de datos: {}".format(e))
    if request.method == "POST" and request.referrer:
        flash(mensaje, "error")
        return redirect(request.referrer)
    return render_template("error.html", mensaje=mensaje), 400


@app.errorhandler(403)
def _403(e):
    return render_template(
        "error.html",
        mensaje="No tenés permiso para esta operación. "
                "Los planilleros solo registran planillas, goles y tarjetas."), 403


@app.errorhandler(404)
def _404(e):
    return render_template("error.html", mensaje="No se encontró lo que buscabas."), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

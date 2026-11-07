# Acá se manejan las reglas de negocio solicitadas por la letra:
#Si alguna no se cumple se lanza Rechazo (una Exception) y la transacción se deshace

from datetime import date, datetime, time, timedelta


class Rechazo(Exception):
    # Error de una regla del torneo, el mensaje se le muestra al usuario
    pass


def _partido(cur, id_partido):
    cur.execute(
        "SELECT p.*, t.hora_fin FROM partido p "
        "JOIN turno t ON t.id_turno = p.id_turno WHERE p.id_partido = %s",
        (id_partido,))
    fila = cur.fetchone()
    if fila is None:
        raise Rechazo("El partido no existe.")
    return fila


def _nombre_equipo(cur, id_equipo):
    cur.execute("SELECT nombre FROM equipo WHERE id_equipo = %s", (id_equipo,))
    fila = cur.fetchone()
    return fila["nombre"] if fila else "el equipo"


def _fin_partido(partido):
    # Devuelve la fecha y hora en que termina el partido. pymysql trae las columnas TIME como timedelta, por eso hay que pasarlas a time antes de juntarlas con el día
    fin = partido["hora_fin"]
    if isinstance(fin, timedelta):
        segundos = int(fin.total_seconds())
        fin = time(segundos // 3600, (segundos % 3600) // 60, segundos % 60)
    return datetime.combine(partido["dia"], fin)


def _exigir_inscripcion(cur, id_torneo):
    # Los planteles solo se pueden tocar mientras el torneo está en inscripción
    cur.execute("SELECT nombre, estado FROM torneo WHERE id_torneo = %s", (id_torneo,))
    torneo = cur.fetchone()
    if torneo is None:
        raise Rechazo("La edición del torneo no existe.")
    if torneo["estado"] != "inscripcion":
        raise Rechazo(
            'Los planteles solo se pueden modificar mientras el torneo está en '
            'etapa de inscripción. "{}" está en {}.'.format(torneo["nombre"],
                                                            torneo["estado"]))
    return torneo


def agregar_al_plantel(cur, id_equipo, ci_jugador, id_torneo, numero_camiseta):
    #chequea todas las reglas antes de agregar un jugador al plantel
    _exigir_inscripcion(cur, id_torneo)

    cur.execute("SELECT * FROM equipo WHERE id_equipo = %s", (id_equipo,))
    equipo = cur.fetchone()
    if equipo is None:
        raise Rechazo("El equipo no existe.")
    if equipo["id_torneo"] != id_torneo:
        raise Rechazo("Ese equipo pertenece a otra edición del torneo.")

    cur.execute("SELECT * FROM jugador WHERE ci = %s", (ci_jugador,))
    jugador = cur.fetchone()
    if jugador is None:
        raise Rechazo("El jugador no existe.")

    if jugador["id_facultad"] != equipo["id_facultad"]:
        raise Rechazo(
            "{} {} pertenece a otra facultad: todos los jugadores del plantel "
            "tienen que ser de la facultad que representa el equipo.".format(
                jugador["nombre"], jugador["apellido"]))

    cur.execute(
        "SELECT e.nombre FROM equipo_jugador_torneo ejt "
        "JOIN equipo e ON e.id_equipo = ejt.id_equipo "
        "WHERE ejt.ci_jugador = %s AND ejt.id_torneo = %s",
        (ci_jugador, id_torneo))
    otro = cur.fetchone()
    if otro:
        raise Rechazo("Ya está inscripto en {} en esta edición.".format(otro["nombre"]))

    cur.execute(
        "SELECT COUNT(*) AS n FROM equipo_jugador_torneo "
        "WHERE id_equipo = %s AND id_torneo = %s", (id_equipo, id_torneo))
    cantidad = cur.fetchone()["n"]
    if cantidad >= 10:
        raise Rechazo("El plantel ya tiene 10 jugadores, que es el máximo.")

    if jugador["tipo"] in ("docente", "funcionario"):
        cur.execute(
            "SELECT COUNT(*) AS n FROM equipo_jugador_torneo ejt "
            "JOIN jugador j ON j.ci = ejt.ci_jugador "
            "WHERE ejt.id_equipo = %s AND ejt.id_torneo = %s "
            "AND j.tipo IN ('docente','funcionario')",
            (id_equipo, id_torneo))
        if cur.fetchone()["n"] >= 2:
            raise Rechazo(
                "Un plantel admite como máximo 2 jugadores docentes o "
                "funcionarios entre todos ellos.")

    cur.execute(
        "SELECT COUNT(*) AS n FROM equipo_jugador_torneo "
        "WHERE id_equipo = %s AND id_torneo = %s AND numero_camiseta = %s",
        (id_equipo, id_torneo, numero_camiseta))
    if cur.fetchone()["n"] > 0:
        raise Rechazo("El número {} ya está ocupado en este plantel.".format(
            numero_camiseta))


def quitar_del_plantel(cur, id_equipo, ci_jugador, id_torneo):
    _exigir_inscripcion(cur, id_torneo)

    cur.execute(
        "SELECT COUNT(*) AS n FROM equipo_jugador_torneo "
        "WHERE id_equipo = %s AND id_torneo = %s", (id_equipo, id_torneo))
    if cur.fetchone()["n"] <= 5:
        raise Rechazo("El plantel no puede quedar con menos de 5 jugadores.")

    cur.execute("SELECT ci_capitan FROM equipo WHERE id_equipo = %s", (id_equipo,))
    if cur.fetchone()["ci_capitan"] == ci_jugador:
        raise Rechazo("Es el capitán: primero hay que designar a otro.")


def modificar_equipo(cur, id_equipo, id_facultad):
    # Si el equipo ya tiene jugadores no se le puede cambiar la facultad, porque todo el plantel tiene que ser de la facultad del equipo
    cur.execute("SELECT id_facultad FROM equipo WHERE id_equipo = %s", (id_equipo,))
    equipo = cur.fetchone()
    if equipo is None:
        raise Rechazo("El equipo no existe.")
    if equipo["id_facultad"] == int(id_facultad):
        return
    cur.execute(
        "SELECT COUNT(*) AS n FROM equipo_jugador_torneo WHERE id_equipo = %s",
        (id_equipo,))
    if cur.fetchone()["n"] > 0:
        raise Rechazo(
            "No se puede cambiar la facultad de un equipo que ya tiene "
            "jugadores en el plantel.")


def asignar_capitan(cur, id_equipo, ci_jugador, id_torneo):
    # El capitán tiene que ser alguien del plantel 
    cur.execute(
        "SELECT COUNT(*) AS n FROM equipo_jugador_torneo "
        "WHERE id_equipo = %s AND ci_jugador = %s AND id_torneo = %s",
        (id_equipo, ci_jugador, id_torneo))
    if cur.fetchone()["n"] == 0:
        raise Rechazo("El capitán tiene que ser uno de los jugadores del plantel.")


def programar_partido(cur, datos, excluir_id=None):
    # Controles que pide la letra al programar un partido.

    # excluir_id se usa al editar: es el mismo partido, y así no choca contra
    # sí mismo en los controles de "ya existe"
    id_torneo = int(datos["id_torneo"])
    local = int(datos["id_equipo_local"])
    visita = int(datos["id_equipo_visitante"])
    fecha = int(datos["numero_fecha"])
    dia = datos["dia"]
    turno = int(datos["id_turno"])
    cancha = datos["nombre_cancha"]
    complejo = int(datos["id_complejo"])

    if local == visita:
        raise Rechazo("Un equipo no puede jugar contra sí mismo.")

    for equipo_id in (local, visita):
        cur.execute("SELECT id_torneo FROM equipo WHERE id_equipo = %s", (equipo_id,))
        fila = cur.fetchone()
        if fila is None:
            raise Rechazo("Uno de los equipos elegidos no existe.")
        if fila["id_torneo"] != id_torneo:
            raise Rechazo(
                "Los dos equipos tienen que pertenecer a la misma edición "
                "del torneo.")

        cur.execute(
            "SELECT COUNT(*) AS n FROM equipo_jugador_torneo "
            "WHERE id_equipo = %s AND id_torneo = %s", (equipo_id, id_torneo))
        n = cur.fetchone()["n"]
        if n < 5:
            raise Rechazo(
                "{} necesita al menos 5 jugadores en el plantel para jugar un "
                "partido (tiene {}).".format(_nombre_equipo(cur, equipo_id), n))

    sql = (
        "SELECT COUNT(*) AS n FROM partido "
        "WHERE id_torneo = %s AND estado <> 'cancelado' AND ("
        "  (id_equipo_local = %s AND id_equipo_visitante = %s) OR "
        "  (id_equipo_local = %s AND id_equipo_visitante = %s))")
    params = [id_torneo, local, visita, visita, local]
    if excluir_id is not None:
        sql += " AND id_partido <> %s"
        params.append(excluir_id)
    cur.execute(sql, params)
    if cur.fetchone()["n"] > 0:
        raise Rechazo("Esos dos equipos ya se enfrentaron en esta edición.")

    for equipo_id in (local, visita):
        sql = ("SELECT COUNT(*) AS n FROM partido "
               "WHERE id_torneo = %s AND numero_fecha = %s "
               "AND estado <> 'cancelado' "
               "AND (id_equipo_local = %s OR id_equipo_visitante = %s)")
        params = [id_torneo, fecha, equipo_id, equipo_id]
        if excluir_id is not None:
            sql += " AND id_partido <> %s"
            params.append(excluir_id)
        cur.execute(sql, params)
        if cur.fetchone()["n"] > 0:
            raise Rechazo("{} ya juega en la fecha {} de esta edición.".format(
                _nombre_equipo(cur, equipo_id), fecha))

    sql = ("SELECT COUNT(*) AS n FROM partido "
           "WHERE dia = %s AND id_turno = %s AND nombre_cancha = %s "
           "AND id_complejo = %s AND estado <> 'cancelado'")
    params = [dia, turno, cancha, complejo]
    if excluir_id is not None:
        sql += " AND id_partido <> %s"
        params.append(excluir_id)
    cur.execute(sql, params)
    if cur.fetchone()["n"] > 0:
        raise Rechazo(
            "Esa cancha ya tiene un partido asignado el mismo día y turno.")

    if datos.get("estado") == "jugado":
        cur.execute("SELECT hora_fin FROM turno WHERE id_turno = %s", (turno,))
        fila = cur.fetchone()
        if fila is not None:
            fila["dia"] = date.fromisoformat(dia)
            if datetime.now() < _fin_partido(fila):
                raise Rechazo(
                    "El partido todavía no se disputó: el día y el turno aún no "
                    "pasaron, así que no se puede marcar como jugado.")


def modificar_partido(cur, id_partido, datos):
    # Si el partido ya se jugó no se puede reprogramar ni cambiar de estado
    partido = _partido(cur, id_partido)

    if partido["estado"] != "jugado":
        return

    se_mueve = (
        str(partido["dia"]) != str(datos.get("dia"))
        or str(partido["id_turno"]) != str(datos.get("id_turno"))
        or partido["nombre_cancha"] != datos.get("nombre_cancha")
        or str(partido["id_complejo"]) != str(datos.get("id_complejo"))
        or str(partido["id_equipo_local"]) != str(datos.get("id_equipo_local"))
        or str(partido["id_equipo_visitante"]) != str(datos.get("id_equipo_visitante"))
        or str(partido["numero_fecha"]) != str(datos.get("numero_fecha"))
    )
    if se_mueve:
        raise Rechazo(
            "El partido ya se disputó: no se puede reprogramar ni cambiar de "
            "equipos ni de fecha.")
    if datos.get("estado") != "jugado":
        raise Rechazo("El partido ya se jugó: su estado no se puede cambiar.")


def borrar_partido(cur, id_partido):
    if _partido(cur, id_partido)["estado"] == "jugado":
        raise Rechazo("Un partido jugado no se puede eliminar.")


def cambiar_estado(cur, id_partido, nuevo_estado):
    # Un partido jugado ya no cambia de estado, y para marcarlo como jugado el dia y el turno tienen que haber pasado.
    partido = _partido(cur, id_partido)
    if partido["estado"] == "jugado":
        raise Rechazo("El partido ya se jugó: su estado no se puede cambiar.")
    if nuevo_estado == "jugado" and datetime.now() < _fin_partido(partido):
        raise Rechazo(
            "El partido todavía no se disputó: el día y el turno aún no pasaron.")
    return partido


def exigir_registrable(cur, id_partido):
    # Para cargar la planilla, goles o tarjetas alcanza con que el partido esté jugado, el límite de 48 horas es solo para corregir
    partido = _partido(cur, id_partido)
    if partido["estado"] != "jugado":
        raise Rechazo("Este partido todavía no se jugó.")
    return partido


def exigir_corregible(cur, id_partido):
    # Lo ya cargado solo se puede corregir o borrar hasta 48 horas después del partido
    partido = _partido(cur, id_partido)
    if partido["estado"] != "jugado":
        raise Rechazo("Este partido todavía no se jugó.")
    if datetime.now() > _fin_partido(partido) + timedelta(hours=48):
        raise Rechazo(
            "Ya pasaron las 48 horas posteriores a la disputa de este partido: "
            "su resultado no se puede corregir.")
    return partido


def agregar_a_planilla(cur, id_partido, ci_jugador):
    # Controla que el jugador pueda ir en la planilla y luego devuelve su equipo
    partido = _partido(cur, id_partido)
    if partido["estado"] != "jugado":
        raise Rechazo("La planilla se registra una vez que el partido se disputó.")

    cur.execute(
        "SELECT id_equipo FROM equipo_jugador_torneo "
        "WHERE ci_jugador = %s AND id_torneo = %s AND id_equipo IN (%s, %s)",
        (ci_jugador, partido["id_torneo"],
         partido["id_equipo_local"], partido["id_equipo_visitante"]))
    fila = cur.fetchone()
    if fila is None:
        raise Rechazo(
            "Solo pueden figurar en la planilla jugadores del plantel de uno "
            "de los dos equipos que juegan.")

    exigir_no_suspendido(cur, ci_jugador, partido["id_torneo"],
                         partido["numero_fecha"])
    return fila["id_equipo"]


def exigir_no_suspendido(cur, ci_jugador, id_torneo, numero_fecha):
    cur.execute(
        "SELECT motivo, numero_fecha_inicio, cantidad_fechas "
        "FROM sancion_jugador "
        "WHERE ci_jugador = %s AND id_torneo = %s "
        "AND %s BETWEEN numero_fecha_inicio "
        "         AND numero_fecha_inicio + cantidad_fechas - 1",
        (ci_jugador, id_torneo, numero_fecha))
    sancion = cur.fetchone()
    if sancion is None:
        return
    cur.execute("SELECT nombre, apellido FROM jugador WHERE ci = %s", (ci_jugador,))
    jugador = cur.fetchone()
    hasta = sancion["numero_fecha_inicio"] + sancion["cantidad_fechas"] - 1
    raise Rechazo(
        "{} {} está suspendido ({}) desde la fecha {} hasta la {}.".format(
            jugador["nombre"], jugador["apellido"], sancion["motivo"],
            sancion["numero_fecha_inicio"], hasta))


def exigir_en_planilla(cur, id_partido, ci_jugador):
    # Solo los que están en la planilla pueden hacer goles o recibir tarjetas
    exigir_registrable(cur, id_partido)
    cur.execute(
        "SELECT 1 FROM planilla_partido WHERE id_partido = %s AND ci_jugador = %s",
        (id_partido, ci_jugador))
    if cur.fetchone() is None:
        raise Rechazo(
            "Solo pueden convertir goles o recibir tarjetas los jugadores que "
            "figuren en la planilla.")


def exigir_planilla_completa(cur, id_partido):
    # Cada equipo tiene que tener entre 5 y 10 jugadores en la planilla
    partido = _partido(cur, id_partido)
    for lado, equipo_id in (("local", partido["id_equipo_local"]),
                            ("visitante", partido["id_equipo_visitante"])):
        cur.execute(
            "SELECT COUNT(*) AS n FROM planilla_partido "
            "WHERE id_partido = %s AND id_equipo = %s",
            (id_partido, equipo_id))
        n = cur.fetchone()["n"]
        if n < 5:
            raise Rechazo(
                "El equipo {} necesita al menos 5 jugadores en la planilla "
                "(quedó con {}).".format(lado, n))
        if n > 10:
            raise Rechazo(
                "El equipo {} no puede tener más de 10 jugadores en la planilla "
                "(quedó con {}).".format(lado, n))


def sancion_automatica(cur, id_tarjeta, id_partido, ci_jugador, color):
    # Una roja, o la tercera amarilla en la edición, suspende al jugador para la siguiente fecha a la del partido
    partido = _partido(cur, id_partido)
    id_torneo = partido["id_torneo"]
    fecha_siguiente = partido["numero_fecha"] + 1

    if color == "roja":
        cur.execute(
            "INSERT INTO sancion_jugador "
            "(ci_jugador, id_torneo, motivo, numero_fecha_inicio, "
            " cantidad_fechas, id_tarjeta) VALUES (%s, %s, 'roja', %s, 1, %s)",
            (ci_jugador, id_torneo, fecha_siguiente, id_tarjeta))
        return

    cur.execute(
        "SELECT COUNT(*) AS n FROM tarjeta t "
        "JOIN partido p ON p.id_partido = t.id_partido "
        "WHERE t.ci_jugador = %s AND p.id_torneo = %s AND t.color = 'amarilla'",
        (ci_jugador, id_torneo))
    if cur.fetchone()["n"] == 3:
        cur.execute(
            "INSERT INTO sancion_jugador "
            "(ci_jugador, id_torneo, motivo, numero_fecha_inicio, "
            " cantidad_fechas, id_tarjeta) VALUES (%s, %s, "
            " 'acumulacion_amarillas', %s, 1, %s)",
            (ci_jugador, id_torneo, fecha_siguiente, id_tarjeta))


def sancion_manual(cur, datos):
    # A mano solo se cargan sanciones disciplinarias. Las de roja y de amarillas las crea el sistema cuando se registra la tarjeta
    if datos.get("motivo") != "disciplinaria":
        raise Rechazo(
            "Las sanciones cargadas a mano son de motivo disciplinaria. Las de "
            "roja y de acumulación de amarillas las genera el sistema al "
            "registrar la tarjeta.")

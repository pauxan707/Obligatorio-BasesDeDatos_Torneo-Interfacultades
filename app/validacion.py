#Validación de los campos en el backend  (formato, largo y rangos) 


import re
from datetime import date, datetime

RE_CI = re.compile(r"^\d{7,8}$")
RE_EMAIL = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
RE_SIN_DIGITOS = re.compile(r"\d")

TIPOS_JUGADOR = ("grado", "posgrado", "docente", "funcionario")
ESTADOS_TORNEO = ("inscripcion", "en_curso", "finalizado")
ESTADOS_PARTIDO = ("programado", "jugado", "postergado", "cancelado")
COLORES = ("amarilla", "roja")
MOTIVOS = ("roja", "acumulacion_amarillas", "disciplinaria")
SUPERFICIES = ("sintetico", "parquet")
ROLES = ("administrador", "planillero")


def _obligatorio(valor, campo, minimo=1, maximo=255):
    errores = []
    valor = (valor or "").strip()
    if len(valor) < minimo:
        errores.append(f"{campo} es obligatorio.")
    elif len(valor) > maximo:
        errores.append(f"{campo} no puede superar los {maximo} caracteres.")
    return errores


def _solo_letras(valor, campo, minimo=2, maximo=50):
    errores = _obligatorio(valor, campo, minimo, maximo)
    if errores:
        return errores
    if RE_SIN_DIGITOS.search(valor):
        errores.append(f"{campo} no puede contener números.")
    return errores


def _fecha(valor, campo, futura_permitida=True):
    if not valor:
        return [f"{campo} es obligatorio."]
    try:
        dia = datetime.strptime(valor, "%Y-%m-%d").date()
    except ValueError:
        return [f"{campo} no es una fecha válida (use aaaa-mm-dd)."]
    if not futura_permitida and dia > date.today():
        return [f"{campo} no puede ser una fecha futura."]
    return []


def _entero(valor, campo, minimo=None, maximo=None):
    if valor is None or str(valor).strip() == "":
        return [f"{campo} es obligatorio."]
    try:
        n = int(valor)
    except (TypeError, ValueError):
        return [f"{campo} tiene que ser un número entero."]
    if minimo is not None and n < minimo:
        return [f"{campo} tiene que ser como mínimo {minimo}."]
    if maximo is not None and n > maximo:
        return [f"{campo} no puede superar {maximo}."]
    return []


def _elegido(valor, campo, opciones):
    if valor not in opciones:
        return [f"{campo} tiene que ser uno de: {', '.join(opciones)}."]
    return []


def jugador(datos):
    ci = (datos.get("ci") or "").strip()
    errores = []
    if not RE_CI.match(ci):
        errores.append("La cédula debe tener 7 u 8 dígitos, sin puntos ni guiones.")
    errores += _solo_letras(datos.get("nombre", ""), "El nombre")
    errores += _solo_letras(datos.get("apellido", ""), "El apellido")
    if not RE_EMAIL.match((datos.get("email") or "").strip()):
        errores.append("El email no tiene un formato válido.")
    errores += _fecha(datos.get("fecha_nacimiento", ""), "La fecha de nacimiento",
                      futura_permitida=False)
    errores += _entero(datos.get("id_facultad", ""), "La facultad", 1)
    errores += _elegido(datos.get("tipo", ""), "El tipo", TIPOS_JUGADOR)
    return errores


def equipo(datos):
    errores = _obligatorio(datos.get("nombre", ""), "El nombre del equipo", 2, 60)
    errores += _entero(datos.get("id_torneo", ""), "La edición", 1)
    errores += _entero(datos.get("id_facultad", ""), "La facultad", 1)
    return errores


def complejo(datos):
    errores = _obligatorio(datos.get("nombre", ""), "El nombre", 2, 100)
    errores += _obligatorio(datos.get("direccion", ""), "La dirección", 2, 150)
    errores += _obligatorio(datos.get("departamento", ""), "El departamento", 2, 50)
    return errores


def cancha(datos):
    errores = _obligatorio(datos.get("nombre_cancha", ""), "El nombre de la cancha", 1, 50)
    errores += _entero(datos.get("id_complejo", ""), "El complejo", 1)
    errores += _elegido(datos.get("superficie", ""), "La superficie", SUPERFICIES)
    return errores


def partido(datos):
    errores = _entero(datos.get("numero_fecha", ""), "La fecha del torneo", 1, 255)
    local = datos.get("id_equipo_local")
    visita = datos.get("id_equipo_visitante")
    if local and visita and str(local).strip() == str(visita).strip():
        errores.append("Un equipo no puede jugar contra sí mismo.")
    errores += _entero(local, "El equipo local", 1)
    errores += _entero(visita, "El equipo visitante", 1)
    errores += _fecha(datos.get("dia", ""), "El día del partido")
    errores += _entero(datos.get("id_turno", ""), "El turno", 1, 5)
    if not (datos.get("nombre_cancha") or "").strip():
        errores.append("Debe elegir una cancha.")
    errores += _entero(datos.get("id_complejo", ""), "El complejo", 1)
    errores += _elegido(datos.get("estado", ""), "El estado", ESTADOS_PARTIDO)
    return errores


def gol(datos):
    errores = _obligatorio(datos.get("ci_jugador", ""), "El jugador", 7, 8)
    errores += _entero(datos.get("minuto", ""), "El minuto", 1, 60)
    return errores


def tarjeta(datos):
    errores = _obligatorio(datos.get("ci_jugador", ""), "El jugador", 7, 8)
    errores += _entero(datos.get("minuto", ""), "El minuto", 1, 60)
    errores += _elegido(datos.get("color", ""), "El color", COLORES)
    return errores


def sancion(datos):
    errores = _obligatorio(datos.get("ci_jugador", ""), "El jugador", 7, 8)
    errores += _elegido(datos.get("motivo", ""), "El motivo", MOTIVOS)
    errores += _entero(datos.get("numero_fecha_inicio", ""), "La fecha de inicio", 1, 255)
    errores += _entero(datos.get("cantidad_fechas", ""), "La cantidad de fechas", 1, 255)
    return errores


def plantel(datos):

    
    errores = _obligatorio(datos.get("ci_jugador", ""), "El jugador", 7, 8)
    errores += _entero(datos.get("numero_camiseta", ""), "El número de camiseta", 1, 99)
    return errores


def credenciales(datos):
    errores = []
    if not RE_EMAIL.match((datos.get("correo") or "").strip()):
        errores.append("El email no tiene un formato válido.")
    if not (datos.get("contrasena") or ""):
        errores.append("La contraseña es obligatoria.")
    return errores

# Aquí se hace la conexión con MySQL

# Cada rol se conecta con su propio usuario de MySQL:
#   login_app       solo puede leer la tabla login (para iniciar sesión)
#   admin_app       lee y escribe todo
#   planillero_app  lee todo, pero solo escribe planillas, goles y tarjetas

# Cuando la app intenta hacer algo que ese usuario no tiene permitido, se rechaza con error 1142 desde MySQL

import os
from contextlib import contextmanager

import pymysql

USUARIOS = {
    "login": ("login_app", "Login"),
    "admin": ("admin_app", "Admin"),
    "planillero": ("planillero_app", "Planillero"),
}


def conectar(como="admin"):
    # Abre una conexión con el usuario de MySQL que corresponda
    usuario, clave = USUARIOS[como]
    return pymysql.connect(
        host=os.environ.get("DB_HOST", "db"),
        user=usuario,
        password=clave,
        database=os.environ.get("DB_NAME", "torneo_f5"),
        cursorclass=pymysql.cursors.DictCursor,
        charset="utf8mb4",
    )


def usuario_para(rol):
    # Los administradores usan admin_app y los planilleros planillero_app
    return "admin" if rol == "administrador" else "planillero"


def consultar(consulta, params=None, como="admin"):
    # Para los SELECT, ejecuta la consulta y devuelve todas las filas
    conn = conectar(como)
    try:
        with conn.cursor() as cur:
            cur.execute(consulta, params or ())
            return cur.fetchall()
    finally:
        conn.close()


@contextmanager
def transaccion(como="admin"):
    # Para las escrituras, si todo sale bien hace commit y si algo falla hace rollback, así no queda nada guardado a medias. (Transaction)
    conn = conectar(como)
    try:
        with conn.cursor() as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

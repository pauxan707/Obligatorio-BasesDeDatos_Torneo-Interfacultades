import os
import pymysql
from flask import Flask

app = Flask(__name__)


def conectar():
    return pymysql.connect(
        host=os.environ.get("DB_HOST", "db"),
        user=os.environ.get("DB_USER", "admin_app"),
        password=os.environ.get("DB_PASSWORD", "Admin_Cambiar_123"),
        database=os.environ.get("DB_NAME", "torneo_f5"),
    )


@app.route("/")
def home():
    return "Torneo F5 funcionando"


@app.route("/salud")
def salud():
    # Prueba que la app llega a MySQL y que el esquema se cargó
    try:
        conn = conectar()
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM turno")
            turnos = cur.fetchone()[0]
        conn.close()
        return f"Conexión OK. Turnos cargados: {turnos}"
    except Exception as e:
        return f"Error de conexión: {e}", 500
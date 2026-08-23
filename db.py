import sqlite3
from pathlib import Path

# Directorio base del proyecto
BASE_DIR = Path(__file__).resolve().parent

# Conexión a la base de datos
conexion = sqlite3.connect(BASE_DIR / "Data" / "partidas.db")
cursor = conexion.cursor()

# Estado del mensaje de guardado
save_message = ""
save_message_timer = 0.0


def init_db():
    """Crea la tabla para guardar la posición del jugador si no existe."""
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS player_pos (
            id INTEGER PRIMARY KEY,
            x REAL,
            y REAL
        )"""
    )
    conexion.commit()


def save_player_pos(x, y):
    """Guarda la posición del jugador y activa el mensaje de confirmación."""
    cursor.execute("INSERT OR REPLACE INTO player_pos (id, x, y) VALUES (1, ?, ?)", (x, y))
    conexion.commit()
    global save_message, save_message_timer
    save_message = "Miau! Posición guardada!"
    save_message_timer = 1.5  # segundos visible


def cargar_partida():
    """Carga la última posición guardada del jugador desde la base de datos."""
    cursor.execute("SELECT x, y FROM player_pos WHERE id = 1")
    row = cursor.fetchone()
    if row:
        return (row[0], row[1])
    return None

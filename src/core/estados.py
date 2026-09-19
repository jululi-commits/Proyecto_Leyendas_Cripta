from enum import Enum


class EstadoJuego(str, Enum):
    """
    Enumeración que define las claves de estado disponibles para el GestorEscenas.
    """
    JUEGO = "juego"
    PAUSA = "pausa"
    GAME_OVER = "game_over"
    VICTORIA = "victoria"

    def __str__(self) -> str:
        return self.value
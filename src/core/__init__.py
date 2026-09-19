"""
Módulo core con la arquitectura base: GestorEscenas, EscenaBase, Estados.
"""
from .escena_base import EscenaBase
from .gestor_escenas import GestorEscenas
from .estados import EstadoJuego
from .entidades import EntidadBase, Jugador

__all__ = ["EscenaBase", "GestorEscenas", "EstadoJuego", "EntidadBase", "Jugador"]

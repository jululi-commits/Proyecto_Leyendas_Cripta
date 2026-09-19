from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, List

import pygame

if TYPE_CHECKING:
    from .gestor_escenas import GestorEscenas


class EscenaBase(ABC):
    """
    Clase base abstracta para todas las escenas del juego.
    
    Toda escena concreta debe heredar de esta clase e implementar los métodos:
    - actualizar(dt)
    - dibujar(pantalla)
    - manejar_eventos(eventos)
    """

    def __init__(self) -> None:
        self.gestor: "GestorEscenas | None" = None

    @abstractmethod
    def manejar_eventos(self, eventos: List[pygame.event.Event]) -> None:
        """
        Procesa la lista de eventos capturados por Pygame en el frame actual.
        
        :param eventos: Lista de objetos pygame.event.Event.
        """
        pass

    @abstractmethod
    def actualizar(self, dt: float) -> None:
        """
        Actualiza la lógica interna de la escena (temporizadores, física, estado).
        
        :param dt: Tiempo transcurrido desde el último frame en segundos (Delta Time).
        """
        pass

    @abstractmethod
    def dibujar(self, pantalla: pygame.Surface) -> None:
        """
        Renderiza los elementos visuales de la escena sobre la superficie dada.
        
        :param pantalla: Superficie de Pygame (pygame.Surface) correspondiente a la ventana.
        """
        pass

    def al_entrar(self, **kwargs: Any) -> None:
        """
        Hook opcional invocado automáticamente cuando la escena se vuelve activa.
        Permite recibir un diccionario de datos (kwargs) desde la escena anterior.
        
        :param kwargs: Datos transferidos entre escenas (ej. puntuación, modo, resultado).
        """
        pass

    def al_salir(self) -> None:
        """
        Hook opcional invocado automáticamente justo antes de abandonar esta escena.
        Útil para realizar limpieza, detener música o guardar estados temporales.
        """
        pass

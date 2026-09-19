from typing import Any, Dict, List, Optional, Union

import pygame

from .escena_base import EscenaBase
from .estados import EstadoJuego


class GestorEscenas:
    """
    Gestor principal de escenas y estados del juego (Patrón State).
    
    Mantiene un diccionario de estados/escenas disponibles y controla las
    transiciones entre ellas, delegando los eventos, la actualización por dt
    y el renderizado a la escena activa actual.
    """

    def __init__(self) -> None:
        # Diccionario de estados: mapea el nombre del estado (str) a la instancia de EscenaBase
        self._escenas: Dict[str, EscenaBase] = {}
        self._escena_actual: Optional[EscenaBase] = None
        self._nombre_estado_actual: Optional[str] = None

    @property
    def escena_actual(self) -> Optional[EscenaBase]:
        """Devuelve la escena activa actualmente."""
        return self._escena_actual

    @property
    def estado_actual(self) -> Optional[str]:
        """Devuelve el nombre del estado activo actualmente."""
        return self._nombre_estado_actual

    def agregar_escena(self, nombre: Union[str, EstadoJuego], escena: EscenaBase) -> None:
        """
        Registra una escena en el diccionario de estados del gestor.
        
        :param nombre: Identificador del estado (string o EstadoJuego enum).
        :param escena: Instancia concreta de la escena (subclase de EscenaBase).
        """
        clave = str(nombre)
        self._escenas[clave] = escena
        escena.gestor = self

    def obtener_escena(self, nombre: Union[str, EstadoJuego]) -> Optional[EscenaBase]:
        """
        Obtiene una escena registrada mediante su identificador.
        """
        return self._escenas.get(str(nombre))

    def cambiar_escena(self, nombre_estado: Union[str, EstadoJuego], **kwargs: Any) -> None:
        """
        Cambia el estado activo actual a la escena indicada por 'nombre_estado'.
        Permite enviar un diccionario de datos o argumentos arbitrarios (**kwargs)
        a la nueva escena mediante su método al_entrar(**kwargs).
        
        :param nombre_estado: Identificador de la escena destino (str o EstadoJuego).
        :param kwargs: Datos transferidos a la nueva escena (puntuación, modo, resultado, etc.).
        """
        clave = str(nombre_estado)

        if clave not in self._escenas:
            raise KeyError(
                f"[GestorEscenas Error] No se encontró la escena '{clave}'. "
                f"Escenas disponibles: {list(self._escenas.keys())}"
            )

        # 1. Ejecutar hook de salida de la escena actual si existe
        if self._escena_actual is not None:
            self._escena_actual.al_salir()

        # 2. Conmutar a la nueva escena
        self._nombre_estado_actual = clave
        self._escena_actual = self._escenas[clave]

        # 3. Ejecutar hook de entrada de la nueva escena pasando el diccionario kwargs
        self._escena_actual.al_entrar(**kwargs)

    def manejar_eventos(self, eventos: List[pygame.event.Event]) -> None:
        """
        Delega el procesamiento de eventos a la escena activa.
        """
        if self._escena_actual is not None:
            self._escena_actual.manejar_eventos(eventos)

    def actualizar(self, dt: float) -> None:
        """
        Delega la actualización lógica a la escena activa.
        
        :param dt: Delta Time en segundos.
        """
        if self._escena_actual is not None:
            self._escena_actual.actualizar(dt)

    def dibujar(self, pantalla: pygame.Surface) -> None:
        """
        Delega el renderizado gráfico a la escena activa.
        
        :param pantalla: Superficie principal de ventana de Pygame.
        """
        if self._escena_actual is not None:
            self._escena_actual.dibujar(pantalla)

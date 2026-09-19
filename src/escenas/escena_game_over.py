from typing import Any, List, Tuple

import pygame

from core.escena_base import EscenaBase
from core.estados import EstadoJuego


class EscenaGameOver(EscenaBase):
    """
    Escena de Fin de Juego (Victoria / Derrota).
    Muestra cómo la escena destino recibe y procesa los datos transferidos vía kwargs.
    """

    def __init__(self) -> None:
        super().__init__()
        self.resultado: str = "GAME OVER"
        self.causa: str = ""
        self.puntuacion: int = 0
        self.tiempo_segundos: int = 0
        self.fuente_titulo: pygame.font.Font | None = None
        self.fuente_texto: pygame.font.Font | None = None

    def al_entrar(self, **kwargs: Any) -> None:
        """
        Procesa el diccionario kwargs transferido desde la escena previa.
        """
        self.resultado = kwargs.get("resultado", "GAME OVER")
        self.causa = kwargs.get("causa", "")
        self.puntuacion = kwargs.get("puntuacion", 0)
        self.tiempo_segundos = kwargs.get("tiempo_segundos", 0)
       
        if not pygame.font.get_init():
            pygame.font.init()
        self.fuente_titulo = pygame.font.SysFont("Georgia", 48, bold=True)
        self.fuente_texto = pygame.font.SysFont("Arial", 22)

    def manejar_eventos(self, eventos: List[pygame.event.Event]) -> None:
        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                if evento.key in (pygame.K_SPACE, pygame.K_RETURN):
                    # Reiniciar partida
                    if self.gestor:
                        self.gestor.cambiar_escena(EstadoJuego.JUEGO)
                elif evento.key == pygame.K_ESCAPE:
                    # Volver al menú
                    if self.gestor:
                        self.gestor.cambiar_escena(EstadoJuego.MENU)

    def actualizar(self, dt: float) -> None:
        pass

    def dibujar(self, pantalla: pygame.Surface) -> None:
        # Fondo oscuro según resultado
        es_victoria = "VICTORIA" in self.resultado
        if es_victoria:
            color_fondo = (20, 45, 30)
            color_titulo = (240, 215, 100)
        else:
            color_fondo = (45, 20, 20)
            color_titulo = (240, 90, 90)

        pantalla.fill(color_fondo)
        ancho, alto = pantalla.get_size()

        if not self.fuente_titulo or not self.fuente_texto:
            return

        # Renderizar superficies de texto
        surf_titulo = self.fuente_titulo.render(self.resultado, True, color_titulo)

        surf_causa = None
        if self.causa:
            surf_causa = self.fuente_texto.render(self.causa, True, (220, 200, 200))
        
        lineas_stats = [
            f"Puntuación Final: {self.puntuacion}",
            f"Tiempo de Partida: {self.tiempo_segundos} segundos",
            tercera_stat,
        ]
        surfs_stats = [self.fuente_texto.render(linea, True, (230, 230, 230)) for linea in lineas_stats]

        surf_ctrl = self.fuente_texto.render(
            "[ ESPACIO ] Volver a Jugar   |   [ ESC ] Menú Principal",
            True,
            (255, 255, 255)
        )

        # Construir lista de (superficie, espaciado_inferior)
        elementos: List[Tuple[pygame.Surface, int]] = []
        elementos.append((surf_titulo, 30))

        if surf_causa:
            elementos.append((surf_causa, 25))

        for i, surf_stat in enumerate(surfs_stats):
            espaciado = 40 if i == len(surfs_stats) - 1 else 12
            elementos.append((surf_stat, espaciado))

        elementos.append((surf_ctrl, 0))

        # Calcular el alto total del bloque de texto
        alto_total = sum(surf.get_height() + espaciado for surf, espaciado in elementos)

        # Centrar verticalmente el bloque completo en la pantalla
        y_actual = (alto - alto_total) // 2

        # Dibujar cada elemento alineado al centro de la pantalla
        for surf, espaciado in elementos:
            rect = surf.get_rect(centerx=ancho // 2, top=y_actual)
            pantalla.blit(surf, rect)
            y_actual += surf.get_height() + espaciado
"""
Módulo de la escena del Menú Principal.

Define la clase EscenaMenu, que hereda de EscenaBase y proporciona
una interfaz de usuario interactiva con dos botones (BotonUi):
- "Jugar": Conmuta el estado del juego a la escena de juego.
- "Salir": Cierra y finaliza la aplicación de forma limpia.

Elementos visuales escalados (+50% general, +25% extra para texto de botones).
"""
from __future__ import annotations

import sys
from typing import List

import pygame

from core.escena_base import EscenaBase
from core.estados import EstadoJuego
from core.interfaz import BotonUi


class EscenaMenu(EscenaBase):
    """
    Escena del Menú Principal del juego.
    
    Hereda de EscenaBase y renderiza el título del juego y botones interactivos
    construidos mediante BotonUi con detección AABB.
    """

    def __init__(self) -> None:
        super().__init__()
        
        # Dimensiones y posicionamiento de los botones centrados (ventana base 1024x720)
        # Escalado +50%: ancho 240 -> 360, alto 55 -> 83
        ancho_boton = int(240 * 1.5)  # 360 px
        alto_boton = int(55 * 1.5)    # 83 px
        centro_x = 1024 // 2 - ancho_boton // 2

        # Texto de los botones escalado un 50% + 25% extra:
        # Base 24 -> +50% = 36 -> +25% extra = 45 px
        tamano_fuente_boton = int(24 * 1.5 * 1.25)  # 45 px
        grosor_borde_boton = int(2 * 1.5)            # 3 px

        # 1. Botón "Jugar"
        self.boton_jugar = BotonUi(
            x=centro_x,
            y=330,
            ancho=ancho_boton,
            alto=alto_boton,
            texto="Jugar",
            tamano_fuente=tamano_fuente_boton,
            grosor_borde=grosor_borde_boton,
        )

        # 2. Botón "Salir"
        self.boton_salir = BotonUi(
            x=centro_x,
            y=440,
            ancho=ancho_boton,
            alto=alto_boton,
            texto="Salir",
            tamano_fuente=tamano_fuente_boton,
            grosor_borde=grosor_borde_boton,
        )

        # Fuentes tipográficas pre-renderizadas (Escaladas +50%: 64->96, 26->39)
        self._fuente_titulo: pygame.font.Font | None = None
        self._fuente_subtitulo: pygame.font.Font | None = None

    def al_entrar(self, **kwargs) -> None:
        """Inicializa recursos tipográficos y reinicia estado al entrar al menú."""
        if not pygame.font.get_init():
            pygame.font.init()
            
        # Título escalado +50%: 64 * 1.5 = 96
        self._fuente_titulo = pygame.font.Font(None, int(64 * 1.5))
        # Subtítulo escalado +50%: 26 * 1.5 = 39
        self._fuente_subtitulo = pygame.font.Font(None, int(26 * 1.5))

    def manejar_eventos(self, eventos: List[pygame.event.Event]) -> None:
        """
        Procesa eventos del menú: clics del mouse sobre los botones AABB y teclas de acceso rápido.
        """
        for evento in eventos:
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                pos_mouse = evento.pos
                clic_izquierdo = True

                # Verificación del botón "Jugar" usando AABB
                if self.boton_jugar.comprobar_clic(pos_mouse, clic_izquierdo):
                    if self.gestor:
                        # Conmuta el estado a la escena de juego
                        if "escena_juego" in self.gestor._escenas:
                            self.gestor.cambiar_escena("escena_juego")
                        else:
                            self.gestor.cambiar_escena(EstadoJuego.JUEGO)
                    return

                # Verificación del botón "Salir" usando AABB
                elif self.boton_salir.comprobar_clic(pos_mouse, clic_izquierdo):
                    # Publica el evento QUIT para que el bucle principal cierre limpiamente
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
                    return

            elif evento.type == pygame.KEYDOWN:
                # Accesos directos por teclado (Enter para jugar, Escape para salir)
                if evento.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if self.gestor:
                        self.gestor.cambiar_escena(EstadoJuego.JUEGO)
                elif evento.key == pygame.K_ESCAPE:
                    pygame.event.post(pygame.event.Event(pygame.QUIT))

    def actualizar(self, dt: float) -> None:
        """Actualización de lógica y animaciones (si fueran necesarias)."""
        pass

    def dibujar(self, pantalla: pygame.Surface) -> None:
        """
        Renderiza el menú principal: fondo, título del juego y los botones interactivos.
        """
        ancho_pantalla = pantalla.get_width()
        alto_pantalla = pantalla.get_height()

        # Ajuste dinámico de posición horizontal en caso de pantallas redimensionadas
        ancho_boton = self.boton_jugar.ancho
        centro_x = (ancho_pantalla - ancho_boton) // 2
        self.boton_jugar.rect.x = centro_x
        self.boton_salir.rect.x = centro_x

        # 1. Fondo estilizado con paleta oscura atmosférica
        pantalla.fill((22, 24, 34))

        # 2. Renderizado del Título y Subtítulo con sombra para legibilidad (+50% de offset: 4px)
        if self._fuente_titulo:
            # Sombra del título
            surf_titulo_sombra = self._fuente_titulo.render("Gatito VS Los Fantasmas", True, (10, 10, 15))
            rect_titulo_sombra = surf_titulo_sombra.get_rect(center=(ancho_pantalla // 2 + 4, 154))
            pantalla.blit(surf_titulo_sombra, rect_titulo_sombra)

            # Texto del título principal
            surf_titulo = self._fuente_titulo.render("Gatito VS Los Fantasmas", True, (240, 245, 255))
            rect_titulo = surf_titulo.get_rect(center=(ancho_pantalla // 2, 150))
            pantalla.blit(surf_titulo, rect_titulo)

        if self._fuente_subtitulo:
            surf_sub = self._fuente_subtitulo.render("Proyecto Leyendas de la Cripta", True, (140, 160, 190))
            rect_sub = surf_sub.get_rect(center=(ancho_pantalla // 2, 225))
            pantalla.blit(surf_sub, rect_sub)

        # 3. Dibujar botones con estado de Hover / Active
        pos_mouse = pygame.mouse.get_pos()
        clic_presionado = pygame.mouse.get_pressed()[0]

        self.boton_jugar.dibujar(pantalla, pos_mouse, clic_presionado)
        self.boton_salir.dibujar(pantalla, pos_mouse, clic_presionado)

"""
Módulo de Interfaz de Usuario (HUD) para el motor de videojuegos 2D.

Proporciona la clase GestorUi que dibuja los elementos del HUD con coordenadas
absolutas en la superficie de la pantalla, independientes de cualquier cámara
o transformación de mundo. Debe invocarse al final del ciclo de renderizado
(después de dibujar todas las entidades del juego).

Principio matemático central — Regla de Tres Simple:
    Si salud_max corresponde a barra_largo_px (100 % de la barra),
    entonces salud_actual corresponde a X píxeles.

    X = (salud_actual × barra_largo_px) / salud_max

Autor: Programador UI/UX Senior
"""
from __future__ import annotations

from typing import Tuple

import pygame


class GestorUi:
    """
    Gestor de Interfaz de Usuario (HUD) para el motor 2D.

    Dibuja elementos superpuestos en coordenadas absolutas de pantalla,
    desacoplados de la cámara del juego. Optimizado para ser invocado
    una sola vez al final de cada frame de renderizado.

    Elementos disponibles:
        - Barra de salud con fondo, relleno dinámico y borde.
        - Indicador de puntaje con texto y sombra de legibilidad.

    Ejemplo de uso::

        gestor_ui = GestorUi()
        # ... dentro del ciclo de renderizado, DESPUÉS de dibujar entidades:
        gestor_ui.dibujar_hud(pantalla, salud_actual=75, salud_max=100, puntaje=1250)
    """

    # =========================================================================
    # Constantes de Diseño Visual (tokens de diseño centralizados)
    # =========================================================================

    # --- Dimensiones de la barra de salud (en píxeles absolutos) ---
    BARRA_X: int = 20                     # Posición X (esquina superior izquierda)
    BARRA_Y: int = 20                     # Posición Y (esquina superior izquierda)
    BARRA_LARGO_PX: int = 250             # Longitud máxima de la barra (100 % salud)
    BARRA_ALTO_PX: int = 28              # Altura de la barra

    # --- Paleta de colores (RGB) ---
    COLOR_BARRA_FONDO: Tuple[int, int, int] = (40, 40, 50)       # Fondo oscuro de la barra
    COLOR_BARRA_BORDE: Tuple[int, int, int] = (180, 190, 210)    # Borde sutil
    COLOR_SALUD_ALTA: Tuple[int, int, int] = (50, 205, 100)      # Verde vivo (> 50 %)
    COLOR_SALUD_MEDIA: Tuple[int, int, int] = (240, 180, 40)     # Amarillo ámbar (25 %–50 %)
    COLOR_SALUD_BAJA: Tuple[int, int, int] = (220, 50, 50)       # Rojo intenso (< 25 %)
    COLOR_TEXTO: Tuple[int, int, int] = (255, 255, 255)           # Blanco para texto principal
    COLOR_SOMBRA_TEXTO: Tuple[int, int, int] = (0, 0, 0)         # Negro para sombra del texto

    # --- Tipografía ---
    FUENTE_TAMANO: int = 22                # Tamaño en puntos para la fuente del HUD
    FUENTE_TAMANO_ETIQUETA: int = 16       # Tamaño para la etiqueta de la barra

    # --- Márgenes y offsets ---
    SOMBRA_OFFSET: int = 2                 # Desplazamiento de la sombra del texto (px)
    MARGEN_PUNTAJE_DERECHA: int = 20       # Margen derecho del puntaje

    def __init__(self) -> None:
        """
        Inicializa el gestor de interfaz precargando las fuentes de Pygame.

        Las fuentes se crean una sola vez en el constructor para evitar
        instanciar objetos de fuente en cada frame (optimización de rendimiento).
        """
        # Precarga de fuentes del sistema (None = fuente por defecto de Pygame)
        self._fuente: pygame.font.Font = pygame.font.Font(None, self.FUENTE_TAMANO)
        self._fuente_etiqueta: pygame.font.Font = pygame.font.Font(None, self.FUENTE_TAMANO_ETIQUETA)

    # =========================================================================
    # Método Público Principal
    # =========================================================================

    def dibujar_hud(
        self,
        pantalla: pygame.Surface,
        salud_actual: float,
        salud_max: float,
        puntaje: int,
    ) -> None:
        """
        Dibuja el HUD completo sobre la pantalla en coordenadas absolutas.

        Este método debe llamarse al FINAL del ciclo de renderizado, después
        de dibujar todas las entidades del juego, para que el HUD se superponga
        a los gráficos del mundo sin ser afectado por la cámara.

        :param pantalla: Superficie principal de Pygame (pygame.display).
        :param salud_actual: Puntos de vida actuales del jugador (>= 0).
        :param salud_max: Puntos de vida máximos del jugador (> 0).
        :param puntaje: Puntaje numérico actual del jugador.
        """
        self._dibujar_barra_salud(pantalla, salud_actual, salud_max)
        self._dibujar_puntaje(pantalla, puntaje)

    # =========================================================================
    # Métodos Privados de Renderizado
    # =========================================================================

    def _dibujar_barra_salud(
        self,
        pantalla: pygame.Surface,
        salud_actual: float,
        salud_max: float,
    ) -> None:
        """
        Renderiza la barra de salud con fondo, relleno proporcional y borde.

        Cálculo de la longitud del relleno — Regla de Tres Simple:
        ──────────────────────────────────────────────────────────
        Si:   salud_max    → BARRA_LARGO_PX   (la barra completa)
        Entonces: salud_actual → X  píxeles

        Despejando:
            X = (salud_actual × BARRA_LARGO_PX) / salud_max

        Esto garantiza que el relleno es directamente proporcional al
        porcentaje de salud restante sin depender de constantes mágicas.

        :param pantalla: Superficie de destino.
        :param salud_actual: Vida actual (valor numérico >= 0).
        :param salud_max: Vida máxima (valor numérico > 0).
        """
        # ── Protección contra división por cero ──
        if salud_max <= 0:
            return

        # ── Clampeo: asegurar que salud_actual ∈ [0, salud_max] ──
        salud_actual = max(0.0, min(float(salud_actual), float(salud_max)))

        # ══════════════════════════════════════════════════════════════
        # REGLA DE TRES SIMPLE para obtener los píxeles de relleno:
        #
        #   salud_max   ──────►  BARRA_LARGO_PX  (píxeles totales)
        #   salud_actual ──────►  largo_relleno   (píxeles proporcionales)
        #
        #   largo_relleno = (salud_actual × BARRA_LARGO_PX) / salud_max
        # ══════════════════════════════════════════════════════════════
        largo_relleno: int = int(
            (salud_actual * self.BARRA_LARGO_PX) / salud_max
        )

        # ── Cálculo del porcentaje normalizado [0.0, 1.0] para el color ──
        porcentaje: float = salud_actual / salud_max

        # ── Selección del color según umbrales de salud ──
        color_relleno = self._obtener_color_salud(porcentaje)

        # ── 1. Fondo de la barra (rectángulo oscuro completo) ──
        rect_fondo = pygame.Rect(
            self.BARRA_X, self.BARRA_Y,
            self.BARRA_LARGO_PX, self.BARRA_ALTO_PX,
        )
        pygame.draw.rect(pantalla, self.COLOR_BARRA_FONDO, rect_fondo)

        # ── 2. Relleno proporcional a la salud actual ──
        if largo_relleno > 0:
            rect_relleno = pygame.Rect(
                self.BARRA_X, self.BARRA_Y,
                largo_relleno, self.BARRA_ALTO_PX,
            )
            pygame.draw.rect(pantalla, color_relleno, rect_relleno)

        # ── 3. Borde exterior de la barra (estética premium) ──
        pygame.draw.rect(pantalla, self.COLOR_BARRA_BORDE, rect_fondo, width=2)

        # ── 4. Etiqueta textual centrada dentro de la barra ("75 / 100") ──
        texto_salud = f"{int(salud_actual)} / {int(salud_max)}"
        self._dibujar_texto_con_sombra(
            pantalla,
            texto_salud,
            self._fuente_etiqueta,
            self.COLOR_TEXTO,
            rect_fondo.centerx,
            rect_fondo.centery,
            centrado=True,
        )

    def _dibujar_puntaje(
        self,
        pantalla: pygame.Surface,
        puntaje: int,
    ) -> None:
        """
        Renderiza el texto del puntaje en la esquina superior derecha de la pantalla.

        Se posiciona usando coordenadas absolutas relativas al ancho de la pantalla,
        independiente de la cámara o del espacio del mundo.

        :param pantalla: Superficie de destino.
        :param puntaje: Valor numérico del puntaje a mostrar.
        """
        ancho_pantalla: int = pantalla.get_width()

        texto_puntaje = f"Puntaje: {puntaje}"

        # Posición X: alineado a la derecha con margen
        superficie_texto = self._fuente.render(texto_puntaje, True, self.COLOR_TEXTO)
        pos_x: int = ancho_pantalla - superficie_texto.get_width() - self.MARGEN_PUNTAJE_DERECHA
        pos_y: int = self.BARRA_Y  # Misma línea vertical que la barra de salud

        self._dibujar_texto_con_sombra(
            pantalla,
            texto_puntaje,
            self._fuente,
            self.COLOR_TEXTO,
            pos_x,
            pos_y,
            centrado=False,
        )

    # =========================================================================
    # Utilidades Internas
    # =========================================================================

    def _obtener_color_salud(
        self,
        porcentaje: float,
    ) -> Tuple[int, int, int]:
        """
        Determina el color de la barra según el porcentaje de salud.

        Umbrales:
            - > 50 %  → Verde vivo (estado saludable).
            - 25–50 % → Amarillo ámbar (precaución).
            - < 25 %  → Rojo intenso (peligro crítico).

        :param porcentaje: Fracción de salud en [0.0, 1.0].
        :return: Tupla RGB del color correspondiente.
        """
        if porcentaje > 0.50:
            return self.COLOR_SALUD_ALTA
        elif porcentaje > 0.25:
            return self.COLOR_SALUD_MEDIA
        else:
            return self.COLOR_SALUD_BAJA

    def _dibujar_texto_con_sombra(
        self,
        pantalla: pygame.Surface,
        texto: str,
        fuente: pygame.font.Font,
        color: Tuple[int, int, int],
        x: int,
        y: int,
        centrado: bool = False,
    ) -> None:
        """
        Renderiza un texto con una sombra proyectada para mejorar la legibilidad
        sobre cualquier fondo del juego.

        La sombra se dibuja primero (capa inferior), desplazada SOMBRA_OFFSET
        píxeles en ambos ejes, y luego se dibuja el texto principal encima.

        :param pantalla: Superficie de destino.
        :param texto: Cadena de texto a renderizar.
        :param fuente: Instancia de pygame.font.Font a utilizar.
        :param color: Color RGB del texto principal.
        :param x: Coordenada X de posicionamiento.
        :param y: Coordenada Y de posicionamiento.
        :param centrado: Si True, (x, y) es el centro; si False, es la esquina superior izquierda.
        """
        # Renderizado de la superficie de sombra y del texto principal (una sola vez cada uno)
        superficie_sombra = fuente.render(texto, True, self.COLOR_SOMBRA_TEXTO)
        superficie_texto = fuente.render(texto, True, color)

        if centrado:
            # Posicionamiento centrado: se usa el centro del rectángulo del texto
            rect_sombra = superficie_sombra.get_rect(
                center=(x + self.SOMBRA_OFFSET, y + self.SOMBRA_OFFSET)
            )
            rect_texto = superficie_texto.get_rect(center=(x, y))
        else:
            # Posicionamiento por esquina superior izquierda
            rect_sombra = superficie_sombra.get_rect(
                topleft=(x + self.SOMBRA_OFFSET, y + self.SOMBRA_OFFSET)
            )
            rect_texto = superficie_texto.get_rect(topleft=(x, y))

        # Capa 1: Sombra (fondo)
        pantalla.blit(superficie_sombra, rect_sombra)
        # Capa 2: Texto principal (primer plano)
        pantalla.blit(superficie_texto, rect_texto)


class BotonUi:
    """
    Componente de botón interactivo para la interfaz de usuario (UI).

    Permite instanciar un botón rectangular con coordenadas en pantalla,
    dimensiones (ancho, alto), texto centrado y detección de colisión/clic
    mediante el algoritmo AABB (Axis-Aligned Bounding Box) punto vs rectángulo.

    Algoritmo AABB (Punto en Rectángulo):
        Para un punto de entrada Mouse(x, y) y un rectángulo delimitado por
        (left, right, top, bottom):
            colision = (Mouse_X >= Box_Left) AND (Mouse_X <= Box_Right) AND
                       (Mouse_Y >= Box_Top)  AND (Mouse_Y <= Box_Bottom)
    """

    # =========================================================================
    # Tokens de Diseño Visual (Constantes de Estilo)
    # =========================================================================
    COLOR_FONDO: Tuple[int, int, int] = (45, 52, 71)             # Azul grisáceo oscuro
    COLOR_FONDO_HOVER: Tuple[int, int, int] = (68, 85, 120)      # Acento interactivo (hover)
    COLOR_FONDO_CLICK: Tuple[int, int, int] = (30, 36, 50)       # Presionado
    COLOR_BORDE: Tuple[int, int, int] = (140, 160, 200)          # Borde sutil
    COLOR_BORDE_HOVER: Tuple[int, int, int] = (200, 220, 255)    # Borde iluminado
    COLOR_TEXTO: Tuple[int, int, int] = (240, 245, 255)          # Blanco con matiz suave
    COLOR_SOMBRA_TEXTO: Tuple[int, int, int] = (15, 15, 20)      # Sombra para contraste

    FUENTE_TAMANO: int = 24
    BORDE_GROSOR: int = 2
    SOMBRA_OFFSET: int = 1

    def __init__(
        self,
        x: int | Tuple[int, int],
        y: int | Tuple[int, int] | None = None,
        ancho: int | str = 0,
        alto: int | None = None,
        texto: str = "",
        tamano_fuente: int | None = None,
        grosor_borde: int | None = None,
    ) -> None:
        """
        Inicializa una nueva instancia de BotonUi.

        Soporta dos firmas de llamada para máxima compatibilidad:
        1. Separada: BotonUi(x=100, y=200, ancho=180, alto=45, texto="Jugar")
        2. Agrupada: BotonUi(posicion=(100, 200), dimensiones=(180, 45), texto="Jugar")

        :param x: Posición X inicial en pixeles, o tupla (x, y).
        :param y: Posición Y inicial en pixeles, o tupla (ancho, alto) si x fue tupla.
        :param ancho: Ancho en pixeles, o texto si se pasaron tuplas.
        :param alto: Alto en pixeles (opcional según la forma de llamada).
        :param texto: Texto a mostrar en el centro del botón.
        :param tamano_fuente: Tamaño opcional de la tipografía del botón.
        :param grosor_borde: Grosor opcional en píxeles del borde.
        """
        # Desempaquetado polimórfico flexible
        if isinstance(x, (tuple, list)):
            self.x: int = int(x[0])
            self.y: int = int(x[1])
            if isinstance(y, (tuple, list)):
                self.ancho: int = int(y[0])
                self.alto: int = int(y[1])
                self.texto: str = str(ancho)
            else:
                self.ancho: int = int(ancho) if isinstance(ancho, (int, float)) else 150
                self.alto: int = int(alto) if alto is not None else 40
                self.texto: str = str(texto)
        else:
            self.x = int(x)
            self.y = int(y) if y is not None else 0
            self.ancho = int(ancho) if isinstance(ancho, (int, float)) else 150
            self.alto = int(alto) if alto is not None else 40
            self.texto = str(texto)

        # Rectángulo matemático AABB (Axis-Aligned Bounding Box)
        self.rect: pygame.Rect = pygame.Rect(self.x, self.y, self.ancho, self.alto)

        # Configuración tipográfica y de estilo
        self.tamano_fuente: int = tamano_fuente if tamano_fuente is not None else self.FUENTE_TAMANO
        self.grosor_borde: int = grosor_borde if grosor_borde is not None else self.BORDE_GROSOR

        # Precarga y caché de fuentes para rendimiento óptimo
        self._fuente: pygame.font.Font = pygame.font.Font(None, self.tamano_fuente)
        self._superficie_texto: pygame.Surface = self._fuente.render(self.texto, True, self.COLOR_TEXTO)
        self._superficie_sombra: pygame.Surface = self._fuente.render(self.texto, True, self.COLOR_SOMBRA_TEXTO)

    def punto_en_aabb(self, punto: Tuple[int, int]) -> bool:
        """
        Aplica el algoritmo de colisión AABB (Axis-Aligned Bounding Box) para
        comprobar si un punto (ej. el cursor) está dentro de los límites del rectángulo.

        Fórmula matemática AABB:
            - Eje X: punto.x >= rect.left AND punto.x <= rect.right
            - Eje Y: punto.y >= rect.top  AND punto.y <= rect.bottom

        :param punto: Tupla de coordenadas (mouse_x, mouse_y).
        :return: True si el punto está dentro del AABB, False en caso contrario.
        """
        px, py = punto

        # Comprobación estricta de límites AABB
        colision_x: bool = (px >= self.rect.left) and (px <= self.rect.right)
        colision_y: bool = (py >= self.rect.top) and (py <= self.rect.bottom)

        return colision_x and colision_y

    def comprobar_clic(
        self,
        posicion_mouse: Tuple[int, int],
        clic_izquierdo: bool,
    ) -> bool:
        """
        Verifica si el usuario hizo clic izquierdo sobre el botón utilizando AABB.

        :param posicion_mouse: Tupla (x, y) con la posición absoluta del cursor.
        :param clic_izquierdo: Booleano que indica si el botón principal (izquierdo)
                               del ratón está presionado.
        :return: True si se presionó clic izquierdo dentro de la caja AABB, False si no.
        """
        # Si no hubo clic, no se activa la acción
        if not clic_izquierdo:
            return False

        # Verificación mediante algoritmo AABB
        return self.punto_en_aabb(posicion_mouse)

    def dibujar(
        self,
        pantalla: pygame.Surface,
        posicion_mouse: Tuple[int, int] | None = None,
        clic_presionado: bool = False,
    ) -> None:
        """
        Renderiza el botón en coordenadas absolutas de pantalla con estados interactivos (Hover / Active).

        :param pantalla: Superficie de Pygame donde se dibuja el botón.
        :param posicion_mouse: Coordenadas actuales del mouse para evaluar hover.
        :param clic_presionado: Si el botón izquierdo está actualmente presionado.
        """
        # Detección de estado Hover mediante AABB
        hover = False
        if posicion_mouse is not None:
            hover = self.punto_en_aabb(posicion_mouse)

        # Selección dinámica de estilos visuales
        if hover and clic_presionado:
            color_fondo = self.COLOR_FONDO_CLICK
            color_borde = self.COLOR_BORDE_HOVER
        elif hover:
            color_fondo = self.COLOR_FONDO_HOVER
            color_borde = self.COLOR_BORDE_HOVER
        else:
            color_fondo = self.COLOR_FONDO
            color_borde = self.COLOR_BORDE

        # 1. Fondo del botón
        pygame.draw.rect(pantalla, color_fondo, self.rect)

        # 2. Borde del botón
        pygame.draw.rect(pantalla, color_borde, self.rect, width=self.grosor_borde)

        # 3. Texto centrado con sombra
        rect_sombra = self._superficie_sombra.get_rect(
            center=(self.rect.centerx + self.SOMBRA_OFFSET, self.rect.centery + self.SOMBRA_OFFSET)
        )
        rect_texto = self._superficie_texto.get_rect(center=self.rect.center)

        pantalla.blit(self._superficie_sombra, rect_sombra)
        pantalla.blit(self._superficie_texto, rect_texto)

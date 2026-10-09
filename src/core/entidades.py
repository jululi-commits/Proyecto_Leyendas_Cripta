"""
Módulo de entidades para el motor de videojuegos 2D (Core).

Define la clase base EntidadBase y subclases como Jugador, con soporte para:
- Coordenadas centrales en coma flotante (subpíxel).
- Vectores de velocidad (vx, vy) independientes de los FPS.
- Procesamiento y actualización con Delta Time (dt).
- Aceleración por gravedad constante (g).
- Captura de teclas (Izquierda/Derecha, A/D) para el vector Vx.
- Rectángulo matemático de colisión (Hitbox).
- Renderizado y depuración en pantalla.
"""
from __future__ import annotations
import math
from typing import Any, Callable, Dict, List, Optional, Tuple
import pygame

class ComponenteSalud:
    """
    Componente de salud independiente para entidades del motor 2D.

    Siguiendo el principio de Composición sobre Herencia (Composition over Inheritance),
    este componente puede adjuntarse a cualquier entidad sin necesidad de herencia,
    manteniendo la lógica de salud completamente desacoplada de la lógica de movimiento,
    renderizado o cualquier otra responsabilidad de la entidad.

    Garantías matemáticas:
    - La vida actual siempre se mantiene en el rango cerrado [0, vida_maxima].
    - El daño y la curación nunca producen valores fuera de ese rango.
    - La vida máxima debe ser estrictamente positiva (> 0).

    Ejemplo de uso::

        salud = ComponenteSalud(vida_maxima=100)
        salud.recibir_daño(30)       # vida_actual → 70
        salud.curar(10)              # vida_actual → 80
        salud.esta_vivo()            # True
        salud.porcentaje()           # 0.80
        salud.recibir_daño(200)      # vida_actual → 0  (clampeo)
        salud.esta_vivo()            # False
    """

    def __init__(
        self,
        vida_maxima: float,
        vida_actual: Optional[float] = None,
    ) -> None:
        """
        Inicializa el componente de salud con una vida máxima definida.

        :param vida_maxima: Cantidad máxima de puntos de vida. Debe ser > 0.
        :param vida_actual: Vida inicial. Si es None, se establece igual a vida_maxima.
        :raises ValueError: Si vida_maxima no es estrictamente positiva.
        :raises ValueError: Si vida_actual es negativa o supera vida_maxima.
        """
        if vida_maxima <= 0:
            raise ValueError(
                f"vida_maxima debe ser un valor estrictamente positivo. "
                f"Se recibió: {vida_maxima}"
            )

        self._vida_maxima: float = float(vida_maxima)

        if vida_actual is None:
            self._vida_actual: float = self._vida_maxima
        else:
            if vida_actual < 0 or vida_actual > vida_maxima:
                raise ValueError(
                    f"vida_actual debe estar en el rango [0, {vida_maxima}]. "
                    f"Se recibió: {vida_actual}"
                )
            self._vida_actual = float(vida_actual)

    # =========================================================================
    # Propiedades de Solo Lectura
    # =========================================================================

    @property
    def vida_actual(self) -> float:
        """Obtiene los puntos de vida actuales (siempre en [0, vida_maxima])."""
        return self._vida_actual

    @property
    def vida_maxima(self) -> float:
        """Obtiene los puntos de vida máximos del componente."""
        return self._vida_maxima

    # =========================================================================
    # Métodos Matemáticos de Modificación de Salud
    # =========================================================================

    def recibir_daño(self, cantidad: float) -> float:
        """
        Resta una cantidad de puntos de vida, con clampeo al límite inferior (0).

        Si la cantidad de daño supera la vida actual, la vida queda en 0
        sin producir valores negativos.

        :param cantidad: Puntos de daño a restar. Debe ser >= 0.
        :return: Daño real aplicado (puede ser menor que 'cantidad' si la vida era baja).
        :raises ValueError: Si la cantidad es negativa (usar curar() para recuperar vida).
        """
        if cantidad < 0:
            raise ValueError(
                f"La cantidad de daño no puede ser negativa. "
                f"Usa curar() para recuperar vida. Se recibió: {cantidad}"
            )

        daño_real: float = min(cantidad, self._vida_actual)
        self._vida_actual = max(0.0, self._vida_actual - cantidad)
        return daño_real

    def curar(self, cantidad: float) -> float:
        """
        Suma una cantidad de puntos de vida, con clampeo al límite superior (vida_maxima).

        Si la curación supera la vida máxima, la vida queda en vida_maxima
        sin producir valores por encima del máximo permitido.

        :param cantidad: Puntos de vida a recuperar. Debe ser >= 0.
        :return: Curación real aplicada (puede ser menor que 'cantidad' si la vida estaba llena).
        :raises ValueError: Si la cantidad es negativa (usar recibir_daño() para quitar vida).
        """
        if cantidad < 0:
            raise ValueError(
                f"La cantidad de curación no puede ser negativa. "
                f"Usa recibir_daño() para reducir la vida. Se recibió: {cantidad}"
            )

        espacio_disponible: float = self._vida_maxima - self._vida_actual
        curación_real: float = min(cantidad, espacio_disponible)
        self._vida_actual = min(self._vida_maxima, self._vida_actual + cantidad)
        return curación_real

    def establecer_vida(self, cantidad: float) -> None:
        """
        Fija la vida actual en un valor específico, respetando los límites [0, vida_maxima].

        Útil para sincronizar el estado de salud desde una base de datos o guardado.

        :param cantidad: Nuevo valor de vida actual.
        :raises ValueError: Si la cantidad está fuera del rango [0, vida_maxima].
        """
        if cantidad < 0 or cantidad > self._vida_maxima:
            raise ValueError(
                f"La vida debe estar en el rango [0, {self._vida_maxima}]. "
                f"Se recibió: {cantidad}"
            )
        self._vida_actual = float(cantidad)

    def reiniciar(self) -> None:
        """Restaura la vida actual a su valor máximo (vida_maxima)."""
        self._vida_actual = self._vida_maxima

    # =========================================================================
    # Métodos de Consulta de Estado
    # =========================================================================

    def esta_vivo(self) -> bool:
        """
        Verifica si la entidad sigue con vida.

        :return: True si la vida actual es estrictamente mayor que 0, False en caso contrario.
        """
        return self._vida_actual > 0.0

    def esta_llena(self) -> bool:
        """
        Verifica si la vida actual es igual a la vida máxima.

        :return: True si la entidad tiene la vida al máximo, False en caso contrario.
        """
        return self._vida_actual >= self._vida_maxima

    def porcentaje(self) -> float:
        """
        Calcula el porcentaje de vida restante en el rango [0.0, 1.0].

        Ideal para alimentar barras de vida (HUD) sin acoplar lógica de UI al componente.

        :return: Valor flotante en [0.0, 1.0] representando la fracción de vida actual.

        Ejemplo::

            salud = ComponenteSalud(100)
            salud.recibir_daño(25)
            salud.porcentaje()  # → 0.75
        """
        return self._vida_actual / self._vida_maxima

    def vida_faltante(self) -> float:
        """
        Calcula cuántos puntos de vida faltan para llegar al máximo.

        :return: Diferencia entre vida_maxima y vida_actual (siempre >= 0).
        """
        return self._vida_maxima - self._vida_actual

    # =========================================================================
    # Representación de la Instancia
    # =========================================================================

    def __repr__(self) -> str:
        return (
            f"<ComponenteSalud vida={self._vida_actual:.1f}/{self._vida_maxima:.1f} "
            f"({self.porcentaje() * 100:.1f}%) vivo={self.esta_vivo()}>"
        )


class EntidadBase(pygame.sprite.Sprite):
    """
    Clase padre para todos los actores y objetos dinámicos del motor 2D.

    Diseñada siguiendo las mejores prácticas de ingeniería de software para motores de juegos:
    - Precisión subpíxel: Las coordenadas centrales (x, y) se almacenan como floats para
      evitar truncamientos numéricos al multiplicar por Delta Time (dt).
    - Desacoplamiento lógico-espacial: Mantiene coordenadas internas precisas y sincroniza
      la Hitbox matemática (pygame.Rect) y el rectángulo gráfico (rect).
    - Control de movimiento: Permite capturar teclas (Flechas y A/D) para modificar Vx.
    - Compatibilidad: Hereda de pygame.sprite.Sprite, permitiendo integración directa con
      grupos de sprites (pygame.sprite.Group) y funciones de colisión estándar.
    """

    def __init__(
        self,
        x: float,
        y: float,
        ancho: int = 32,
        alto: int = 32,
        vx: float = 0.0,
        vy: float = 0.0,
        gravedad: float = 0.0,
        velocidad_movimiento: float = 200.0,
        fuerza_salto: float = 480.0,
        controlar_con_teclado: bool = False,
        imagen: Optional[pygame.Surface] = None,
        color: Tuple[int, int, int] = (255, 255, 255),
        hitbox_ancho: Optional[int] = None,
        hitbox_alto: Optional[int] = None,
        offset_visual_x: float = 0.0,
        offset_visual_y: float = 0.0,
    ) -> None:
        """
        Inicializa una nueva instancia de EntidadBase.

        :param x: Coordenada X del centro de la entidad (float para subpíxel).
        :param y: Coordenada Y del centro de la entidad (float para subpíxel).
        :param ancho: Ancho visual de la entidad en píxeles.
        :param alto: Alto visual de la entidad en píxeles.
        :param vx: Velocidad inicial en el eje X (píxeles por segundo).
        :param vy: Velocidad inicial en el eje Y (píxeles por segundo).
        :param gravedad: Aceleración gravitatoria hacia abajo (g, px/s^2).
        :param velocidad_movimiento: Rapidez de desplazamiento horizontal al presionar teclas (px/s).
        :param fuerza_salto: Rapidez del impulso vertical hacia arriba al saltar (px/s).
        :param controlar_con_teclado: Si es True, captura automáticamente el teclado en actualizar(dt).
        :param imagen: Superficie gráfica opcional (pygame.Surface).
        :param color: Color RGB representativo si no se asigna imagen.
        :param hitbox_ancho: Ancho físico de la hitbox (si es None, se usa ancho).
        :param hitbox_alto: Alto físico de la hitbox (si es None, se usa alto).
        :param offset_visual_y: Ajuste vertical fino entre el rect visual y la hitbox.
                                Un valor positivo baja el sprite respecto a la hitbox.
        :param offset_visual_x: Ajuste horizontal fino entre el rect visual y la hitbox.
                                Un valor positivo desplaza el sprite hacia la derecha.
        """
        super().__init__()

        # Coordenadas centrales con precisión flotante (evita pérdidas de precisión con dt)
        self._x: float = float(x)
        self._y: float = float(y)

        # Dimensiones visuales de la entidad
        self.ancho: int = int(ancho)
        self.alto: int = int(alto)

        # Dimensiones físicas del hitbox (desacopladas del sprite visual)
        self.hitbox_ancho: int = int(hitbox_ancho) if hitbox_ancho is not None else self.ancho
        self.hitbox_alto: int = int(hitbox_alto) if hitbox_alto is not None else self.alto
        self.offset_visual_y: float = float(offset_visual_y)
        self.offset_visual_x: float = float(offset_visual_x)

        # Velocidad vectorial en píxeles por segundo (px/s)
        self.vx: float = float(vx)
        self.vy: float = float(vy)

        # Aceleración de gravedad (g en px/s^2)
        self.gravedad: float = float(gravedad)

        # Configuración de movimiento y control por teclado
        self.velocidad_movimiento: float = float(velocidad_movimiento)
        self.fuerza_salto: float = float(fuerza_salto)
        self.controlar_con_teclado: bool = controlar_con_teclado
        self.orientacion: str = "derecha"

        # Superficies gráficas y soporte para espejado de orientación
        self.imagen_derecha: Optional[pygame.Surface] = imagen
        self.imagen_izquierda: Optional[pygame.Surface] = (
            pygame.transform.flip(imagen, True, False) if imagen is not None else None
        )
        self.image: Optional[pygame.Surface] = (
            self.imagen_izquierda if self.orientacion == "izquierda" else self.imagen_derecha
        )
        self.color: Tuple[int, int, int] = color

        # Rectángulo visual (rect)
        if self.image is not None:
            self.rect: pygame.Rect = self.image.get_rect(center=(round(self._x), round(self._y)))
            self.ancho = self.rect.width
            self.alto = self.rect.height
        else:
            self.rect = pygame.Rect(0, 0, self.ancho, self.alto)
            self.rect.center = (round(self._x), round(self._y))

        # Rectángulo matemático de colisiones (Hitbox física desacoplada)
        self.hitbox: pygame.Rect = pygame.Rect(0, 0, self.hitbox_ancho, self.hitbox_alto)
        self.sincronizar_hitbox()

        # Flags de control de estado del ciclo de vida y física
        self.activa: bool = True
        self.viva: bool = True
        self.en_suelo: bool = False

        # Temporizador de invulnerabilidad (tiempo de gracia tras recibir daño)
        self.temporizador_invulnerable: float = 0.0
        self.duracion_invulnerabilidad: float = 1.0

    # =========================================================================
    # Propiedades para Coordenadas Centrales (x, y) y Parámetros Físicos
    # =========================================================================

    @property
    def x(self) -> float:
        """Obtiene la coordenada central X de la entidad."""
        return self._x

    @x.setter
    def x(self, valor: float) -> None:
        """Establece la coordenada central X y sincroniza la hitbox."""
        self._x = float(valor)
        self.sincronizar_hitbox()

    @property
    def y(self) -> float:
        """Obtiene la coordenada central Y de la entidad."""
        return self._y

    @y.setter
    def y(self, valor: float) -> None:
        """Establece la coordenada central Y y sincroniza la hitbox."""
        self._y = float(valor)
        self.sincronizar_hitbox()

    @property
    def centro(self) -> Tuple[float, float]:
        """Obtiene una tupla (x, y) con las coordenadas centrales actuales."""
        return (self._x, self._y)

    @centro.setter
    def centro(self, posicion: Tuple[float, float]) -> None:
        """Establece las coordenadas centrales (x, y) y sincroniza la hitbox."""
        self._x = float(posicion[0])
        self._y = float(posicion[1])
        self.sincronizar_hitbox()

    @property
    def g(self) -> float:
        """Obtiene la aceleración de gravedad (g)."""
        return self.gravedad

    @g.setter
    def g(self, valor: float) -> None:
        """Establece la aceleración de gravedad (g)."""
        self.gravedad = float(valor)

    # =========================================================================
    # Captura de Teclas y Entrada de Usuario
    # =========================================================================

    def manejar_entrada(self, teclas: Optional[Any] = None) -> None:
        """
        Captura el estado de las teclas de dirección horizontal (Flechas Izquierda/Derecha o A/D)
        y actualiza el vector de velocidad horizontal (Vx) de la entidad.

        Soporta simultáneamente:
        - Flecha izquierda (pygame.K_LEFT) o tecla 'A' (pygame.K_a): movimiento hacia la izquierda (Vx negativo).
        - Flecha derecha (pygame.K_RIGHT) o tecla 'D' (pygame.K_d): movimiento hacia la derecha (Vx positivo).
        - Si no se presiona ninguna tecla o se presionan ambas simultáneamente, Vx se establece en 0.0.

        :param teclas: Secuencia de estados de teclas de pygame.key.get_pressed().
                       Si es None, se consulta automáticamente mediante pygame.key.get_pressed().
        """
        if teclas is None:
            teclas = pygame.key.get_pressed()

        izquierda = bool(teclas[pygame.K_LEFT] or teclas[pygame.K_a])
        derecha = bool(teclas[pygame.K_RIGHT] or teclas[pygame.K_d])

        direccion_x = 0.0
        if izquierda and not derecha:
            direccion_x = -1.0
            self.orientacion = "izquierda"
            if self.imagen_izquierda is not None:
                self.image = self.imagen_izquierda
        elif derecha and not izquierda:
            direccion_x = 1.0
            self.orientacion = "derecha"
            if self.imagen_derecha is not None:
                self.image = self.imagen_derecha
        else:
            direccion_x = 0.0

        # Modificación del vector Vx en función de la rapidez de movimiento configurada
        self.vx = direccion_x * self.velocidad_movimiento

        # Detección de salto: Espacio, Flecha Arriba o W (solo permitido si está en el suelo)
        salto = bool(teclas[pygame.K_SPACE] or teclas[pygame.K_UP] or teclas[pygame.K_w])
        if salto and self.en_suelo and self.fuerza_salto > 0:
            self.vy = -self.fuerza_salto
            self.en_suelo = False

    def actualizar_orientacion_sprite(self) -> None:
        """Actualiza la imagen activa según la orientación actual ('derecha' o 'izquierda')."""
        if self.orientacion == "izquierda" and self.imagen_izquierda is not None:
            self.image = self.imagen_izquierda
        elif self.orientacion == "derecha" and self.imagen_derecha is not None:
            self.image = self.imagen_derecha

    def establecer_imagen(self, imagen: Optional[pygame.Surface]) -> None:
        """
        Asigna una nueva superficie gráfica a la entidad y precalcula su versión espejada.

        :param imagen: Superficie de Pygame a asignar.
        """
        self.imagen_derecha = imagen
        self.imagen_izquierda = (
            pygame.transform.flip(imagen, True, False) if imagen is not None else None
        )
        self.actualizar_orientacion_sprite()
        if self.image is not None:
            self.rect = self.image.get_rect(center=(round(self._x), round(self._y)))
            self.sincronizar_hitbox()

    # =========================================================================
    # Métodos de Transformación y Sincronización
    # =========================================================================

    def sincronizar_hitbox(self) -> None:
        """
        Sincroniza el centro de la hitbox matemática con las coordenadas continuas (x, y)
        y alinea la base del rectángulo visual (rect.midbottom) con la base de la hitbox,
        garantizando que las patas del personaje toquen el suelo con precisión milimétrica.
        """
        centro_entero = (round(self._x), round(self._y))
        self.hitbox.center = centro_entero
        if hasattr(self, "rect") and self.rect is not None:
            offset_y = round(getattr(self, "offset_visual_y", 0.0))
            offset_x = round(getattr(self, "offset_visual_x", 0.0))

            # Si el sprite está volteado horizontalmente, invertimos el offset visual
            if getattr(self, "orientacion", "derecha") == "izquierda":
                offset_x = -offset_x

            self.rect.midbottom = (
                self.hitbox.midbottom[0] + offset_x,
                self.hitbox.midbottom[1] + offset_y,
            )

    def establecer_velocidad(self, vx: float, vy: float) -> None:
        """
        Establece la velocidad actual de la entidad en píxeles por segundo.

        :param vx: Velocidad horizontal (px/s).
        :param vy: Velocidad vertical (px/s).
        """
        self.vx = float(vx)
        self.vy = float(vy)

    def desplazar(self, dx: float, dy: float) -> None:
        """
        Desplaza la entidad una cantidad determinada en píxeles y actualiza la hitbox.

        :param dx: Desplazamiento en el eje X.
        :param dy: Desplazamiento en el eje Y.
        """
        self._x += float(dx)
        self._y += float(dy)
        self.sincronizar_hitbox()

    def calcular_distancia_hitbox(self, otra_entidad: EntidadBase) -> float:
        """
        Calcula la distancia euclidiana entre el centro del Hitbox de esta entidad
        y el centro del Hitbox de otra entidad.

        :param otra_entidad: Instancia de EntidadBase a comparar.
        :return: Distancia en píxeles (float).
        """
        centro_self_x, centro_self_y = self.hitbox.center
        centro_otro_x, centro_otro_y = otra_entidad.hitbox.center
        dx = centro_otro_x - centro_self_x
        dy = centro_otro_y - centro_self_y
        return math.hypot(dx, dy)

    # =========================================================================
    # Métodos del Ciclo de Vida del Motor
    # =========================================================================

    def resolver_colisiones(
        self,
        lista_suelo: List[Any],
        dt: float,
    ) -> None:
        """
        Resuelve el movimiento y las colisiones AABB aplicando separación desacoplada de ejes.

        Fases del algoritmo:
        1. Eje X:
           - Integra el desplazamiento horizontal continuo: x(t + dt) = x(t) + vx * dt
           - Sincroniza la hitbox en el eje X.
           - Comprueba colisión AABB contra cada obstáculo y resuelve en X según el signo de vx.
           - Anula la componente vx si hubo colisión lateral (impacto inelástico).
        2. Eje Y:
           - Aplica la aceleración gravitatoria: vy(t + dt) = vy(t) + g * dt [Euler semi-implícito]
           - Integra el desplazamiento vertical continuo: y(t + dt) = y(t) + vy * dt
           - Sincroniza la hitbox en el eje Y.
           - Comprueba colisión AABB contra cada obstáculo y resuelve en Y según el signo de vy.
           - Anula la componente vy si hubo colisión vertical y actualiza el flag 'en_suelo'.
        3. Sincroniza las coordenadas continuas y el rectángulo visual.

        :param lista_suelo: Lista de obstáculos (pygame.Rect o instancias con atributo .hitbox).
        :param dt: Delta Time en segundos.
        """
        if not self.activa:
            return

        # =========================================================================
        # FASE 1: MOVIMIENTO Y RESOLUCIÓN EN EL EJE HORIZONTAL (X)
        # =========================================================================
        # 1.1. Integración de posición horizontal continua
        self._x += self.vx * dt
        self.hitbox.centerx = round(self._x)

        # 1.2. Detección y respuesta de colisiones en el eje X
        for obstaculo in lista_suelo:
            rect_obstaculo = obstaculo.hitbox if hasattr(obstaculo, "hitbox") else obstaculo
            if self.hitbox.colliderect(rect_obstaculo):
                if self.vx > 0.0:
                    # Desplazamiento hacia la derecha (+X): impacto contra la cara izquierda del obstáculo
                    self.hitbox.right = rect_obstaculo.left
                    self._x = float(self.hitbox.centerx)
                    self.vx = 0.0
                elif self.vx < 0.0:
                    # Desplazamiento hacia la izquierda (-X): impacto contra la cara derecha del obstáculo
                    self.hitbox.left = rect_obstaculo.right
                    self._x = float(self.hitbox.centerx)
                    self.vx = 0.0

        # =========================================================================
        # FASE 2: MOVIMIENTO Y RESOLUCIÓN EN EL EJE VERTICAL (Y)
        # =========================================================================
        # 2.1. Aceleración por gravedad (Euler semi-implícito)
        self.vy += self.gravedad * dt

        # 2.2. Integración de posición vertical continua
        self._y += self.vy * dt
        self.hitbox.centery = round(self._y)

        # 2.3. Reinicio presuntivo del flag de contacto con el suelo
        self.en_suelo = False

        # 2.4. Detección y respuesta de colisiones en el eje Y
        for obstaculo in lista_suelo:
            rect_obstaculo = obstaculo.hitbox if hasattr(obstaculo, "hitbox") else obstaculo
            if self.hitbox.colliderect(rect_obstaculo):
                if self.vy > 0.0:
                    # Caída hacia abajo (+Y): la base de la entidad aterriza en el suelo
                    self.hitbox.bottom = rect_obstaculo.top
                    self._y = float(self.hitbox.centery)
                    self.vy = 0.0
                    self.en_suelo = True
                elif self.vy < 0.0:
                    # Salto hacia arriba (-Y): la cabeza de la entidad colisiona con un techo
                    self.hitbox.top = rect_obstaculo.bottom
                    self._y = float(self.hitbox.centery)
                    self.vy = 0.0

        # =========================================================================
        # FASE 3: SINCRONIZACIÓN FINAL
        # =========================================================================
        self.sincronizar_hitbox()

    def actualizar(
        self,
        dt: float,
        teclas: Optional[Any] = None,
        lista_suelo: Optional[List[Any]] = None,
    ) -> None:
        """
        Actualiza el estado físico de la entidad procesando el Delta Time (dt).

        Si se proporciona 'lista_suelo', resuelve las colisiones en X e Y mediante
        separación de ejes desacoplada. Si es None, realiza movimiento continuo libre.

        :param dt: Delta Time en segundos (tiempo transcurrido desde el frame anterior).
        :param teclas: Mapa opcional de teclas de pygame.key.get_pressed().
        :param lista_suelo: Lista opcional de obstáculos físicos (pygame.Rect o con .hitbox).
        """
        if not self.activa:
            return

        # 1. Captura de teclas para modificar el vector de velocidad horizontal Vx y salto
        if teclas is not None or self.controlar_con_teclado:
            self.manejar_entrada(teclas)

        # 2. Actualización de posición y resolución de colisiones
        if lista_suelo is not None:
            self.resolver_colisiones(lista_suelo, dt)
        else:
            self.vy = self.vy + (self.gravedad * dt)
            self._x = self._x + (self.vx * dt)
            self._y = self._y + (self.vy * dt)
            self.sincronizar_hitbox()

        # 3. Lógica matemática para reducir el tiempo de invulnerabilidad en cada cuadro renderizado:
        # temporizador_invulnerable = temporizador_invulnerable - dt
        if self.temporizador_invulnerable > 0.0:
            self.temporizador_invulnerable = self.temporizador_invulnerable - dt
            if self.temporizador_invulnerable <= 0.0:
                self.temporizador_invulnerable = 0.0
                if hasattr(self, "imagen_normal") and self.imagen_normal is not None:
                    if hasattr(self, "salud") and self.salud and self.salud.esta_vivo():
                        self.image = self.imagen_normal
                elif hasattr(self, "actualizar_orientacion_sprite"):
                    self.actualizar_orientacion_sprite()

    def recibir_daño(self, cantidad: float) -> None:
        """
        Aplica daño al componente de salud de cualquier entidad si no está en invulnerabilidad.
        Inmediatamente después del golpe, establece temporizador_invulnerable = 1.0 (segundo de gracia).
        """
        if not self.activa:
            return

        if hasattr(self, "salud") and self.salud is not None:
            if not self.salud.esta_vivo():
                return

        if self.temporizador_invulnerable > 0.0:
            return

        if hasattr(self, "salud") and self.salud is not None:
            self.salud.recibir_daño(cantidad)

        # Inmediatamente después del golpe, establece 1.0 segundo de gracia
        self.temporizador_invulnerable = getattr(self, "duracion_invulnerabilidad", 1.0)

        salud_txt = (
            f"{self.salud.vida_actual:.1f}/{self.salud.vida_maxima:.1f}"
            if hasattr(self, "salud") and self.salud is not None
            else "N/A"
        )

        print(
            f"💥 [{self.__class__.__name__}] GOLPEADO! Daño: -{cantidad:.1f} HP | "
            f"Salud restante: {salud_txt} | Invulnerable por {self.temporizador_invulnerable:.1f}s"
        )

        if hasattr(self, "imagen_herido") and self.imagen_herido is not None:
            if hasattr(self, "salud") and self.salud and self.salud.esta_vivo():
                self.image = self.imagen_herido

        if hasattr(self, "salud") and self.salud and not self.salud.esta_vivo():
            print(f"💀 [{self.__class__.__name__}] DERROTADO!")
            self.activa = False
            self.viva = False

    def dibujar(self, pantalla: pygame.Surface, depurar_hitbox: bool = False) -> None:
        """
        Renderiza la entidad sobre la superficie provista con soporte para parpadeo de invulnerabilidad.

        :param pantalla: Superficie de Pygame (pygame.Surface) donde se dibujará la entidad.
        :param depurar_hitbox: Si es True, dibuja el contorno de la hitbox en verde para depuración.
        """
        if not self.activa:
            return

        # Parpadeo gráfico mientras transcurre el tiempo de invulnerabilidad
        if self.temporizador_invulnerable > 0.0 and int(self.temporizador_invulnerable * 16) % 2 == 0:
            if depurar_hitbox:
                if hasattr(self, "hurtbox") and self.hurtbox is not None:
                    pygame.draw.rect(pantalla, (0, 180, 255), self.hurtbox, width=1)
                pygame.draw.rect(pantalla, (0, 255, 0), self.hitbox, width=1)
            return

        # Renderizado del sprite o figura de reemplazo
        if self.image is not None:
            pantalla.blit(self.image, self.rect)
        else:
            pygame.draw.rect(pantalla, self.color, self.hitbox)

        # Renderizado opcional de la hitbox matemática para depuración física
        if depurar_hitbox:
            pygame.draw.rect(pantalla, (0, 255, 0), self.hitbox, width=1)

    def colisiona_con(self, otra_entidad: "EntidadBase") -> bool:
        """
        Verifica colisión AABB entre la hitbox de esta entidad y la de otra entidad.

        :param otra_entidad: Otra instancia de EntidadBase.
        :return: True si las hitboxes se solapan, False en caso contrario.
        """
        return self.hitbox.colliderect(otra_entidad.hitbox)

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} centro=({self._x:.2f}, {self._y:.2f}) "
            f"vel=({self.vx:.2f}, {self.vy:.2f}) hitbox={self.hitbox}>"
        )


class Jugador(EntidadBase):
    """
    Subclase especializada para el personaje jugable.
    Habilita por defecto el control por teclado para movimiento sobre el eje X.

    Rectángulos de colisión:
    - hitbox: rectángulo físico reducido, usado para colisiones con el escenario.
    - hurtbox: rectángulo que cubre todo el sprite visual, usado para recibir daño.
    """

    def __init__(
        self,
        x: float,
        y: float,
        ancho: int = 32,
        alto: int = 32,
        vx: float = 0.0,
        vy: float = 0.0,
        gravedad: float = 980.0,
        velocidad_movimiento: float = 250.0,
        fuerza_salto: float = 480.0,
        imagen: Optional[pygame.Surface] = None,
        color: Tuple[int, int, int] = (0, 200, 255),
        hitbox_ancho: Optional[int] = None,
        hitbox_alto: Optional[int] = None,
        offset_visual_y: float = 0.0,
        offset_visual_x: float = 0.0,
        hurtbox_margin_x: int = 0,
        hurtbox_margin_y: int = 0,
        hurtbox_offset_x: float = 0.0,
        hurtbox_offset_y: float = 0.0,
        vida_maxima: float = 100.0,
    ) -> None:
        super().__init__(
            x=x,
            y=y,
            ancho=ancho,
            alto=alto,
            vx=vx,
            vy=vy,
            gravedad=gravedad,
            velocidad_movimiento=velocidad_movimiento,
            fuerza_salto=fuerza_salto,
            controlar_con_teclado=True,
            imagen=imagen,
            color=color,
            hitbox_ancho=hitbox_ancho,
            hitbox_alto=hitbox_alto,
            offset_visual_y=offset_visual_y,
            offset_visual_x=offset_visual_x,
        )

        # Componente de salud desacoplado (Composición sobre Herencia)
        self.salud: ComponenteSalud = ComponenteSalud(vida_maxima=vida_maxima)

        # Márgenes (dimensiones) y desfasajes (posicionamiento) de la hurtbox
        self.hurtbox_margin_x: int = hurtbox_margin_x
        self.hurtbox_margin_y: int = hurtbox_margin_y
        self.hurtbox_offset_x: float = hurtbox_offset_x
        self.hurtbox_offset_y: float = hurtbox_offset_y

        # Hurtbox: nace y se mantiene alineada a la hitbox física por defecto
        self.hurtbox: pygame.Rect = self.hitbox.inflate(self.hurtbox_margin_x, self.hurtbox_margin_y)

        # Attackbox: área de impacto de ataque. Comienza apagada / vacía (None)
        # y se activará temporalmente como un pygame.Rect durante un ataque.
        self.attackbox: Optional[pygame.Rect] = None
        self.atacando: bool = False
        self.duracion_ataque: float = 0.25  # Duración del ataque en segundos (250 ms)
        self.tiempo_ataque_restante: float = 0.0
        self.attackbox_ancho: int = int(ancho * 0.7)  # Tamaño proporcional de la caja de ataque
        self.attackbox_alto: int = int(alto * 0.7)

        # Registro de enemigos ya impactados durante el ataque en curso
        self.enemigos_golpeados_en_este_ataque: set[int] = set()

    # =========================================================================
    # Mecánicas de Ataque
    # =========================================================================

    def atacar(self) -> None:
        """
        Activa la maniobra de ataque. Genera la attackbox frente al personaje
        durante 'duracion_ataque' segundos.
        """
        if not self.atacando:
            self.atacando = True
            self.tiempo_ataque_restante = self.duracion_ataque
            self.enemigos_golpeados_en_este_ataque.clear()
            self.actualizar_attackbox()

    def actualizar_attackbox(self) -> None:
        """
        Calcula y posiciona la attackbox inmediatamente frente al personaje
        según su dirección actual (derecha o izquierda).
        """
        if not hasattr(self, "hurtbox") or self.hurtbox is None:
            return

        alto_box = min(self.attackbox_alto, self.hurtbox.height)
        pos_y = self.hurtbox.centery - (alto_box // 2)

        if self.orientacion == "izquierda":
            pos_x = self.hurtbox.left - self.attackbox_ancho
        else:
            pos_x = self.hurtbox.right

        self.attackbox = pygame.Rect(pos_x, pos_y, self.attackbox_ancho, alto_box)

    # =========================================================================
    # Sincronización y Actualización
    # =========================================================================

    def sincronizar_hitbox(self) -> None:
        """
        Extiende la sincronización base para mantener la hurtbox y la attackbox alineadas
        con la hitbox física (self.hitbox) en cada frame.
        """
        super().sincronizar_hitbox()
        if hasattr(self, "hurtbox") and hasattr(self, "hitbox") and self.hitbox is not None:
            margin_x = getattr(self, "hurtbox_margin_x", 0)
            margin_y = getattr(self, "hurtbox_margin_y", 0)
            off_x = getattr(self, "hurtbox_offset_x", 0.0)
            off_y = getattr(self, "hurtbox_offset_y", 0.0)

            if getattr(self, "orientacion", "derecha") == "izquierda":
                off_x = -off_x

            # Nace y se sincroniza a partir de self.hitbox (física)
            self.hurtbox = self.hitbox.inflate(margin_x, margin_y)
            self.hurtbox.x += round(off_x)
            self.hurtbox.y += round(off_y)

        if getattr(self, "atacando", False):
            self.actualizar_attackbox()

    def actualizar(
        self,
        dt: float,
        teclas: Optional[Any] = None,
        lista_suelo: Optional[List[Any]] = None,
    ) -> None:
        """
        Actualiza el estado físico y decrementa el temporizador de ataque.
        """
        super().actualizar(dt, teclas=teclas, lista_suelo=lista_suelo)

        # Gestión del temporizador del ataque activo
        if self.atacando:
            self.tiempo_ataque_restante -= dt
            if self.tiempo_ataque_restante <= 0.0:
                self.atacando = False
                self.attackbox = None
                self.tiempo_ataque_restante = 0.0
            else:
                self.actualizar_attackbox()
        else:
            self.attackbox = None

    def dibujar(self, pantalla: pygame.Surface, depurar_hitbox: bool = False) -> None:
        """
        Renderiza la entidad y su attackbox (en rojo) cuando esté activa.
        """
        super().dibujar(pantalla, depurar_hitbox=depurar_hitbox)

        # Si el ataque está activo, renderizar la attackbox (rojo traslúcido / contorno)
        if self.attackbox is not None:
            pygame.draw.rect(pantalla, (255, 60, 60), self.attackbox, width=2)

        if depurar_hitbox and hasattr(self, "hurtbox") and self.hurtbox is not None:
            pygame.draw.rect(pantalla, (0, 180, 255), self.hurtbox, width=1)


class Enemigo(EntidadBase):
    """
    Entidad enemiga controlada por una Máquina de Estados Finitos (FSM).
    Dispone de ComponenteSalud, Hurtbox propia, representación gráfica, 
    tiempo de gracia/invulnerabilidad y comportamientos modulares en un diccionario.
    """

    def __init__(
        self,
        x: float,
        y: float,
        ancho: int = 64,
        alto: int = 64,
        imagen: Optional[pygame.Surface] = None,
        imagen_herido: Optional[pygame.Surface] = None,
        vida_maxima: float = 100.0,
        rango_deteccion: float = 300.0,
        rango_ataque: float = 50.0,
        puntos_patrulla: Optional[List[Tuple[float, float]]] = None,
    ) -> None:
        super().__init__(
            x=x,
            y=y,
            ancho=ancho,
            alto=alto,
            controlar_con_teclado=False,
            imagen=imagen,
            color=(220, 50, 80),
        )

        self.salud: ComponenteSalud = ComponenteSalud(vida_maxima=vida_maxima)
        self.imagen_normal: Optional[pygame.Surface] = imagen
        self.imagen_herido: Optional[pygame.Surface] = imagen_herido
        self.hurtbox: pygame.Rect = self.hitbox.copy()

        # Temporizador de invulnerabilidad (tiempo de gracia tras recibir daño)
        self.temporizador_invulnerable: float = 0.0

        # ---------------------------------------------------------------------
        # PARÁMETROS Y VARIABLES DE LA FSM (IA ENEMIGA)
        # ---------------------------------------------------------------------
        self.rango_deteccion: float = rango_deteccion
        self.rango_ataque: float = rango_ataque
        self.cooldown_ataque: float = 2.0  # Segundos de espera entre ataques
        self.tiempo_ultimo_ataque: float = 0.0

        # Puntos de patrulla (por defecto realiza un recorrido horizontal)
        self.puntos_patrulla: List[Tuple[float, float]] = puntos_patrulla or [
            (x - 100.0, y),
            (x + 100.0, y),
        ]
        self._indice_patrulla: int = 0

        # Estado inicial y Diccionario de Comportamientos (FSM)
        self.estado_actual: str = "PATRULLA"
        self.comportamientos: Dict[str, Callable[[float, Optional[Any]], None]] = {
            "PATRULLA": self._ejecutar_patrulla,
            "PERSECUCION": self._ejecutar_persecucion,
            "ATAQUE": self._ejecutar_ataque,
        }

    def sincronizar_hitbox(self) -> None:
        super().sincronizar_hitbox()
        if hasattr(self, "hurtbox") and hasattr(self, "hitbox") and self.hitbox is not None:
            self.hurtbox = self.hitbox.copy()

    def recibir_daño(self, cantidad: float) -> None:
        """Aplica daño al componente de salud si la entidad no está en estado de invulnerabilidad."""
        if not self.salud.esta_vivo() or self.temporizador_invulnerable > 0.0:
            return

        self.salud.recibir_daño(cantidad)

        # Inmediatamente después del golpe, establece 1.0 segundo de gracia
        self.temporizador_invulnerable = 1.0

        print(
            f"💥 ¡ENEMIGO GOLPEADO! Daño: -{cantidad:.1f} HP | "
            f"Salud restante: {self.salud.vida_actual:.1f}/{self.salud.vida_maxima:.1f} | "
            f"Invulnerable por 1.0s"
        )

        if self.imagen_herido is not None and self.salud.esta_vivo():
            self.image = self.imagen_herido

        if not self.salud.esta_vivo():
            print("💀 ¡ENEMIGO DERROTADO!")
            self.activa = False

    # =========================================================================
    # BUCLE PRINCIPAL DE ACTUALIZACIÓN (CONSULTA Y EJECUTA EL ESTADO ACTUAL)
    # =========================================================================

    def actualizar(
        self,
        dt: float,
        teclas: Optional[Any] = None,
        lista_suelo: Optional[List[Any]] = None,
        jugador: Optional[Any] = None,
    ) -> None:
        """
        Actualiza la posición, descuenta la invulnerabilidad y consulta/ejecuta 
        el estado actual de la FSM desde el diccionario de comportamientos.
        """
        # Descuento de temporizadores (cooldown de ataque e invulnerabilidad)
        if self.tiempo_ultimo_ataque > 0.0:
            self.tiempo_ultimo_ataque = max(0.0, self.tiempo_ultimo_ataque - dt)

        if self.temporizador_invulnerable > 0.0:
            self.temporizador_invulnerable = self.temporizador_invulnerable - dt
            if self.temporizador_invulnerable <= 0.0:
                self.temporizador_invulnerable = 0.0
                if self.imagen_normal is not None and self.salud.esta_vivo():
                    self.image = self.imagen_normal

        if self.salud.esta_vivo():
            # 1. Evaluación de transiciones según la distancia al jugador
            if jugador is not None:
                self._evaluar_transiciones(jugador)

            # 2. Consulta y ejecución del estado actual desde el diccionario
            accion_estado = self.comportamientos.get(self.estado_actual)
            if accion_estado:
                accion_estado(dt, jugador)

        # 3. Actualización física base (aplicación de movimiento por subpíxel y gravedad)
        super().actualizar(dt, teclas=teclas, lista_suelo=lista_suelo)

    # =========================================================================
    # LÓGICA DE TRANSICIÓN Y MÉTODOS DE ESTADO (FSM MODULAR)
    # =========================================================================

    def _evaluar_transiciones(self, jugador: Any) -> None:
        """
        Evalúa la distancia euclidiana entre el centro del Hitbox del enemigo
        y el centro del Hitbox del jugador para determinar el estado correspondiente.
        """
        distancia = self.calcular_distancia_hitbox(jugador)

        if distancia <= self.rango_ataque:
            self.cambiar_estado("ATAQUE")
        elif distancia <= self.rango_deteccion:
            self.cambiar_estado("PERSECUCION")
        else:
            self.cambiar_estado("PATRULLA")

    def cambiar_estado(self, nuevo_estado: str) -> None:
        """Cambia el estado actual asegurándose de que exista en la FSM."""
        if nuevo_estado in self.comportamientos and self.estado_actual != nuevo_estado:
            self.estado_actual = nuevo_estado

    def _ejecutar_patrulla(self, dt: float, jugador: Optional[Any] = None) -> None:
        """Lógica del estado PATRULLA: oscila entre los puntos de patrulla."""
        if not self.puntos_patrulla:
            self.vx = 0.0
            return

        objetivo_x, _ = self.puntos_patrulla[self._indice_patrulla]
        dx = objetivo_x - self.x

        if abs(dx) < 5.0:
            self._indice_patrulla = (self._indice_patrulla + 1) % len(self.puntos_patrulla)
        else:
            direccion = 1.0 if dx > 0 else -1.0
            self.vx = direccion * (self.velocidad_movimiento * 0.5)

    def _ejecutar_persecucion(self, dt: float, jugador: Optional[Any] = None) -> None:
        """Lógica del estado PERSECUCION: avanza hacia el centro del Hitbox del jugador."""
        if jugador is None:
            self.vx = 0.0
            return

        centro_enemigo_x = self.hitbox.centerx
        centro_jugador_x = jugador.hitbox.centerx
        dx = centro_jugador_x - centro_enemigo_x

        if abs(dx) > 0.0:
            direccion = 1.0 if dx > 0 else -1.0
            self.vx = direccion * self.velocidad_movimiento

    def _ejecutar_ataque(self, dt: float, jugador: Optional[Any] = None) -> None:
        """Lógica del estado ATAQUE: detiene el desplazamiento. El daño real se gestiona en la escena."""
        self.vx = 0.0

    def _realizar_ataque(self, jugador: Optional[Any]) -> None:
        """Realiza la acción directa de ataque contra la posición del Hitbox del jugador."""
        if jugador is not None:
            distancia_hitbox = self.calcular_distancia_hitbox(jugador)
            print(
                f"⚔️ ¡ENEMIGO ATACA AL JUGADOR! "
                f"Distancia entre Hitboxes: {distancia_hitbox:.1f}px | "
                f"Centro Hitbox Jugador: {jugador.hitbox.center}"
            )


    def dibujar(self, pantalla: pygame.Surface, depurar_hitbox: bool = False) -> None:
        if not self.activa:
            return

        super().dibujar(pantalla, depurar_hitbox=depurar_hitbox)

        # Barra de vida gráfica sobre el enemigo
        if self.salud.esta_vivo():
            ancho_bar = self.hitbox.width
            alto_bar = 6
            x_bar = self.hitbox.left
            y_bar = self.hitbox.top - 12
            porcentaje = self.salud.porcentaje()

            pygame.draw.rect(pantalla, (80, 20, 20), (x_bar, y_bar, ancho_bar, alto_bar))
            pygame.draw.rect(
                pantalla, (50, 220, 80), (x_bar, y_bar, int(ancho_bar * porcentaje), alto_bar)
            )
            pygame.draw.rect(pantalla, (255, 255, 255), (x_bar, y_bar, ancho_bar, alto_bar), width=1)

        if depurar_hitbox and hasattr(self, "hurtbox") and self.hurtbox is not None:
            pygame.draw.rect(pantalla, (0, 180, 255), self.hurtbox, width=1)


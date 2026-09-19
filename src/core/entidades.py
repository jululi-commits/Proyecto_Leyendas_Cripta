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
from typing import Any, List, Optional, Tuple
import pygame


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
        y alinea el rectángulo visual (rect) sobre la hitbox.

        offset_visual_y: desplazamiento vertical fino entre sprite y hitbox.
        Un valor positivo baja el sprite (cierra el aire con el suelo).
        Un valor negativo sube el sprite.
        """
        centro_entero = (round(self._x), round(self._y))
        self.hitbox.center = centro_entero
        if hasattr(self, "rect") and self.rect is not None:
            offset_y = round(getattr(self, "offset_visual_y", 0.0))
            self.rect.centerx = self.hitbox.centerx
            self.rect.centery = self.hitbox.centery + offset_y

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

    def dibujar(self, pantalla: pygame.Surface, depurar_hitbox: bool = False) -> None:
        """
        Renderiza la entidad sobre la superficie provista.

        Si dispone de una imagen (self.image), la dibuja en pantalla. De lo contrario,
        dibuja un rectángulo de color según las dimensiones de la hitbox (útil para prototipado).

        :param pantalla: Superficie de Pygame (pygame.Surface) donde se dibujará la entidad.
        :param depurar_hitbox: Si es True, dibuja el contorno de la hitbox en verde para depuración.
        """
        if not self.activa:
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
        )

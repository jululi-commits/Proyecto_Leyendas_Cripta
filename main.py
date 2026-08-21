import pygame
import sys
import sqlite3
import random
from pathlib import Path

# Directorio base del proyecto (la carpeta donde está este archivo main.py)
BASE_DIR = Path(__file__).resolve().parent

# conexion
conexion = sqlite3.connect(BASE_DIR / "Data" / "partidas.db")
cursor = conexion.cursor()


def init_db():
    # Crea la tabla para guardar la posición del jugador si no existe
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS player_pos (
            id INTEGER PRIMARY KEY,
            x REAL,
            y REAL
        )"""
    )
    conexion.commit()


def save_player_pos(x, y):
    cursor.execute("INSERT OR REPLACE INTO player_pos (id, x, y) VALUES (1, ?, ?)", (x, y))
    conexion.commit()
    global save_message, save_message_timer
    save_message = "Miau! Posición guardada!"
    save_message_timer = 1.5  # segundos visible


def cargar_partida():
    cursor.execute("SELECT x, y FROM player_pos WHERE id = 1")
    row = cursor.fetchone()
    if row:
        return (row[0], row[1])
    return None

# estado del mensaje de guardado
save_message = ""
save_message_timer = 0.0

class Personaje:
    def __init__(self, x, y, velocidad, image=None, alt_image=None, attack_image=None, hitbox_padding=0):
        # Coordenada horizontal del personaje
        self.x = x
        # Coordenada vertical del personaje
        self.y = y
        # Velocidad de movimiento (píxeles por segundo)
        self.velocidad = velocidad
        # Sprite (Surface) y rect
        self.image = image
        # Preparar versiones espejo para facing
        self.facing = 'right'
        if image:
            self.image_right = image
            self.image_left = pygame.transform.flip(image, True, False)
            # si hay una imagen alternativa (ej. salto), crear sus versiones espejo
            if alt_image:
                self.alt_right = alt_image
                self.alt_left = pygame.transform.flip(alt_image, True, False)
            else:
                self.alt_right = None
                self.alt_left = None

            # si hay imagen de ataque, crear sus versiones espejo
            if attack_image:
                self.attack_right = attack_image
                self.attack_left = pygame.transform.flip(attack_image, True, False)
            else:
                self.attack_right = None
                self.attack_left = None

            # la imagen actualmente visible (por defecto a la derecha)
            self.current_image = self.image_right
            self.rect = self.current_image.get_rect(center=(x, y))
        else:
            self.rect = pygame.Rect(x, y, 0, 0)

        # Guardar padding para poder recalcular la hitbox si cambiamos la imagen
        self.hitbox_padding = hitbox_padding

        # Hitbox para colisiones (más pequeña que el rect visual si se pide)
        if self.hitbox_padding > 0:
            # inflate reduces width/height by the given amounts (total)
            self.hitbox = self.rect.inflate(-self.hitbox_padding * 3, -self.hitbox_padding * 3)
        else:
            # por defecto la hitbox coincide con el rect
            self.hitbox = self.rect.copy()

    @property
    def mask(self):
        """Retorna la máscara de colisión de píxeles para la imagen actualmente activa."""
        if getattr(self, 'current_image', None) is not None:
            return pygame.mask.from_surface(self.current_image)
        return None

    def move(self, dx, dy):
        ix = int(dx)
        iy = int(dy)
        self.rect.x += ix
        self.rect.y += iy
        # mover también la hitbox
        self.hitbox.x += ix
        self.hitbox.y += iy

    def draw(self, screen):
        # Dibujar la imagen actualmente activa si existe
        if getattr(self, 'current_image', None) is not None:
            screen.blit(self.current_image, self.rect)


class Jugador(Personaje):
    def __init__(self, x, y, velocidad, image, alt_image=None, attack_image=None, hitbox_padding=10):
        # Inicializa usando el constructor de la clase base Personaje
        super().__init__(x, y, velocidad, image, alt_image, attack_image, hitbox_padding)
        # temporizador para ataque breve
        self.attack_duration = 0.25  # segundos (aumentado para facilitar el impacto)
        self.attack_timer = 0.0
        self._attack_pressed_last = False
        # guardar posición (tecla G) - detección de flanco
        self._save_pressed_last = False
        # Vidas del jugador e invulnerabilidad tras recibir daño
        self.lives = 9
        self.invuln_timer = 0.0
        self.invuln_duration = 1.0

    def handle_input(self, keys, dt):
        dx = 0
        dy = 0
        # velocidad en píxeles por segundo, dt en segundos
        speed = self.velocidad * dt
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += speed

        # Normalizar diagonal para evitar moverse más rápido en diagonal
        if dx != 0 and dy != 0:
            from math import sqrt
            factor = 1 / sqrt(2)
            dx *= factor
            dy *= factor

        # Actualizar facing (flip horizontal) según movimiento en X
        if dx < 0:
            self.facing = 'left'
        elif dx > 0:
            self.facing = 'right'

        # Estado de salto: activo mientras se mantenga la tecla W/UP
        jumping = keys[pygame.K_w] or keys[pygame.K_UP]

        # Detectar inicio de ataque (flanco) con SPACE para mostrar sprite momentáneo
        attack_pressed = keys[pygame.K_SPACE]
        if attack_pressed and not self._attack_pressed_last:
            self.attack_timer = self.attack_duration
            self.has_hit_boss = False  # Reiniciar control para 1 golpe por zarpazo
        self._attack_pressed_last = attack_pressed

        # Guardar posición al presionar G (flanco)
        save_pressed = keys[pygame.K_g]
        if save_pressed and not self._save_pressed_last:
            # guardar la posición central actual
            save_player_pos(self.rect.centerx, self.rect.centery)
        self._save_pressed_last = save_pressed

        # decrementar temporizador de ataque
        if self.attack_timer > 0:
            self.attack_timer -= dt

        attacking = self.attack_timer > 0

        # Seleccionar la imagen actual según estado y facing (ataque > salto > normal)
        if attacking:
            if self.facing == 'left' and getattr(self, 'attack_left', None):
                self.current_image = self.attack_left
            elif getattr(self, 'attack_right', None):
                self.current_image = self.attack_right
        elif jumping:
            if self.facing == 'left' and getattr(self, 'alt_left', None):
                self.current_image = self.alt_left
            elif getattr(self, 'alt_right', None):
                self.current_image = self.alt_right
        else:
            if self.facing == 'left':
                self.current_image = self.image_left
            else:
                self.current_image = self.image_right

        self.move(dx, dy)

    def get_attack_rect(self):
        """Retorna un rect que representa el alcance del ataque según el facing.
        El rect aparece justo al lado de la hitbox del jugador en la dirección que mire."""
        w = int(self.hitbox.width * 0.3)
        h = int(self.hitbox.height * 0.3)
        if self.facing == 'right':
            rect = pygame.Rect(self.hitbox.right, self.hitbox.centery - h // 2, w, h)
        else:
            rect = pygame.Rect(self.hitbox.left - w, self.hitbox.centery - h // 2, w, h)
        return rect


class Enemigo(Personaje):
    def __init__(self, x, y, velocidad, image=None, hitbox_padding=6, hp=1):
        # Inicializa usando el constructor de la clase base Personaje
        # Pasamos alt_image/attack_image como None para Enemigo
        super().__init__(x, y, velocidad, image, None, None, hitbox_padding)
        # velocidad horizontal (píxeles/segundo)
        self.speed = velocidad
        self.hp = hp
        # El enemigo está "activo" mientras se mueve; cuando recibe daño pasa a estado de muerte
        self.active = True
        self.death_timer = 0.0
        self.dead = False
        # Refinar hitbox para colisiones más precisas: más estrecha y ubicada en la parte baja
        # (reduce falsas colisiones antes de que las imágenes se toquen)
        w = int(self.rect.width * 0.2)
        h = int(self.rect.height * 0.6)
        self.hitbox = pygame.Rect(0, 0, max(1, w), max(1, h))
        # colocar la hitbox alineada al centro inferior del sprite
        self.hitbox.midbottom = self.rect.midbottom

    def update(self, dt):
        """Si está activo se mueve; si no, decrementa el temporizador de muerte hasta desaparecer."""
        if self.active:
            dx = self.speed * dt
            self.move(dx, 0)
        else:
            if self.death_timer > 0:
                self.death_timer -= dt
                if self.death_timer <= 0:
                    self.dead = True

    def is_off_screen(self, screen_rect):
        # Cuando el enemigo se haya movido completamente fuera del lado derecho
        return self.rect.left > screen_rect.right

    def take_damage(self, amount):
        # Cuando recibe daño, se detiene en el lugar y comienza el temporizador de desaparición
        self.hp -= amount
        if self.hp <= 0 and self.active:
            self.active = False
            self.death_timer = 0.6


class Proyectil(Enemigo):
    """Clase para los proyectiles lanzados por el Jefe Final.
    Hereda de Enemigo para aprovechar el movimiento hacia la derecha y la detección de daño al jugador."""
    def __init__(self, x, y, velocidad, image):
        super().__init__(x, y, velocidad=velocidad, image=image, hitbox_padding=2, hp=1)

    def take_damage(self, amount):
        """Al recibir daño, el proyectil desaparece inmediatamente sin temporizador de muerte ni cambio de sprite."""
        self.hp -= amount
        if self.hp <= 0:
            self.active = False
            self.dead = True


class JefeFinal(Personaje):
    """Clase para el Jefe Final del juego.
    Hereda de Personaje, posee 100 HP, se queda en una posición fija (velocidad=0) y dispara proyectiles con velocidad e intervalos aleatorios."""
    def __init__(self, x, y, image, projectile_image, hp=100):
        super().__init__(x, y, velocidad=0, image=image, hitbox_padding=10)
        self.hp = hp
        self.max_hp = hp
        self.active = True
        self.dead = False
        # Primer disparo en un intervalo aleatorio entre 0.5s y 2.0s
        self.shoot_timer = random.uniform(0.5, 2.0)
        self.projectile_image = projectile_image

        # Refinar la hitbox del cuerpo del Jefe a su núcleo central
        # (evita que el aura externa del sprite gigante haga daño al jugador desde lejos)
        w = int(self.rect.width * 0.4)
        h = int(self.rect.height * 0.6)
        self.hitbox = pygame.Rect(0, 0, max(1, w), max(1, h))
        self.hitbox.center = self.rect.center

    def update(self, dt):
        """Actualiza el temporizador de disparo del jefe y devuelve un Proyectil cuando el temporizador llega a 0."""
        if not self.active or self.dead:
            return None

        self.shoot_timer -= dt
        if self.shoot_timer <= 0:
            # Siguiente disparo en un intervalo aleatorio entre 0.5 y 2.0 segundos
            self.shoot_timer = random.uniform(0.5, 1.5)

            # Origen aleatorio a la izquierda (detrás del sprite del Jefe)
            spawn_x = self.rect.left - random.randint(10, 40)
            # Altura aleatoria en la pantalla (dejando margen superior e inferior)
            spawn_y = random.randint(50, 670)

            # Velocidad aleatoria entre 280 y 300
            velocidad_aleatoria = random.uniform(280, 300)

            return Proyectil(
                x=spawn_x,
                y=spawn_y,
                velocidad=velocidad_aleatoria,
                image=self.projectile_image
            )
        return None

    def take_damage(self, amount):
        """Aplica daño al Jefe y marca su estado de muerte cuando la vida llega a 0."""
        if self.active:
            self.hp -= amount
            if self.hp <= 0:
                self.hp = 0
                self.active = False
                self.dead = True


def init_screen(width, height):
    # Se configura la pantalla del juego con el tamaño deseado y fondo negro
    pygame.init()
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Juego 2D Simple")
    screen.fill((0, 0, 0))
    return screen

def load_centered_image(image_path, screen):
    # Se carga la imagen y se posiciona en el centro de la pantalla
    image = pygame.image.load(image_path).convert_alpha()
    rect = image.get_rect(center=screen.get_rect().center)
    return image, rect


def scale_image_to_fit(image, max_width, max_height):
    """Escala `image` para que quepa dentro de max_width x max_height manteniendo proporción.
    No agranda la imagen si ya es más pequeña."""
    w, h = image.get_size()
    scale = min(max_width / w, max_height / h, 1)
    new_size = (int(w * scale), int(h * scale))
    if new_size == (w, h):
        return image
    return pygame.transform.smoothscale(image, new_size)

def check_pixel_collision(obj1, obj2):
    """Comprueba colisión en 2 fases:
    1. Filtro rápido por rectángulo visual en pantalla (broad-phase)
    2. Colisión exacta píxel por píxel con máscaras (narrow-phase)
    """
    r1 = obj1.rect
    r2 = obj2.rect
    if not r1.colliderect(r2):
        return False

    m1 = getattr(obj1, 'mask', None)
    m2 = getattr(obj2, 'mask', None)
    if m1 is None or m2 is None:
        return True

    offset = (obj2.rect.x - obj1.rect.x, obj2.rect.y - obj1.rect.y)
    return m1.overlap(m2, offset) is not None

def main():
    screen = init_screen(1280, 720)
    # usar las variables de mensaje definidas a nivel de módulo
    global save_message, save_message_timer

    # Inicializar la tabla en la base de datos y cargar la última posición guardada
    init_db()
    last_pos = cargar_partida()

    # Cargar fondo del escenario y escalarlo a las dimensiones de la pantalla
    fondo_img = pygame.image.load(BASE_DIR / "Assets" / "escenario.jpg").convert()
    fondo_img = pygame.transform.scale(fondo_img, (screen.get_width(), screen.get_height()))

    # Cargar sprite del gato
    gato_img = pygame.image.load(BASE_DIR / "Assets" / "gato_normal.png").convert_alpha()

    # Escalar el sprite al 30% del ancho/alto de la pantalla
    gato_img = scale_image_to_fit(gato_img, screen.get_width() * 0.4, screen.get_height() * 0.4)

    # Cargar sprite de salto y escalarlo al mismo tamaño que el sprite principal
    salto_img = pygame.image.load(BASE_DIR / "Assets" / "gato_salta.png").convert_alpha()
    salto_img = pygame.transform.smoothscale(salto_img, gato_img.get_size())

    # Cargar sprite de ataque y escalarlo al mismo tamaño
    ataque_img = pygame.image.load(BASE_DIR / "Assets" / "gato_ataque.png").convert_alpha()
    ataque_img = pygame.transform.smoothscale(ataque_img, gato_img.get_size())

    # --- Sprites enemigos ---
    fant_normal = pygame.image.load(BASE_DIR / "Assets" / "fant_normal.png").convert_alpha()
    fant_enojado = pygame.image.load(BASE_DIR / "Assets" / "fant_enojado.png").convert_alpha()
    # escalar a tamaño apropiado
    max_w = screen.get_width() * 0.25
    max_h = screen.get_height() * 0.25
    fant_normal = scale_image_to_fit(fant_normal, max_w, max_h)
    fant_enojado = scale_image_to_fit(fant_enojado, max_w, max_h)
    # sprite que verán los fantasmas cuando el juego termine (derrota)
    fant_gana = pygame.image.load(BASE_DIR / "Assets" / "fant_gana.png").convert_alpha()
    fant_gana = scale_image_to_fit(fant_gana, max_w, max_h)
    # sprite que verán los fantasmas cuando son heridos (victoria del jugador)
    fant_herido = pygame.image.load(BASE_DIR / "Assets" / "fant_herido.png").convert_alpha()
    fant_herido = scale_image_to_fit(fant_herido, max_w, max_h)

    # --- Sprites del Jefe Final y Proyectiles ---
    jefe_img = pygame.image.load(BASE_DIR / "Assets" / "fant_enojado.png").convert_alpha()
    jefe_img = scale_image_to_fit(jefe_img, screen.get_width() * 0.66, screen.get_height() * 0.924)

    proyectil_img = pygame.image.load(BASE_DIR / "Assets" / "proyectil.png").convert_alpha()
    proyectil_img = scale_image_to_fit(proyectil_img, screen.get_width() * 0.088, screen.get_height() * 0.088)

    # Crear jugador en la última posición guardada o en el centro
    if last_pos:
        start_x, start_y = int(last_pos[0]), int(last_pos[1])
    else:
        start_x, start_y = screen.get_rect().center

    jugador = Jugador(start_x, start_y, velocidad=350, image=gato_img, alt_image=salto_img, attack_image=ataque_img, hitbox_padding=10)

    # Sprite del jugador herido para mostrar en la pantalla de derrota
    gato_herido = pygame.image.load(BASE_DIR / "Assets" / "gato_herido.png").convert_alpha()
    gato_herido = pygame.transform.smoothscale(gato_herido, gato_img.get_size())

    # Fuente para mensajes en pantalla (crear después de pygame.init())
    font = pygame.font.Font(None, 24)

    clock = pygame.time.Clock()
    # Enemigos
    enemies = []
    spawn_timer = 0.0
    spawn_interval = 2
    spawn_interval_jitter = 0.8
    enemy_speed = 126  # Aumentado un 5% (de 120 a 126)
    enemies_crossed = 0
    enemies_killed = 0
    survival_timer = 120.0  # segundos para sobrevivir
    game_won = False
    victory_font = pygame.font.Font(None, 72)
    game_over = False
    game_over_font = pygame.font.Font(None, 72)
    running = True

    # Control del Jefe Final
    jefe = None
    jefe_spawned = False

    def restart():
        nonlocal spawn_timer, enemies_crossed, enemies_killed, survival_timer, game_over, game_won, jefe, jefe_spawned
        # limpiar enemigos en pantalla
        enemies.clear()
        jefe = None
        jefe_spawned = False
        # reiniciar contadores y timers
        spawn_timer = 0.0
        enemies_crossed = 0
        enemies_killed = 0
        survival_timer = 120.0
        game_over = False
        game_won = False
        # reiniciar jugador
        jugador.lives = 9
        jugador.invuln_timer = 0.0
        jugador.attack_timer = 0.0
        # restaurar sprites originales
        try:
            jugador.image_right = gato_img
            jugador.image_left = pygame.transform.flip(gato_img, True, False)
            jugador.alt_right = salto_img
            jugador.alt_left = pygame.transform.flip(salto_img, True, False)
            jugador.attack_right = ataque_img
            jugador.attack_left = pygame.transform.flip(ataque_img, True, False)
            jugador.current_image = jugador.image_left if jugador.facing == 'left' else jugador.image_right
        except Exception:
            pass
        # centrar jugador en la posición inicial
        jugador.rect.center = (start_x, start_y)
        jugador.hitbox.center = jugador.rect.center

    while running:
        # dt en segundos (para movimiento independiente de FPS)
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # Reiniciar partida al presionar J cuando hay game over o game won
            if event.type == pygame.KEYDOWN and event.key == pygame.K_j and (game_over or game_won):
                restart()

        # Leer estado de teclas
        keys = pygame.key.get_pressed()

        # Mover jugador con WASD (también acepta flechas) — solo si no hay derrota
        if not game_over:
            jugador.handle_input(keys, dt)

        # --- Spawn y actualización de enemigos y Jefe ---
        if not game_over and not game_won:
            # Aparición del Jefe Final tras eliminar 15 enemigos comunes
            if enemies_killed >= 15 and not jefe_spawned:
                jefe_spawned = True
                jefe = JefeFinal(x=130, y=screen.get_height() // 2, image=jefe_img, projectile_image=proyectil_img, hp=30)

            # Si el jefe está activo, actualiza el lanzamiento de sus proyectiles
            if jefe and jefe.active:
                nuevo_proyectil = jefe.update(dt)
                if nuevo_proyectil:
                    enemies.append(nuevo_proyectil)

            # Determinar si la FASE 2 del Jefe está activa (vida al 50% o menos)
            fase_2 = (jefe and jefe.active and jefe.hp <= jefe.max_hp // 2)

            # Spawn de enemigos normales: solo si el jefe NO ha aparecido O si está en FASE 2
            if not jefe_spawned or fase_2:
                spawn_timer -= dt
                if spawn_timer <= 0:
                    spawn_timer = spawn_interval + random.uniform(-spawn_interval_jitter, spawn_interval_jitter)
                    spawn_x = -max(fant_normal.get_width(), fant_enojado.get_width())
                    min_y = 50
                    max_y = screen.get_height() - 50
                    spawn_y = random.randint(min_y, max_y)
                    chosen_img = random.choice([fant_normal, fant_enojado])
                    spawn_speed = enemy_speed * 1.6 if chosen_img == fant_enojado else enemy_speed
                    e = Enemigo(spawn_x, spawn_y, velocidad=spawn_speed, image=chosen_img, hitbox_padding=6, hp=1)
                    enemies.append(e)

            for e in enemies[:]:
                e.update(dt)
                # Si se sale por la derecha y estaba activo, contar como cruzado
                if not getattr(e, 'dead', False) and e.is_off_screen(screen.get_rect()):
                    if getattr(e, 'active', False) and not isinstance(e, Proyectil):
                        enemies_crossed += 1
                    enemies.remove(e)
                # eliminar si terminó su animación de muerte
                elif getattr(e, 'dead', False):
                    enemies.remove(e)
        else:
            # Si hay derrota no spawneamos ni movemos enemigos
            pass

        # Manejo de colisiones: solo mientras no haya derrota
        if not game_over and not game_won:
            attacking = jugador.attack_timer > 0
            if attacking:
                # Daño del ataque del jugador a enemigos normales y proyectiles
                for e in enemies:
                    if getattr(e, 'active', False) and check_pixel_collision(jugador, e):
                        e.take_damage(e.hp)
                        # Si es un enemigo normal y murió, cambiar a sprite herido
                        if not getattr(e, 'active', True) and not isinstance(e, Proyectil):
                            try:
                                e.image_right = fant_herido
                                e.image_left = pygame.transform.flip(fant_herido, True, False)
                                e.current_image = e.image_right
                            except Exception:
                                pass
                            # Contabilizar muertes solo antes de que aparezca el Jefe
                            if not jefe_spawned:
                                enemies_killed += 1

                # Daño del ataque del jugador al Jefe Final (1 punto de daño por zarpazo)
                if jefe and jefe.active and check_pixel_collision(jugador, jefe):
                    if not getattr(jugador, 'has_hit_boss', False):
                        jefe.take_damage(1)
                        jugador.has_hit_boss = True

            # Daño de enemigos y proyectiles al jugador (incluso durante el ataque si el proyectil lo alcanza)
            for e in enemies:
                if getattr(e, 'active', False) and check_pixel_collision(jugador, e):
                    if jugador.invuln_timer <= 0:
                        jugador.lives -= 1
                        jugador.invuln_timer = jugador.invuln_duration

            # Decrementar temporizador de invulnerabilidad del jugador
            if jugador.invuln_timer > 0:
                jugador.invuln_timer -= dt

            # Decrementar temporizador de supervivencia
            survival_timer -= dt
            if survival_timer < 0:
                survival_timer = 0

            # Comprobar condición de victoria: Derrotar al Jefe Final o agotar el tiempo total
            if (jefe and jefe.dead) or survival_timer <= 0:
                game_won = True
                for ee in enemies:
                    try:
                        ee.image_right = fant_herido
                        ee.image_left = pygame.transform.flip(fant_herido, True, False)
                        ee.current_image = ee.image_right
                    except Exception:
                        pass

        # Comprobar condiciones de derrota (vidas o enemigos cruzados)
        if not game_over and not game_won and (jugador.lives <= 0 or enemies_crossed >= 10):
            game_over = True
            # Cambiar sprite del jugador al estado herido
            try:
                jugador.image_right = gato_herido
                jugador.image_left = pygame.transform.flip(gato_herido, True, False)
                jugador.current_image = jugador.image_left if jugador.facing == 'left' else jugador.image_right
                # Actualizar rect y hitbox para la nueva imagen para evitar discrepancias
                try:
                    jugador.rect = jugador.current_image.get_rect(center=jugador.rect.center)
                    if getattr(jugador, 'hitbox_padding', 0) > 0:
                        jugador.hitbox = jugador.rect.inflate(-jugador.hitbox_padding * 3, -jugador.hitbox_padding * 3)
                    else:
                        jugador.hitbox = jugador.rect.copy()
                except Exception:
                    pass
            except Exception:
                pass
            # Cambiar todos los enemigos a la imagen de victoria para ellos
            for e in enemies:
                try:
                    e.image_right = fant_gana
                    e.image_left = pygame.transform.flip(fant_gana, True, False)
                    e.current_image = e.image_right
                except Exception:
                    pass

        # Mantener dentro de la pantalla usando la hitbox reducida
        jugador.hitbox.clamp_ip(screen.get_rect())
        # sincronizar el rect visual con la hitbox (mantener centrado)
        jugador.rect.center = jugador.hitbox.center

        # Dibujar fondo del escenario
        screen.blit(fondo_img, (0, 0))

        # Dibujar enemigos y proyectiles (para que queden debajo del Jefe)
        for e in enemies:
            e.draw(screen)

        # Dibujar Jefe Final si está activo (encima de los proyectiles)
        if jefe and jefe.active:
            jefe.draw(screen)

        # Dibujar jugador: siempre visible en pantalla de derrota, si no, parpadea si es invulnerable
        if game_over:
            jugador.draw(screen)
        else:
            draw_player = True
            if jugador.invuln_timer > 0:
                draw_player = (int(jugador.invuln_timer * 10) % 2) == 0
            if draw_player:
                jugador.draw(screen)

        if save_message_timer > 0:
            save_message_timer -= dt
            text = font.render(save_message, True, (255, 255, 255))
            screen.blit(text, (10, 10))  # ajustar posición si quieres

        # Mostrar vidas en pantalla
        lives_text = font.render(f"Vidas: {jugador.lives}", True, (255, 255, 255))
        screen.blit(lives_text, (10, 40))

        # Mostrar barra de vida del Jefe Final en la parte superior central
        if jefe and jefe.active:
            if jefe.hp <= jefe.max_hp // 2:
                boss_text = font.render(f"¡FASE 2! - JEFE FINAL - Vida: {jefe.hp}/{jefe.max_hp}", True, (255, 50, 255))
            else:
                boss_text = font.render(f"JEFE FINAL - Vida: {jefe.hp}/{jefe.max_hp}", True, (255, 60, 60))
            boss_rect = boss_text.get_rect(center=(screen.get_width() // 2, 30))
            screen.blit(boss_text, boss_rect)

        # Temporizador debajo de las vidas (lado izquierdo)
        x_left = 10
        y_left = 40 + lives_text.get_height() + 6
        minutes = int(survival_timer) // 60
        seconds = int(survival_timer) % 60
        timer_text = font.render(f"Tiempo: {minutes:02d}:{seconds:02d}", True, (255, 0, 0))
        screen.blit(timer_text, (x_left, y_left))

        # Contadores en el lado derecho: Fantasmas muertos arriba, Fantasmas que escaparon abajo
        x_right_margin = 10
        # Fantasmas muertos: color VERDE, arriba a la derecha
        killed_text = font.render(f"Fantasmas muertos: {enemies_killed}/15", True, (0, 255, 0))
        killed_rect = killed_text.get_rect()
        killed_rect.topright = (screen.get_width() - x_right_margin, 40)
        screen.blit(killed_text, killed_rect)

        # Fantasmas que escaparon: color BLANCO, debajo del contador de muertos
        escaped_text = font.render(f"Fantasmas que escaparon: {enemies_crossed}/10", True, (255, 255, 255))
        escaped_rect = escaped_text.get_rect()
        escaped_rect.topright = (screen.get_width() - x_right_margin, 40 + killed_rect.height + 4)
        screen.blit(escaped_text, escaped_rect)

        # Mensaje de derrota o victoria centrado
        if game_over:
            msg = game_over_font.render("¡Derrota!", True, (255, 0, 0))
            msg_rect = msg.get_rect(center=screen.get_rect().center)
            screen.blit(msg, msg_rect)
            # Mensaje para reiniciar
            restart_text = font.render("Presiona J para volver a jugar", True, (255, 255, 255))
            restart_rect = restart_text.get_rect(center=(screen.get_rect().centerx, msg_rect.bottom + 20))
            screen.blit(restart_text, restart_rect)
        elif game_won:
            # Cambiar sprites de los enemigos a fant_herido
            for e in enemies:
                try:
                    e.image_right = fant_herido
                    e.image_left = pygame.transform.flip(fant_herido, True, False)
                    e.current_image = e.image_right
                except Exception:
                    pass
            msg = victory_font.render("¡Victoria!", True, (0, 200, 0))
            msg_rect = msg.get_rect(center=screen.get_rect().center)
            screen.blit(msg, msg_rect)
            # Mensaje para reiniciar
            restart_text = font.render("Presiona J para volver a jugar", True, (255, 255, 255))
            restart_rect = restart_text.get_rect(center=(screen.get_rect().centerx, msg_rect.bottom + 20))
            screen.blit(restart_text, restart_rect)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()




        
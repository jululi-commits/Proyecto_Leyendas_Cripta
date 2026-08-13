import pygame
import sys
import sqlite3

# conexion
conexion = sqlite3.connect("partidas.db")
cursor = conexion.cursor()


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

        # Hitbox para colisiones (más pequeña que el rect visual si se pide)
        if hitbox_padding > 0:
            # inflate reduces width/height by the given amounts (total)
            self.hitbox = self.rect.inflate(-hitbox_padding * 2, -hitbox_padding * 2)
        else:
            # por defecto la hitbox coincide con el rect
            self.hitbox = self.rect.copy()

    def move(self, dx, dy):
        ix = int(dx)
        iy = int(dy)
        self.rect.x += ix
        self.rect.y += iy
        # mover también la hitbox
        self.hitbox.x += ix
        self.hitbox.y += iy

    def draw(self, screen):
        if self.image:
            screen.blit(self.current_image, self.rect)


class Jugador(Personaje):
    def __init__(self, x, y, velocidad, image, alt_image=None, attack_image=None, hitbox_padding=10):
        # Inicializa usando el constructor de la clase base Personaje
        super().__init__(x, y, velocidad, image, alt_image, attack_image, hitbox_padding)
        # temporizador para ataque breve
        self.attack_duration = 0.16  # segundos
        self.attack_timer = 0.0
        self._attack_pressed_last = False

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
        self._attack_pressed_last = attack_pressed

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


class Enemigo(Personaje):
    def __init__(self, x, y, velocidad, image=None):
        # Inicializa usando el constructor de la clase base Personaje
        super().__init__(x, y, velocidad, image)


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

def main():
    screen = init_screen(800, 600)

    # Cargar sprite del gato (ruta relativa a la carpeta del proyecto)
    gato_img = pygame.image.load("Proyecto_Leyendas_Cripta/Assets/gato_normal.png").convert_alpha()

    # Escalar el sprite al 30% del ancho/alto de la pantalla
    gato_img = scale_image_to_fit(gato_img, screen.get_width() * 0.3, screen.get_height() * 0.3)

    # Cargar sprite de salto y escalarlo al mismo tamaño que el sprite principal
    salto_img = pygame.image.load("Proyecto_Leyendas_Cripta/Assets/gato_salta.png").convert_alpha()
    salto_img = pygame.transform.smoothscale(salto_img, gato_img.get_size())

    # Cargar sprite de ataque y escalarlo al mismo tamaño
    ataque_img = pygame.image.load("Proyecto_Leyendas_Cripta/Assets/gato_ataque.png").convert_alpha()
    ataque_img = pygame.transform.smoothscale(ataque_img, gato_img.get_size())

    # Crear jugador en el centro (hitbox_padding=5, velocidad aumentada)
    jugador = Jugador(400, 300, velocidad=300, image=gato_img, alt_image=salto_img, attack_image=ataque_img, hitbox_padding=5)

    clock = pygame.time.Clock()
    running = True

    while running:
        # dt en segundos (para movimiento independiente de FPS)
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Leer estado de teclas
        keys = pygame.key.get_pressed()

        # Mover jugador con WASD (también acepta flechas)
        jugador.handle_input(keys, dt)

        # Mantener dentro de la pantalla usando la hitbox reducida
        jugador.hitbox.clamp_ip(screen.get_rect())
        # sincronizar el rect visual con la hitbox (mantener centrado)
        jugador.rect.center = jugador.hitbox.center

        # Dibujar
        screen.fill((0, 0, 0))
        jugador.draw(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()




        
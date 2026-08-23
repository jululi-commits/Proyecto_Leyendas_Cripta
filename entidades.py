import random
from math import sqrt
import pygame


class Personaje:
    def __init__(self, x, y, velocidad, image=None, alt_image=None, attack_image=None, hitbox_padding=0):
        # Coordenadas y velocidad base
        self.x = x
        self.y = y
        self.velocidad = velocidad
        self.facing = 'right'
        self.hitbox_padding = hitbox_padding

        # Inicialización modular de sprites y hitbox
        self._setup_sprites(image, alt_image, attack_image, x, y)
        self._setup_hitbox()

    def _setup_sprites(self, image, alt_image, attack_image, x, y):
        """Configura y prepara las superficies y rectángulos del personaje (incluyendo versiones espejo)."""
        self.image = image
        if image:
            self.image_right = image
            self.image_left = pygame.transform.flip(image, True, False)

            self.alt_right = alt_image if alt_image else None
            self.alt_left = pygame.transform.flip(alt_image, True, False) if alt_image else None

            self.attack_right = attack_image if attack_image else None
            self.attack_left = pygame.transform.flip(attack_image, True, False) if attack_image else None

            self.current_image = self.image_right
            self.rect = self.current_image.get_rect(center=(x, y))
        else:
            self.image_right = None
            self.image_left = None
            self.alt_right = None
            self.alt_left = None
            self.attack_right = None
            self.attack_left = None
            self.current_image = None
            self.rect = pygame.Rect(x, y, 0, 0)

    def _setup_hitbox(self):
        """Construye la caja de colisión recortada según el padding especificado."""
        if self.hitbox_padding > 0:
            self.hitbox = self.rect.inflate(-self.hitbox_padding * 3, -self.hitbox_padding * 3)
        else:
            self.hitbox = self.rect.copy()

    @property
    def mask(self):
        """Retorna la máscara de colisión de píxeles para la imagen actualmente activa."""
        if getattr(self, 'current_image', None) is not None:
            return pygame.mask.from_surface(self.current_image)
        return None

    def move(self, dx, dy):
        """Aplica el desplazamiento entero a la posición visual y a la caja de colisiones."""
        ix = int(dx)
        iy = int(dy)
        self.rect.x += ix
        self.rect.y += iy
        self.hitbox.x += ix
        self.hitbox.y += iy

    def draw(self, screen):
        """Dibuja el sprite activo en pantalla."""
        if getattr(self, 'current_image', None) is not None:
            screen.blit(self.current_image, self.rect)


class Jugador(Personaje):
    def __init__(self, x, y, velocidad, image, alt_image=None, attack_image=None, hitbox_padding=10):
        super().__init__(x, y, velocidad, image, alt_image, attack_image, hitbox_padding)
        self.attack_duration = 0.25
        self.attack_timer = 0.0
        self._attack_pressed_last = False
        self._save_pressed_last = False
        self.lives = 9
        self.invuln_timer = 0.0
        self.invuln_duration = 1.0

    def handle_input(self, keys, dt):
        """Orquesta la entrada del teclado, movimiento, acciones y actualización visual del jugador."""
        dx, dy = self._calculate_movement(keys, dt)
        self._update_facing(dx)

        jumping = keys[pygame.K_w] or keys[pygame.K_UP]
        attacking = self._handle_actions(keys, dt)

        self._update_sprite(jumping, attacking)
        self.move(dx, dy)

    def _calculate_movement(self, keys, dt):
        """Calcula el vector de velocidad horizontal y vertical normalizado en caso de movimiento diagonal."""
        dx = 0
        dy = 0
        speed = self.velocidad * dt

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += speed

        if dx != 0 and dy != 0:
            factor = 1 / sqrt(2)
            dx *= factor
            dy *= factor

        return dx, dy

    def _update_facing(self, dx):
        """Actualiza la orientación (dirección a la que mira) según el movimiento horizontal."""
        if dx < 0:
            self.facing = 'left'
        elif dx > 0:
            self.facing = 'right'

    def _handle_actions(self, keys, dt):
        """Maneja los eventos de pulsación de teclas para ataque (SPACE) y guardado (G), y actualiza el temporizador."""
        attack_pressed = keys[pygame.K_SPACE]
        if attack_pressed and not self._attack_pressed_last:
            self.attack_timer = self.attack_duration
            self.has_hit_boss = False
        self._attack_pressed_last = attack_pressed

        save_pressed = keys[pygame.K_g]
        if save_pressed and not self._save_pressed_last:
            from db import save_player_pos
            save_player_pos(self.rect.centerx, self.rect.centery)
        self._save_pressed_last = save_pressed

        if self.attack_timer > 0:
            self.attack_timer -= dt

        return self.attack_timer > 0

    def _update_sprite(self, jumping, attacking):
        """Selecciona la textura adecuada (ataque > salto > normal) considerando la orientación actual."""
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

    def get_attack_rect(self):
        """Retorna un rect que representa el alcance del ataque según el facing."""
        w = int(self.hitbox.width * 0.3)
        h = int(self.hitbox.height * 0.3)
        if self.facing == 'right':
            return pygame.Rect(self.hitbox.right, self.hitbox.centery - h // 2, w, h)
        return pygame.Rect(self.hitbox.left - w, self.hitbox.centery - h // 2, w, h)


class Enemigo(Personaje):
    def __init__(self, x, y, velocidad, image=None, hitbox_padding=6, hp=1):
        super().__init__(x, y, velocidad, image, None, None, hitbox_padding)
        self.speed = velocidad
        self.hp = hp
        self.active = True
        self.death_timer = 0.0
        self.dead = False

        w = int(self.rect.width * 0.2)
        h = int(self.rect.height * 0.6)
        self.hitbox = pygame.Rect(0, 0, max(1, w), max(1, h))
        self.hitbox.midbottom = self.rect.midbottom

    def update(self, dt):
        """Si está activo se mueve; si no, decrementa el temporizador de muerte hasta desaparecer."""
        if self.active:
            dx = self.speed * dt
            self.move(dx, 0)
        else:
            self._update_death_timer(dt)

    def _update_death_timer(self, dt):
        """Maneja la cuenta regresiva tras recibir daño mortal."""
        if self.death_timer > 0:
            self.death_timer -= dt
            if self.death_timer <= 0:
                self.dead = True

    def is_off_screen(self, screen_rect):
        return self.rect.left > screen_rect.right

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0 and self.active:
            self.active = False
            self.death_timer = 0.6


class Proyectil(Enemigo):
    """Clase para los proyectiles lanzados por el Jefe Final."""
    def __init__(self, x, y, velocidad, image):
        super().__init__(x, y, velocidad=velocidad, image=image, hitbox_padding=2, hp=1)

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.active = False
            self.dead = True


class JefeFinal(Personaje):
    """Clase para el Jefe Final del juego."""
    def __init__(self, x, y, image, projectile_image, hp=100):
        super().__init__(x, y, velocidad=0, image=image, hitbox_padding=10)
        self.hp = hp
        self.max_hp = hp
        self.active = True
        self.dead = False
        self.shoot_timer = random.uniform(0.5, 2.0)
        self.projectile_image = projectile_image

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
            self.shoot_timer = random.uniform(0.5, 1.5)
            return self._create_projectile()
        return None

    def _create_projectile(self):
        """Genera una instancia de Proyectil con velocidad y posición Y aleatorias."""
        spawn_x = self.rect.left - random.randint(10, 40)
        spawn_y = random.randint(50, 670)
        velocidad_aleatoria = random.uniform(280, 300)

        return Proyectil(
            x=spawn_x,
            y=spawn_y,
            velocidad=velocidad_aleatoria,
            image=self.projectile_image
        )

    def take_damage(self, amount):
        if self.active:
            self.hp -= amount
            if self.hp <= 0:
                self.hp = 0
                self.active = False
                self.dead = True

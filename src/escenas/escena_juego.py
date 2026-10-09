from pathlib import Path
from typing import Any, List, Tuple, Dict

from core.escena_base import EscenaBase
from core.estados import EstadoJuego
from core.entidades import Jugador, Enemigo
import pygame

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ASSETS_DIR = BASE_DIR / "Assets"

# Definición de hitboxes estáticas del escenario (Obstáculos AABB)
suelo = pygame.Rect(0, 620, 1024, 100)       # Plataforma horizontal inferior
muroDer = pygame.Rect(960, 200, 64, 420)     # Muro vertical derecho
Hitboxes_Suelo: list[pygame.Rect] = [suelo, muroDer]

def colision_aabb(box1: pygame.Rect, box2: pygame.Rect) -> bool:
    """
    Algoritmo de Colisión AABB (Axis-Aligned Bounding Box).
    Comprueba el solapamiento entre dos rectángulos alineados con los ejes:
    - Eje X: box1.left < box2.right Y box1.right > box2.left
    - Eje Y: box1.top < box2.bottom Y box1.bottom > box2.top
    """
    return (
        box1.left < box2.right
        and box1.right > box2.left
        and box1.top < box2.bottom
        and box1.bottom > box2.top
    )


class EscenaJuego(EscenaBase):
    def __init__(self) -> None:
        super().__init__()
        self.jugador: Jugador | None = None
        self.enemigo: Enemigo | None = None

    def al_entrar(self, **kwargs) -> None:
        """Se ejecuta al iniciar o reiniciar la partida."""
        # 1. Carga y optimización del sprite del personaje desde Assets
        ruta_sprite = ASSETS_DIR / "gato_normal.png"
        sprite_gato: pygame.Surface | None = None

        # --- Tamaño del personaje: modifica SOLO esta variable ---
        ancho_personaje = 200
        alto_personaje = 200

        # Proporciones del hitbox calibradas visualmente para gato_normal.png
        HITBOX_RATIO_ANCHO  = 0.607   # fracción del ancho del sprite
        HITBOX_RATIO_ALTO   = 0.473   # fracción del alto del sprite
        OFFSET_RATIO_VISUAL_Y = 0.310   # fracción del alto del sprite
        OFFSET_RATIO_VISUAL_X = 0.040   # fracción del ancho del sprite

        hitbox_ancho_px  = int(ancho_personaje * HITBOX_RATIO_ANCHO)
        hitbox_alto_px   = int(alto_personaje  * HITBOX_RATIO_ALTO)
        offset_visual_y  = alto_personaje * OFFSET_RATIO_VISUAL_Y
        offset_visual_x  = ancho_personaje * OFFSET_RATIO_VISUAL_X  

        if ruta_sprite.exists():
            try:
                img_cargada = pygame.image.load(str(ruta_sprite)).convert_alpha()
                sprite_gato = pygame.transform.smoothscale(img_cargada, (ancho_personaje, alto_personaje))
            except Exception as e:
                print(f"Advertencia: No se pudo cargar el sprite '{ruta_sprite}': {e}")

        # 2. Instanciamos al jugador con hitbox y offset proporcionales
        self.jugador = Jugador(
            x=300.0,
            y=200.0,
            ancho=ancho_personaje,
            alto=alto_personaje,
            velocidad_movimiento=300.0,
            gravedad=980.0,
            imagen=sprite_gato,
            hitbox_ancho=hitbox_ancho_px,
            hitbox_alto=hitbox_alto_px,
            offset_visual_y=offset_visual_y,
            offset_visual_x=offset_visual_x,
            hurtbox_margin_x=0,
            hurtbox_margin_y=0,
            hurtbox_offset_x=0.0,
            hurtbox_offset_y=0.0,
            vida_maxima=100.0,
        )

        # 3. Instanciamos un enemigo de prueba estático (Fantasma)
        ruta_fant = ASSETS_DIR / "fant_normal.png"
        ruta_fant_herido = ASSETS_DIR / "fant_herido.png"
        sprite_fant: pygame.Surface | None = None
        sprite_fant_herido: pygame.Surface | None = None

        if ruta_fant.exists():
            try:
                img_f = pygame.image.load(str(ruta_fant)).convert_alpha()
                sprite_fant = pygame.transform.smoothscale(img_f, (120, 120))
            except Exception as e:
                print(f"Advertencia al cargar sprite de enemigo: {e}")

        if ruta_fant_herido.exists():
            try:
                img_fh = pygame.image.load(str(ruta_fant_herido)).convert_alpha()
                sprite_fant_herido = pygame.transform.smoothscale(img_fh, (120, 120))
            except Exception as e:
                print(f"Advertencia al cargar sprite de enemigo herido: {e}")

        self.enemigo = Enemigo(
            x=750.0,
            y=550.0,
            ancho=120,
            alto=120,
            imagen=sprite_fant,
            imagen_herido=sprite_fant_herido,
            vida_maxima=100.0,
        )

    def manejar_eventos(self, eventos: list[pygame.event.Event]) -> None:
        """Procesa la captura de eventos de teclado para acciones como el ataque."""
        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                # Tecla de ataque: X, o F
                if evento.key in (pygame.K_x, pygame.K_f):
                    if self.jugador:
                        self.jugador.atacar()

    def actualizar(self, dt: float) -> None:
        """Actualiza la física del jugador, del enemigo y resuelve los impactos AABB e invulnerabilidad."""
        if self.jugador and self.jugador.activa:
            self.jugador.actualizar(dt, lista_suelo=Hitboxes_Suelo)

        if self.enemigo and self.enemigo.activa:
            self.enemigo.actualizar(dt, lista_suelo=Hitboxes_Suelo, jugador=self.jugador)

            # 1. Ataque del Jugador -> Hurtbox del Enemigo
            if (
                self.jugador
                and self.jugador.activa
                and self.jugador.atacando
                and self.jugador.attackbox is not None
                and self.enemigo.temporizador_invulnerable <= 0.0
                and id(self.enemigo) not in self.jugador.enemigos_golpeados_en_este_ataque
            ):
                if colision_aabb(self.jugador.attackbox, self.enemigo.hurtbox):
                    dano_jugador = 25.0
                    self.enemigo.recibir_daño(dano_jugador)
                    self.jugador.enemigos_golpeados_en_este_ataque.add(id(self.enemigo))

            # 2. Ataque del Enemigo -> Hurtbox del Jugador (solo en estado ATAQUE y con cooldown listo)
            if (
                self.jugador
                and self.jugador.activa
                and self.jugador.temporizador_invulnerable <= 0.0
                and self.enemigo.estado_actual == "ATAQUE"
                and self.enemigo.tiempo_ultimo_ataque <= 0.0
            ):
                if colision_aabb(self.enemigo.hurtbox, self.jugador.hurtbox):
                    dano_enemigo = 15.0
                    self.jugador.recibir_daño(dano_enemigo)
                    self.enemigo.tiempo_ultimo_ataque = self.enemigo.cooldown_ataque

    def dibujar(self, pantalla: pygame.Surface) -> None:
        """Renderiza fondo, personajes, enemigo y HUD en pantalla."""
        pantalla.fill((30, 30, 40))

        # Dibujar obstáculos del escenario (Hitboxes_Suelo)
        for obstaculo in Hitboxes_Suelo:
            pygame.draw.rect(pantalla, (60, 70, 95), obstaculo)
            pygame.draw.rect(pantalla, (110, 135, 175), obstaculo, width=2)

        # Dibujar enemigo estático de prueba
        if self.enemigo:
            self.enemigo.dibujar(pantalla, depurar_hitbox=False)

        # Dibujar personaje jugador
        if self.jugador:
            self.jugador.dibujar(pantalla, depurar_hitbox=False)

    def cargar_imagen(self,ruta_archivo, alpha=True):
        """Carga y optimiza una imagen desde el disco gestionando excepciones (Principio DRY)."""
        try:
            imagen = pygame.image.load(ruta_archivo)
            return imagen.convert_alpha() if alpha else imagen.convert()
        except (FileNotFoundError, pygame.error) as e:
            print(f"Error crítico al cargar el recurso gráfico en '{ruta_archivo}': {e}")
            sys.exit(1)

    def cargar_assets(self, screen):
        """Carga y escala todos los recursos gráficos necesarios para la partida usando cargar_imagen."""
        w, h = screen.get_width(), screen.get_height()
        assets_dir = BASE_DIR / "Assets"

        fondo_img = pygame.transform.scale(
            cargar_imagen(assets_dir / "escenario.jpg", alpha=False), (w, h)
        )

        gato_img = scale_image_to_fit(cargar_imagen(assets_dir / "gato_normal.png"), w * 0.4, h * 0.4)
        salto_img = pygame.transform.smoothscale(cargar_imagen(assets_dir / "gato_salta.png"), gato_img.get_size())
        ataque_img = pygame.transform.smoothscale(cargar_imagen(assets_dir / "gato_ataque.png"), gato_img.get_size())
        gato_herido = pygame.transform.smoothscale(cargar_imagen(assets_dir / "gato_herido.png"), gato_img.get_size())

        max_w, max_h = w * 0.25, h * 0.25
        fant_normal = scale_image_to_fit(cargar_imagen(assets_dir / "fant_normal.png"), max_w, max_h)
        fant_enojado = scale_image_to_fit(cargar_imagen(assets_dir / "fant_enojado.png"), max_w, max_h)
        fant_gana = scale_image_to_fit(cargar_imagen(assets_dir / "fant_gana.png"), max_w, max_h)
        fant_herido = scale_image_to_fit(cargar_imagen(assets_dir / "fant_herido.png"), max_w, max_h)

        jefe_img = scale_image_to_fit(cargar_imagen(assets_dir / "fant_enojado.png"), w * 0.66, h * 0.924)
        proyectil_img = scale_image_to_fit(cargar_imagen(assets_dir / "proyectil.png"), w * 0.088, h * 0.088)

        return {
            "fondo": fondo_img,
            "gato_normal": gato_img,
            "gato_salta": salto_img,
            "gato_ataque": ataque_img,
            "gato_herido": gato_herido,
            "fant_normal": fant_normal,
            "fant_enojado": fant_enojado,
            "fant_gana": fant_gana,
            "fant_herido": fant_herido,
            "jefe": jefe_img,
            "proyectil": proyectil_img,
        }


    def actualizar_spawns_y_enemigos(self,dt, screen, enemies, jefe, jefe_spawned, spawn_timer, enemies_killed, enemies_crossed, assets):
        """Maneja el spawn de enemigos comunes, generación de proyectiles del jefe y movimiento general."""
        if enemies_killed >= 15 and not jefe_spawned:
            jefe_spawned = True
            jefe = JefeFinal(x=130, y=screen.get_height() // 2, image=assets["jefe"], projectile_image=assets["proyectil"], hp=30)

        if jefe and jefe.active:
            nuevo_proyectil = jefe.update(dt)
            if nuevo_proyectil:
                enemies.append(nuevo_proyectil)

        fase_2 = (jefe and jefe.active and jefe.hp <= jefe.max_hp // 2)

        if not jefe_spawned or fase_2:
            spawn_timer -= dt
            if spawn_timer <= 0:
                spawn_timer = 2 + random.uniform(-0.8, 0.8)
                spawn_x = -max(assets["fant_normal"].get_width(), assets["fant_enojado"].get_width())
                spawn_y = random.randint(50, screen.get_height() - 50)
                chosen_img = random.choice([assets["fant_normal"], assets["fant_enojado"]])
                spawn_speed = 126 * 1.6 if chosen_img == assets["fant_enojado"] else 126
                enemies.append(Enemigo(spawn_x, spawn_y, velocidad=spawn_speed, image=chosen_img, hitbox_padding=6, hp=1))

        for e in enemies[:]:
            e.update(dt)
            if not getattr(e, 'dead', False) and e.is_off_screen(screen.get_rect()):
                if getattr(e, 'active', False) and not isinstance(e, Proyectil):
                    enemies_crossed += 1
                enemies.remove(e)
            elif getattr(e, 'dead', False):
                enemies.remove(e)

        return jefe, jefe_spawned, spawn_timer, enemies_crossed

    def scale_image_to_fit(self, image, max_width, max_height):
        """Escala una imagen manteniendo su proporción original dentro del tamaño límite especificado."""
        w, h = image.get_size()
        scale = min(max_width / w, max_height / h, 1)
        new_size = (int(w * scale), int(h * scale))
        if new_size == (w, h):
            return image
        return pygame.transform.smoothscale(image, new_size)

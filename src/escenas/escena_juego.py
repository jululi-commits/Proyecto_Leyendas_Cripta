from pathlib import Path
from typing import Any, List, Tuple, Dict

from core.escena_base import EscenaBase
from core.estados import EstadoJuego
from core.entidades import Jugador
import pygame

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ASSETS_DIR = BASE_DIR / "Assets"

# Definición de hitboxes estáticas del escenario (Obstáculos AABB)
suelo = pygame.Rect(0, 620, 1024, 100)       # Plataforma horizontal inferior
muroDer = pygame.Rect(960, 200, 64, 420)     # Muro vertical derecho
Hitboxes_Suelo: list[pygame.Rect] = [suelo, muroDer]

class EscenaJuego(EscenaBase):
    def __init__(self) -> None:
        super().__init__()
        self.jugador: Jugador | None = None

    def al_entrar(self, **kwargs) -> None:
        """Se ejecuta al iniciar o reiniciar la partida."""
        # 1. Carga y optimización del sprite del personaje desde Assets
        ruta_sprite = ASSETS_DIR / "gato_normal.png"
        sprite_gato: pygame.Surface | None = None

        # --- Tamaño del personaje: modifica SOLO esta variable ---
        # El hitbox y el offset se calculan automáticamente a partir de ella.
        ancho_personaje = 200
        alto_personaje = 200

        # Proporciones del hitbox calibradas visualmente para gato_normal.png
        # (68/112 ≈ 0.607 de ancho, 53/112 ≈ 0.473 de alto, offset=9/112 ≈ 0.080)
        # Si cambiás ancho_personaje/alto_personaje, el alineamiento se mantiene automáticamente.
        HITBOX_RATIO_ANCHO  = 0.607   # fracción del ancho del sprite
        HITBOX_RATIO_ALTO   = 0.473   # fracción del alto del sprite
        OFFSET_RATIO_VISUAL = 0.080   # fracción del alto del sprite (baja el sprite levemente)

        hitbox_ancho_px  = int(ancho_personaje * HITBOX_RATIO_ANCHO)
        hitbox_alto_px   = int(alto_personaje  * HITBOX_RATIO_ALTO)
        offset_visual_px = alto_personaje * OFFSET_RATIO_VISUAL

        if ruta_sprite.exists():
            try:
                img_cargada = pygame.image.load(str(ruta_sprite)).convert_alpha()
                sprite_gato = pygame.transform.smoothscale(img_cargada, (ancho_personaje, alto_personaje))
            except Exception as e:
                print(f"Advertencia: No se pudo cargar el sprite '{ruta_sprite}': {e}")

        # 2. Instanciamos al jugador con hitbox y offset proporcionales al tamaño del sprite
        self.jugador = Jugador(
            x=500.0,
            y=200.0,
            ancho=ancho_personaje,
            alto=alto_personaje,
            velocidad_movimiento=300.0,
            gravedad=980.0,
            imagen=sprite_gato,
            hitbox_ancho=hitbox_ancho_px,
            hitbox_alto=hitbox_alto_px,
            offset_visual_y=offset_visual_px,
        )

    def manejar_eventos(self, eventos: list[pygame.event.Event]) -> None:
        pass

    def actualizar(self, dt: float) -> None:
        """Actualiza la física y el movimiento del jugador resolviendo colisiones."""
        if self.jugador:
            self.jugador.actualizar(dt, lista_suelo=Hitboxes_Suelo)

    def dibujar(self, pantalla: pygame.Surface) -> None:
        """Renderiza fondo, personajes, jefe y HUD en pantalla."""
        pantalla.fill((30, 30, 40))  # O dibujar assets["fondo"]

        # Dibujar obstáculos del escenario (Hitboxes_Suelo)
        for obstaculo in Hitboxes_Suelo:
            pygame.draw.rect(pantalla, (60, 70, 95), obstaculo)
            pygame.draw.rect(pantalla, (110, 135, 175), obstaculo, width=2)

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

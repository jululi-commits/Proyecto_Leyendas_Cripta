import os
import pygame
import sys
import random
from pathlib import Path

from entidades import Personaje, Jugador, Enemigo, Proyectil, JefeFinal
import db
from interfaz import dibujar_mensaje_guardado, dibujar_hud, dibujar_pantalla_final

# Directorio base del proyecto
BASE_DIR = Path(__file__).resolve().parent


def init_screen(width, height):
    """Inicializa Pygame y configura las dimensiones de la pantalla de juego."""
    pygame.init()
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Gatito VS Fantasmas")
    screen.fill((0, 0, 0))
    return screen


def scale_image_to_fit(image, max_width, max_height):
    """Escala una imagen manteniendo su proporción original dentro del tamaño límite especificado."""
    w, h = image.get_size()
    scale = min(max_width / w, max_height / h, 1)
    new_size = (int(w * scale), int(h * scale))
    if new_size == (w, h):
        return image
    return pygame.transform.smoothscale(image, new_size)


def check_pixel_collision(obj1, obj2):
    """Comprueba colisiones en dos fases: caja de delimitación visual y overlap de máscaras de píxeles."""
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


def cargar_imagen(ruta_archivo, alpha=True):
    """Carga y optimiza una imagen desde el disco gestionando excepciones (Principio DRY)."""
    try:
        imagen = pygame.image.load(ruta_archivo)
        return imagen.convert_alpha() if alpha else imagen.convert()
    except (FileNotFoundError, pygame.error) as e:
        print(f"Error crítico al cargar el recurso gráfico en '{ruta_archivo}': {e}")
        sys.exit(1)


def cargar_assets(screen):
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


def actualizar_spawns_y_enemigos(dt, screen, enemies, jefe, jefe_spawned, spawn_timer, enemies_killed, enemies_crossed, assets):
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


def procesar_colisiones(jugador, jefe, enemies, jefe_spawned, enemies_killed, assets):
    """Procesa los ataques del jugador hacia los enemigos/Jefe y el daño recibido por el jugador."""
    if jugador.attack_timer > 0:
        for e in enemies:
            if getattr(e, 'active', False) and check_pixel_collision(jugador, e):
                e.take_damage(e.hp)
                if not getattr(e, 'active', True) and not isinstance(e, Proyectil):
                    try:
                        e.image_right = assets["fant_herido"]
                        e.image_left = pygame.transform.flip(assets["fant_herido"], True, False)
                        e.current_image = e.image_right
                    except Exception:
                        pass
                    if not jefe_spawned:
                        enemies_killed += 1

        if jefe and jefe.active and check_pixel_collision(jugador, jefe):
            if not getattr(jugador, 'has_hit_boss', False):
                jefe.take_damage(1)
                jugador.has_hit_boss = True

    for e in enemies:
        if getattr(e, 'active', False) and check_pixel_collision(jugador, e):
            if jugador.invuln_timer <= 0:
                jugador.lives -= 1
                jugador.invuln_timer = jugador.invuln_duration

    return enemies_killed


def actualizar_estado_partida(jugador, jefe, enemies, survival_timer, enemies_crossed, game_over, game_won, assets):
    """Evalúa las condiciones de victoria o derrota y aplica cambios de sprite de fin de juego."""
    if not game_over and not game_won:
        if (jefe and jefe.dead) or survival_timer <= 0:
            game_won = True
            for ee in enemies:
                try:
                    ee.image_right = assets["fant_herido"]
                    ee.image_left = pygame.transform.flip(assets["fant_herido"], True, False)
                    ee.current_image = ee.image_right
                except Exception:
                    pass

    if not game_over and not game_won and (jugador.lives <= 0 or enemies_crossed >= 10):
        game_over = True
        try:
            jugador.image_right = assets["gato_herido"]
            jugador.image_left = pygame.transform.flip(assets["gato_herido"], True, False)
            jugador.current_image = jugador.image_left if jugador.facing == 'left' else jugador.image_right
            jugador.rect = jugador.current_image.get_rect(center=jugador.rect.center)
            jugador.hitbox = jugador.rect.inflate(-jugador.hitbox_padding * 3, -jugador.hitbox_padding * 3) if jugador.hitbox_padding > 0 else jugador.rect.copy()
        except Exception:
            pass

        for e in enemies:
            try:
                e.image_right = assets["fant_gana"]
                e.image_left = pygame.transform.flip(assets["fant_gana"], True, False)
                e.current_image = e.image_right
            except Exception:
                pass

    return game_over, game_won


def renderizar_escena(screen, font, game_over_font, victory_font, assets, jugador, jefe, enemies, survival_timer, enemies_killed, enemies_crossed, game_over, game_won, dt):
    """Renderiza todos los componentes visuales del escenario, sprites e interfaz de usuario."""
    screen.blit(assets["fondo"], (0, 0))

    for e in enemies:
        e.draw(screen)

    if jefe and jefe.active:
        jefe.draw(screen)

    if game_over:
        jugador.draw(screen)
    else:
        draw_player = True
        if jugador.invuln_timer > 0:
            draw_player = (int(jugador.invuln_timer * 10) % 2) == 0
        if draw_player:
            jugador.draw(screen)

    dibujar_mensaje_guardado(screen, font, dt)
    dibujar_hud(screen, font, jugador, jefe, survival_timer, enemies_killed, enemies_crossed)
    dibujar_pantalla_final(screen, font, game_over_font, victory_font, game_over, game_won)

    pygame.display.flip()


def main():
    """Punto de entrada principal: inicializa el juego y coordina el bucle de eventos."""
    db_usuario = os.getenv("DB_USUARIO")
    db_password = os.getenv("DB_PASSWORD")
    print(f"Conectando Usuario: {db_usuario}")

    screen = init_screen(1280, 720)
    db.init_db()
    last_pos = db.cargar_partida()

    assets = cargar_assets(screen)

    start_x, start_y = (int(last_pos[0]), int(last_pos[1])) if last_pos else screen.get_rect().center
    jugador = Jugador(start_x, start_y, velocidad=350, image=assets["gato_normal"], alt_image=assets["gato_salta"], attack_image=assets["gato_ataque"], hitbox_padding=10)

    font = pygame.font.Font(None, 24)
    game_over_font = pygame.font.Font(None, 72)
    victory_font = pygame.font.Font(None, 72)

    clock = pygame.time.Clock()
    enemies = []
    spawn_timer = 0.0
    enemies_crossed = 0
    enemies_killed = 0
    survival_timer = 120.0
    game_won = False
    game_over = False
    running = True

    jefe = None
    jefe_spawned = False

    def restart():
        nonlocal spawn_timer, enemies_crossed, enemies_killed, survival_timer, game_over, game_won, jefe, jefe_spawned
        enemies.clear()
        jefe = None
        jefe_spawned = False
        spawn_timer = 0.0
        enemies_crossed = 0
        enemies_killed = 0
        survival_timer = 120.0
        game_over = False
        game_won = False

        jugador.lives = 9
        jugador.invuln_timer = 0.0
        jugador.attack_timer = 0.0

        try:
            jugador.image_right = assets["gato_normal"]
            jugador.image_left = pygame.transform.flip(assets["gato_normal"], True, False)
            jugador.alt_right = assets["gato_salta"]
            jugador.alt_left = pygame.transform.flip(assets["gato_salta"], True, False)
            jugador.attack_right = assets["gato_ataque"]
            jugador.attack_left = pygame.transform.flip(assets["gato_ataque"], True, False)
            jugador.current_image = jugador.image_left if jugador.facing == 'left' else jugador.image_right
        except Exception:
            pass

        jugador.rect.center = (start_x, start_y)
        jugador.hitbox.center = jugador.rect.center

    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_j and (game_over or game_won):
                restart()

        keys = pygame.key.get_pressed()

        if not game_over:
            jugador.handle_input(keys, dt)

        if not game_over and not game_won:
            jefe, jefe_spawned, spawn_timer, enemies_crossed = actualizar_spawns_y_enemigos(
                dt, screen, enemies, jefe, jefe_spawned, spawn_timer, enemies_killed, enemies_crossed, assets
            )
            enemies_killed = procesar_colisiones(jugador, jefe, enemies, jefe_spawned, enemies_killed, assets)

            if jugador.invuln_timer > 0:
                jugador.invuln_timer -= dt

            survival_timer = max(0.0, survival_timer - dt)

        game_over, game_won = actualizar_estado_partida(
            jugador, jefe, enemies, survival_timer, enemies_crossed, game_over, game_won, assets
        )

        jugador.hitbox.clamp_ip(screen.get_rect())
        jugador.rect.center = jugador.hitbox.center

        renderizar_escena(
            screen, font, game_over_font, victory_font, assets, jugador, jefe, enemies,
            survival_timer, enemies_killed, enemies_crossed, game_over, game_won, dt
        )

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
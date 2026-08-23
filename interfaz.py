import pygame
import db


def dibujar_mensaje_guardado(screen, font, dt):
    """Dibuja la notificación flotante de guardado en la esquina superior izquierda si está activa."""
    if db.save_message_timer > 0:
        db.save_message_timer -= dt
        text = font.render(db.save_message, True, (255, 255, 255))
        screen.blit(text, (10, 10))


def dibujar_hud(screen, font, jugador, jefe, survival_timer, enemies_killed, enemies_crossed):
    """Renderiza toda la interfaz durante la partida: vidas, tiempo, contadores y vida del Jefe."""
    # Vidas en pantalla
    lives_text = font.render(f"Vidas: {jugador.lives}", True, (255, 255, 255))
    screen.blit(lives_text, (10, 40))

    # Barra de vida del Jefe Final en la parte superior central
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

    # Contadores en el lado derecho
    x_right_margin = 10
    # Fantasmas muertos: VERDE, arriba a la derecha
    killed_text = font.render(f"Fantasmas muertos: {enemies_killed}/15", True, (0, 255, 0))
    killed_rect = killed_text.get_rect()
    killed_rect.topright = (screen.get_width() - x_right_margin, 40)
    screen.blit(killed_text, killed_rect)

    # Fantasmas que escaparon: BLANCO, debajo del contador de muertos
    escaped_text = font.render(f"Fantasmas que escaparon: {enemies_crossed}/10", True, (255, 255, 255))
    escaped_rect = escaped_text.get_rect()
    escaped_rect.topright = (screen.get_width() - x_right_margin, 40 + killed_rect.height + 4)
    screen.blit(escaped_text, escaped_rect)


def dibujar_pantalla_final(screen, font, game_over_font, victory_font, game_over, game_won):
    """Muestra el cartel de Derrota o Victoria y la instrucción para reiniciar la partida."""
    if game_over:
        msg = game_over_font.render("¡Derrota!", True, (255, 0, 0))
        msg_rect = msg.get_rect(center=screen.get_rect().center)
        screen.blit(msg, msg_rect)

        restart_text = font.render("Presiona J para volver a jugar", True, (255, 255, 255))
        restart_rect = restart_text.get_rect(center=(screen.get_rect().centerx, msg_rect.bottom + 20))
        screen.blit(restart_text, restart_rect)

    elif game_won:
        msg = victory_font.render("¡Victoria!", True, (0, 200, 0))
        msg_rect = msg.get_rect(center=screen.get_rect().center)
        screen.blit(msg, msg_rect)

        restart_text = font.render("Presiona J para volver a jugar", True, (255, 255, 255))
        restart_rect = restart_text.get_rect(center=(screen.get_rect().centerx, msg_rect.bottom + 20))
        screen.blit(restart_text, restart_rect)

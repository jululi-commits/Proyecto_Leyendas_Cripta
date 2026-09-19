import sys
from pathlib import Path

# Garantizar que el directorio 'src' esté en sys.path al ejecutar directamente
SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import pygame

from core.estados import EstadoJuego
from core.gestor_escenas import GestorEscenas
from escenas.escena_game_over import EscenaGameOver
from escenas.escena_juego import EscenaJuego

def main() -> None:
    # 1. Inicialización de Pygame
    pygame.init()
    
    ANCHO_VENTANA = 1024
    ALTO_VENTANA = 720
    pantalla = pygame.display.set_mode((ANCHO_VENTANA, ALTO_VENTANA))
    pygame.display.set_caption("Gatito VS los Fantasmas")
    
    reloj = pygame.time.Clock()
    FPS = 60

    # 2. Instanciación del GestorEscenas y registro en el diccionario de estados
    gestor = GestorEscenas()

    #gestor.agregar_escena(EstadoJuego.MENU, EscenaMenu())
    gestor.agregar_escena(EstadoJuego.JUEGO, EscenaJuego())
    gestor.agregar_escena(EstadoJuego.GAME_OVER, EscenaGameOver())

    # 3. Establecer la escena inicial
    #gestor.cambiar_escena(EstadoJuego.MENU)
    gestor.cambiar_escena(EstadoJuego.JUEGO)

    # 4. Bucle principal del juego (Game Loop)
    ejecutando = True
    while ejecutando:
        # Cálculo del tiempo delta (dt) en segundos
        dt = reloj.tick(FPS) / 1000.0

        # Captura y filtrado de eventos
        eventos = pygame.event.get()
        for evento in eventos:
            if evento.type == pygame.QUIT:
                ejecutando = False

        # Delegación del ciclo de vida al GestorEscenas
        gestor.manejar_eventos(eventos)
        gestor.actualizar(dt)
        gestor.dibujar(pantalla)

        # Actualización de pantalla
        pygame.display.flip()

    # 5. Cierre limpio
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
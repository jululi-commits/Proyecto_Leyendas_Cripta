import pygame
import sys
import sqlite3

#conexion
conexion=sqlite3.connect("partidas.db")
cursor=conexion.cursor()


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

def main():
    screen = init_screen(800, 600)
    image, image_rect = load_centered_image("Assets/gato_normal.png", screen)

    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill((0, 0, 0))
        screen.blit(image, image_rect)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

class Personaje:
    def __init__(self, x, y, velocidad):
        # Coordenada horizontal del personaje
        self.x = x
        # Coordenada vertical del personaje
        self.y = y
        # Velocidad de movimiento del personaje
        self.velocidad = velocidad

class Jugador(Personaje):
    def __init__(self, x, y, velocidad):
        # Inicializa usando el constructor de la clase base Personaje
        super().__init__(x, y, velocidad)

class Enemigo(Personaje):
    def __init__(self, x, y, velocidad):
        # Inicializa usando el constructor de la clase base Personaje
        super().__init__(x, y, velocidad)




        
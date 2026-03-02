import pygame
from camera import Camera

# ---------- INIT ----------
pygame.init()

WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2D Parking System")

# ---------- COLORS ----------
WHITE = (255,255,255)
GREEN = (0,200,0)
BLACK = (0,0,0)

# ---------- PARKING SLOTS ----------
# ---------- PARKING SLOTS ----------
parking_slots = []

slot_width = 80
slot_height = 150
gap_x = 40
gap_y = 60
start_x = 150
start_y = 100
rows=2
cols=4

# create 8 parking slots automatically
for i in range(rows):
    for j in range(cols):
        x = start_x + j * (slot_width + gap_x)
        y = start_y + i * (slot_height + gap_y)

        slot = pygame.Rect(x, y, slot_width, slot_height)
        parking_slots.append(slot)
camera = Camera(100, 300)  # left side of boundary
# ---------- GAME LOOP ----------
running = True
while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    keys = pygame.key.get_pressed()

    if keys[pygame.K_LEFT]:
        camera.rotate("left")

    if keys[pygame.K_RIGHT]:
        camera.rotate("right")
    # background
    screen.fill(BLACK)

    # boundary
    pygame.draw.rect(screen, WHITE, (50,50,800,500), 4)

    # draw slots
    for slot in parking_slots:
        pygame.draw.rect(screen, GREEN, slot, 3)
    camera.draw_camera(screen)
    camera.draw_fov(screen)
    pygame.display.update()

pygame.quit()
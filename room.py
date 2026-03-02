import pygame
from camera import Camera
from visibility import is_slot_visible, is_blocked

pygame.init()

WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2D Smart Parking Surveillance")

WHITE = (255,255,255)
GREEN = (0,200,0)
BLACK = (0,0,0)
RED = (255,0,0)
GRAY = (150,150,150)

# ---------- PARKING SLOTS ----------
parking_slots = []

slot_width = 80
slot_height = 150
gap_x = 40
gap_y = 60
start_x = 150
start_y = 100
rows = 2
cols = 4

for i in range(rows):
    for j in range(cols):
        x = start_x + j * (slot_width + gap_x)
        y = start_y + i * (slot_height + gap_y)
        slot = pygame.Rect(x, y, slot_width, slot_height)
        parking_slots.append(slot)

# ---------- OBSTACLE ----------
obstacle = pygame.Rect(450, 250, 40, 150)

# ---------- CAMERA ----------
camera = Camera(100, 300)

running = True
clock = pygame.time.Clock()

while running:

    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        camera.rotate("left")
    if keys[pygame.K_RIGHT]:
        camera.rotate("right")

    screen.fill(BLACK)

    # Boundary
    pygame.draw.rect(screen, WHITE, (50,50,800,500), 4)

    # Draw obstacle
    pygame.draw.rect(screen, GRAY, obstacle)

    # Draw parking slots with visibility logic
    for slot in parking_slots:

        visible = is_slot_visible(slot, camera)

        blocked = is_blocked(camera, slot, obstacle)

        if visible and not blocked:
            pygame.draw.rect(screen, RED, slot, 3)
        else:
            pygame.draw.rect(screen, GREEN, slot, 3)

    camera.draw_camera(screen)
    camera.draw_fov(screen)

    pygame.display.update()

pygame.quit()
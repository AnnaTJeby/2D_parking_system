import pygame
from camera import Camera
from visibility import is_slot_visible, is_blocked, is_car_detected

pygame.init()

WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2D Smart Parking Surveillance")

WHITE = (255,255,255)
GREEN = (0,200,0)
BLACK = (0,0,0)
RED = (255,0,0)
GRAY = (150,150,150)
YELLOW = (255, 220, 0)

PARKING_LANE_BOUNDS = pygame.Rect(50, 50, 800, 500)
CAMERA_FOV = 90
CAMERA_RANGE = 320

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
# ---------- MOVING CAR ----------
# Start from the top-left corner entrance inside the boundary
car = pygame.Rect(60, 60, 40, 60)
car_speed = 4

running = True
clock = pygame.time.Clock()

while running:

    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    if keys[pygame.K_a]:
        camera.rotate("left")
    if keys[pygame.K_d]:
        camera.rotate("right")

    screen.fill(BLACK)

    # Boundary
    pygame.draw.rect(screen, WHITE, PARKING_LANE_BOUNDS, 4)

    # Drive car with arrow keys
    dx = 0
    dy = 0
    if keys[pygame.K_LEFT]:
        dx -= car_speed
    if keys[pygame.K_RIGHT]:
        dx += car_speed
    if keys[pygame.K_UP]:
        dy -= car_speed
    if keys[pygame.K_DOWN]:
        dy += car_speed

    previous_pos = car.copy()
    car.x += dx
    car.y += dy

    # Keep car inside boundary
    car.left = max(car.left, PARKING_LANE_BOUNDS.left)
    car.top = max(car.top, PARKING_LANE_BOUNDS.top)
    car.right = min(car.right, PARKING_LANE_BOUNDS.right)
    car.bottom = min(car.bottom, PARKING_LANE_BOUNDS.bottom)

    # Prevent moving through obstacle
    if car.colliderect(obstacle):
        car = previous_pos

    # Draw obstacle
    pygame.draw.rect(screen, GRAY, obstacle)

    car_detected = is_car_detected(
        car,
        camera,
        obstacle,
        PARKING_LANE_BOUNDS,
        fov=CAMERA_FOV,
        max_distance=CAMERA_RANGE,
    )

    # Draw parking slots with visibility logic
    for slot in parking_slots:

        visible = is_slot_visible(slot, camera, fov=CAMERA_FOV, max_distance=CAMERA_RANGE)

        blocked = is_blocked(camera, slot, obstacle)

        if visible and not blocked:
            pygame.draw.rect(screen, RED, slot, 3)
        else:
            pygame.draw.rect(screen, GREEN, slot, 3)

    camera.draw_camera(screen)
    camera.draw_fov(screen, fov_angle=CAMERA_FOV, distance=CAMERA_RANGE)

    car_color = YELLOW if car_detected else (0, 0, 255)
    pygame.draw.rect(screen, car_color, car)

    font = pygame.font.Font(None, 30)
    status_text = "Car detected: YES" if car_detected else "Car detected: NO"
    status_color = YELLOW if car_detected else WHITE
    screen.blit(font.render(status_text, True, status_color), (20, 20))

    pygame.display.update()

pygame.quit()

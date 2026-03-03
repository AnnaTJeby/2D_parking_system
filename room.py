import pygame
from camera import Camera
from visibility import is_slot_visible, is_blocked, is_car_detected

pygame.init()

WIDTH, HEIGHT = 1000, 900
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2D Smart Parking Surveillance")

BASE_WIDTH, BASE_HEIGHT = 900, 600
scale_x = WIDTH / BASE_WIDTH
scale_y = HEIGHT / BASE_HEIGHT
scale = min(scale_x, scale_y)

def sx(value):
    return max(1, int(value * scale_x))

def sy(value):
    return max(1, int(value * scale_y))

def ss(value):
    return max(1, int(value * scale))

WHITE = (255,255,255)
GREEN = (0,200,0)
BLACK = (0,0,0)
RED = (255,0,0)
GRAY = (150,150,150)
YELLOW = (255, 220, 0)
BLUE = (0, 140, 255)
ORANGE = (255, 140, 0)
DARK_GRAY = (40, 40, 40)

lane_margin_x = sx(50)
lane_margin_top = sy(80)
lane_margin_bottom = sy(45)
PARKING_LANE_BOUNDS = pygame.Rect(
    lane_margin_x,
    lane_margin_top,
    WIDTH - (2 * lane_margin_x),
    HEIGHT - lane_margin_top - lane_margin_bottom,
)
CAMERA_FOV = 90
CAMERA_RANGE = ss(320)
CAR_SPEED = max(2, ss(4))
CAR_SIZE = (ss(40), ss(60))
ENTRY_POINT = (PARKING_LANE_BOUNDS.left + ss(10), PARKING_LANE_BOUNDS.top + ss(10))
ADD_CAR_BUTTON = pygame.Rect(WIDTH - sx(220), sy(10), sx(200), sy(42))

# ---------- PARKING SLOTS ----------
parking_slots = []

slot_width = ss(80)
slot_height = ss(150)
gap_x = ss(40)
gap_y = ss(60)
rows = 2
cols = 4
middle_gap = ss(150)

layout_width = cols * slot_width + (cols - 1) * gap_x + middle_gap
start_x = PARKING_LANE_BOUNDS.centerx - layout_width // 2
start_y = PARKING_LANE_BOUNDS.top + sy(55)

for i in range(rows):
    for j in range(cols):
        x = start_x + j * (slot_width + gap_x)

        # Add extra gap after 2nd column
        if j >= 2:
            x += middle_gap

        y = start_y + i * (slot_height + gap_y)
        slot = pygame.Rect(x, y, slot_width, slot_height)
        parking_slots.append(slot)

left_column_right = parking_slots[1].right
right_column_left = parking_slots[2].left

slots_center_x = (left_column_right + right_column_left) // 2
slots_center_y = int(sum(slot.centery for slot in parking_slots) / len(parking_slots))
# ---------- OBSTACLE / RIGHT WALL ----------
obstacle = pygame.Rect(
    PARKING_LANE_BOUNDS.right - ss(10),
    PARKING_LANE_BOUNDS.top,
    ss(10),
    PARKING_LANE_BOUNDS.height,
)

# ---------- CAMERA ----------
camera = Camera(slots_center_x, slots_center_y)

# ---------- CAR STATE ----------
active_car = None
parked_cars = []
occupied_slots = set()
scanned_slots = set()
status_message = "Click Add Car to enter a new vehicle."
previous_park_key = False
popup_message = ""
popup_until = 0
vehicle_alert_active = False
alert_played = False
ok_button = pygame.Rect(WIDTH//2 - 50, HEIGHT//2 + 20, 100, 40)
ok_button = pygame.Rect(WIDTH // 2 - sx(70), HEIGHT // 2 + sy(20), sx(140), sy(50))
font = pygame.font.Font(None, ss(34))
small_font = pygame.font.Font(None, ss(26))
HUD_LEFT = sx(20)
HUD_TOP = sy(8)

running = True
clock = pygame.time.Clock()

while running:

    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if ADD_CAR_BUTTON.collidepoint(event.pos):
                if active_car is None:
                    new_car = pygame.Rect(ENTRY_POINT[0], ENTRY_POINT[1], CAR_SIZE[0], CAR_SIZE[1])
                    entry_blocked = new_car.colliderect(obstacle) or any(
                        new_car.colliderect(parking_slots[idx]) for idx in occupied_slots
                    )
                    if entry_blocked:
                        status_message = "Entry is blocked. Move parked cars/camera and try again."
                    else:
                        active_car = new_car
                        status_message = "New car added. Use arrow keys to drive, P to park."
                else:
                    status_message = "Park the current car first before adding a new one."

    keys = pygame.key.get_pressed()
    if keys[pygame.K_a]:
        camera.rotate("left")
    if keys[pygame.K_d]:
        camera.rotate("right")

    screen.fill(BLACK)

    # Boundary
    pygame.draw.rect(screen, WHITE, PARKING_LANE_BOUNDS, 4)

    # Drive active car with arrow keys
    if active_car is not None:
        dx = 0
        dy = 0
        if keys[pygame.K_LEFT]:
            dx -= CAR_SPEED
        if keys[pygame.K_RIGHT]:
            dx += CAR_SPEED
        if keys[pygame.K_UP]:
            dy -= CAR_SPEED
        if keys[pygame.K_DOWN]:
            dy += CAR_SPEED

        previous_pos = active_car.copy()
        active_car.x += dx
        active_car.y += dy

        # Keep car inside parking lane boundary
        active_car.left = max(active_car.left, PARKING_LANE_BOUNDS.left)
        active_car.top = max(active_car.top, PARKING_LANE_BOUNDS.top)
        active_car.right = min(active_car.right, PARKING_LANE_BOUNDS.right)
        active_car.bottom = min(active_car.bottom, PARKING_LANE_BOUNDS.bottom)

        # Prevent crossing obstacle/right wall or occupied parking slots
        blocked_by_taken_slot = any(
            active_car.colliderect(parking_slots[idx]) for idx in occupied_slots
        )
        if active_car.colliderect(obstacle) or blocked_by_taken_slot:
            if blocked_by_taken_slot:
                popup_message = "Warning: Slot already occupied."
                popup_until = pygame.time.get_ticks() + 1800
            active_car = previous_pos

    park_key = keys[pygame.K_p]
    if active_car is not None and park_key and not previous_park_key:
        selected_slot = None
        for idx, slot in enumerate(parking_slots):
            if slot.collidepoint(active_car.center):
                selected_slot = idx
                break

        if selected_slot is None:
            status_message = "Move the car into a parking slot, then press P."
        elif selected_slot in occupied_slots:
            status_message = "Slot is already occupied. Choose a free slot."
            popup_message = "Warning: Slot already occupied."
            popup_until = pygame.time.get_ticks() + 1800
        else:
            parked_car = active_car.copy()
            parked_car.center = parking_slots[selected_slot].center
            parked_cars.append(parked_car)
            occupied_slots.add(selected_slot)
            active_car = None
            status_message = f"Car parked in slot {selected_slot + 1}."
    previous_park_key = park_key

    # Draw obstacle
    pygame.draw.rect(screen, GRAY, obstacle)

    # Draw parking slots with visibility logic
    for idx, slot in enumerate(parking_slots):
        visible = is_slot_visible(slot, camera, fov=CAMERA_FOV, max_distance=CAMERA_RANGE)
        blocked = is_blocked(camera, slot, obstacle)
        if visible and not blocked:
            scanned_slots.add(idx)

        if idx in occupied_slots:
            pygame.draw.rect(screen, ORANGE, slot, 0)
            pygame.draw.rect(screen, WHITE, slot, 2)
        elif visible and not blocked:
            pygame.draw.rect(screen, RED, slot, 3)
        else:
            pygame.draw.rect(screen, GREEN, slot, 3)
    if not vehicle_alert_active:
        camera.auto_rotate()
    camera.draw_camera(screen)
    camera.draw_fov(screen, fov_angle=CAMERA_FOV, distance=CAMERA_RANGE)

    all_cars = parked_cars + ([active_car] if active_car is not None else [])
    detected_count = 0
    for parked in parked_cars:
        car_seen = is_car_detected(
            parked,
            camera,
            obstacle,
            PARKING_LANE_BOUNDS,
            fov=CAMERA_FOV,
            max_distance=CAMERA_RANGE,
        )
        if car_seen:
            detected_count += 1
        pygame.draw.rect(screen, YELLOW if car_seen else BLUE, parked)

    if active_car is not None:
        active_seen = is_car_detected(
            active_car,
            camera,
            obstacle,
            PARKING_LANE_BOUNDS,
            fov=CAMERA_FOV,
            max_distance=CAMERA_RANGE,
        )
        if active_seen:
            detected_count += 1
        pygame.draw.rect(screen, YELLOW if active_seen else BLUE, active_car)

    pygame.draw.rect(screen, DARK_GRAY, ADD_CAR_BUTTON, border_radius=6)
    pygame.draw.rect(screen, WHITE, ADD_CAR_BUTTON, 2, border_radius=6)
    add_label = small_font.render("Add Car", True, WHITE)
    add_label_rect = add_label.get_rect(center=ADD_CAR_BUTTON.center)
    screen.blit(add_label, add_label_rect)

    total_slots = len(parking_slots)
    if len(scanned_slots) == total_slots:
        free_slots = total_slots - len(occupied_slots)
        top_text = f"Free Slots: {free_slots}/{total_slots}"
    else:
        top_text = f"Scanning lot: {len(scanned_slots)}/{total_slots} slots covered"
    top_surface = font.render(top_text, True, WHITE)
    top_y = HUD_TOP
    screen.blit(top_surface, (HUD_LEFT, top_y))

    detect_text = f"Cars detected by camera: {detected_count}/{len(all_cars)}"
    detect_surface = small_font.render(detect_text, True, YELLOW)
    detect_y = top_y + top_surface.get_height() + 2
    max_detect_y = PARKING_LANE_BOUNDS.top - detect_surface.get_height() - 4
    detect_y = min(detect_y, max_detect_y)
    screen.blit(detect_surface, (HUD_LEFT, detect_y))
    status_surface = small_font.render(status_message, True, WHITE)
    status_y = HEIGHT - status_surface.get_height() - sy(10)
    screen.blit(status_surface, (HUD_LEFT, status_y))

    if pygame.time.get_ticks() < popup_until:
        popup_rect = pygame.Rect(
            WIDTH // 2 - sx(240),
            PARKING_LANE_BOUNDS.top + sy(20),
            sx(480),
            sy(70),
        )
        pygame.draw.rect(screen, (170, 20, 20), popup_rect, border_radius=8)
        pygame.draw.rect(screen, WHITE, popup_rect, 2, border_radius=8)
        popup_label = font.render(popup_message, True, WHITE)
        popup_label_rect = popup_label.get_rect(center=popup_rect.center)
        screen.blit(popup_label, popup_label_rect)

    pygame.display.update()

pygame.quit()

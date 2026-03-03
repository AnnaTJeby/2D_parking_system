import pygame
import math
from camera import Camera
from visibility import is_slot_visible, is_blocked, is_car_detected

pygame.init()

info = pygame.display.Info()
WIDTH = int(info.current_w * 0.9)
HEIGHT = int(info.current_h * 0.9)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2D Smart Parking Surveillance")

BASE_WIDTH, BASE_HEIGHT = 900, 900
scale_x = WIDTH / BASE_WIDTH
scale_y = HEIGHT / BASE_HEIGHT
scale = min(scale_x, scale_y)

def sx(value):
    return max(1, int(value * scale))

def sy(value):
    return max(1, int(value * scale))

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
CAR_SIZE = (ss(72), ss(28))
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
active_car_angle = 0.0
wheel_phase = 0.0
parked_cars = []
parked_car_slots = []
occupied_slots = set()
scanned_slots = set()
status_message = "Click Add Car to enter a new vehicle."
previous_park_key = False
popup_message = ""
popup_until = 0
popup_color = (170, 20, 20)
assigned_slot_idx = None
vehicle_alert_active = False
booked_alert_slots = set()
booking_popup_until = 0
BOOKING_POPUP_MS = 900
font = pygame.font.SysFont("Segoe UI Symbol", ss(34))
small_font = pygame.font.SysFont("Segoe UI Symbol", ss(26))
HUD_LEFT = sx(20)
HUD_TOP = sy(8)

# ---------- ON-SCREEN DRIVE CONTROLS ----------
CTRL_W = sx(60)      
CTRL_H = sy(50)      
CTRL_GAP = sx(12)    
# ---------- CONTROL PANEL POSITION ----------
slots_bottom = max(slot.bottom for slot in parking_slots)

CONTROL_BOX_WIDTH = sx(320)
CONTROL_BOX_HEIGHT = sy(240)

CONTROL_BOX_X = PARKING_LANE_BOUNDS.centerx - CONTROL_BOX_WIDTH // 2
CONTROL_BOX_Y = slots_bottom + sy(100)
control_box = pygame.Rect(
    CONTROL_BOX_X,
    CONTROL_BOX_Y,
    CONTROL_BOX_WIDTH,
    CONTROL_BOX_HEIGHT
)
CTRL_CENTER_X = PARKING_LANE_BOUNDS.centerx
cluster_height = CTRL_H * 2 + CTRL_GAP
CTRL_TOP = control_box.centery - cluster_height // 2
bottom_row_width = CTRL_W * 3 + CTRL_GAP * 2
bottom_start_x = CTRL_CENTER_X - bottom_row_width // 2
bottom_y = CTRL_TOP + CTRL_H + CTRL_GAP

LEFT_BUTTON = pygame.Rect(
    bottom_start_x,
    bottom_y,
    CTRL_W,
    CTRL_H,
)

DOWN_BUTTON = pygame.Rect(
    bottom_start_x + CTRL_W + CTRL_GAP,
    bottom_y,
    CTRL_W,
    CTRL_H,
)

RIGHT_BUTTON = pygame.Rect(
    bottom_start_x + (CTRL_W + CTRL_GAP) * 2,
    bottom_y,
    CTRL_W,
    CTRL_H,
)


UP_BUTTON = pygame.Rect(
    CTRL_CENTER_X - CTRL_W // 2,
    CTRL_TOP,
    CTRL_W,
    CTRL_H,
)


pygame.draw.rect(screen, (25, 25, 25), control_box, border_radius=10)
pygame.draw.rect(screen, WHITE, control_box, 2, border_radius=10)

title_surface = small_font.render("Vehicle Controls", True, WHITE)
title_rect = title_surface.get_rect(center=(control_box.centerx, control_box.y + sy(15)))
screen.blit(title_surface, title_rect)
def draw_control_button(rect, direction, enabled, active):
    if not enabled:
        fill = (60, 60, 60)
        border = (120, 120, 120)
        arrow_color = (150, 150, 150)
    elif active:
        fill = (35, 120, 210)
        border = WHITE
        arrow_color = WHITE
    else:
        fill = DARK_GRAY
        border = WHITE
        arrow_color = WHITE

    # Draw button
    pygame.draw.rect(screen, fill, rect, border_radius=10)
    pygame.draw.rect(screen, border, rect, 2, border_radius=10)

    cx, cy = rect.center
    size = rect.width // 3

    if direction == "UP":
        points = [
            (cx, cy - size),
            (cx - size, cy + size),
            (cx + size, cy + size),
        ]

    elif direction == "DOWN":
        points = [
            (cx - size, cy - size),
            (cx + size, cy - size),
            (cx, cy + size),
        ]

    elif direction == "LEFT":
        points = [
            (cx - size, cy),
            (cx + size, cy - size),
            (cx + size, cy + size),
        ]

    elif direction == "RIGHT":
        points = [
            (cx - size, cy - size),
            (cx - size, cy + size),
            (cx + size, cy),
        ]

    pygame.draw.polygon(screen, arrow_color, points)
    

def draw_animated_car(screen, rect, angle, detected=False, wheel_phase=0.0):
    pad = 18
    canvas_w = rect.width + pad * 2
    canvas_h = rect.height + pad * 2
    car_surface = pygame.Surface((canvas_w, canvas_h), pygame.SRCALPHA)

    body_color = YELLOW if detected else BLUE
    body_rect = pygame.Rect(pad, pad, rect.width, rect.height)
    cabin_rect = pygame.Rect(
        body_rect.x + int(body_rect.width * 0.28),
        body_rect.y - int(body_rect.height * 0.28),
        int(body_rect.width * 0.44),
        int(body_rect.height * 0.55),
    )

    # Side-view body and cabin
    pygame.draw.rect(car_surface, body_color, body_rect, border_radius=8)
    pygame.draw.rect(car_surface, (35, 70, 120), cabin_rect, border_radius=6)

    # Side windows
    glass_color = (170, 215, 240)
    window_w = int(cabin_rect.width * 0.42)
    left_window = pygame.Rect(cabin_rect.x + 3, cabin_rect.y + 3, window_w, cabin_rect.height - 6)
    right_window = pygame.Rect(cabin_rect.right - window_w - 3, cabin_rect.y + 3, window_w, cabin_rect.height - 6)
    pygame.draw.rect(car_surface, glass_color, left_window, border_radius=3)
    pygame.draw.rect(car_surface, glass_color, right_window, border_radius=3)

    # Front/rear lights in side profile
    pygame.draw.rect(car_surface, (255, 240, 120), (body_rect.right - 3, body_rect.y + 6, 3, 7), border_radius=2)
    pygame.draw.rect(car_surface, (255, 100, 100), (body_rect.x, body_rect.y + 6, 3, 7), border_radius=2)

    wheel_size = (14, 9)
    wheel_positions = [
        (body_rect.x + 8, body_rect.bottom - 4),
        (body_rect.right - 22, body_rect.bottom - 4),
    ]
    spoke_rad = math.radians(wheel_phase)
    spoke_dx = int(4 * math.cos(spoke_rad))
    spoke_dy = int(2 * math.sin(spoke_rad))
    for wx, wy in wheel_positions:
        wrect = pygame.Rect(wx, wy, wheel_size[0], wheel_size[1])
        pygame.draw.ellipse(car_surface, (20, 20, 20), wrect)
        center = wrect.center
        pygame.draw.line(
            car_surface,
            (180, 180, 180),
            (center[0] - spoke_dx, center[1] - spoke_dy),
            (center[0] + spoke_dx, center[1] + spoke_dy),
            2,
        )

    rotated = pygame.transform.rotate(car_surface, -angle)
    rotated_rect = rotated.get_rect(center=rect.center)
    screen.blit(rotated, rotated_rect.topleft)

running = True
clock = pygame.time.Clock()

while running:

    clock.tick(60)
    now = pygame.time.get_ticks()
    vehicle_alert_active = now < booking_popup_until

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not vehicle_alert_active and ADD_CAR_BUTTON.collidepoint(event.pos):
                if active_car is None:
                    free_slots = [idx for idx in range(len(parking_slots)) if idx not in occupied_slots]
                    if not free_slots:
                        status_message = "No free slots available right now."
                        popup_message = "Parking Full"
                        popup_color = (170, 20, 20)
                        popup_until = now + 1800
                        continue

                    new_car = pygame.Rect(ENTRY_POINT[0], ENTRY_POINT[1], CAR_SIZE[0], CAR_SIZE[1])
                    entry_blocked = new_car.colliderect(obstacle) or any(
                        new_car.colliderect(parking_slots[idx]) for idx in occupied_slots
                    )
                    if entry_blocked:
                        status_message = "Entry is blocked. Move parked cars/camera and try again."
                    else:
                        assigned_slot_idx = free_slots[0]
                        active_car = new_car
                        active_car_angle = 0.0
                        status_message = f"Camera instruction: Goto slot B{assigned_slot_idx + 1}."
                        popup_message = f"Goto slot B{assigned_slot_idx + 1}"
                        popup_color = (20, 90, 170)
                        popup_until = now + 1600
                else:
                    status_message = "Park the current car first before adding a new one."

    keys = pygame.key.get_pressed()
    if not vehicle_alert_active and keys[pygame.K_a]:
        camera.rotate("left")
    if not vehicle_alert_active and keys[pygame.K_d]:
        camera.rotate("right")

    mouse_left_down = pygame.mouse.get_pressed()[0]
    mouse_pos = pygame.mouse.get_pos()
    mouse_up = (
        not vehicle_alert_active
        and mouse_left_down
        and UP_BUTTON.collidepoint(mouse_pos)
    )
    mouse_down = (
        not vehicle_alert_active
        and mouse_left_down
        and DOWN_BUTTON.collidepoint(mouse_pos)
    )
    mouse_left = (
        not vehicle_alert_active
        and mouse_left_down
        and LEFT_BUTTON.collidepoint(mouse_pos)
    )
    mouse_right = (
        not vehicle_alert_active
        and mouse_left_down
        and RIGHT_BUTTON.collidepoint(mouse_pos)
    )

    screen.fill(BLACK)
    # Draw control panel box
    pygame.draw.rect(screen, (25, 25, 25), control_box, border_radius=10)
    pygame.draw.rect(screen, WHITE, control_box, 2, border_radius=10)

    title_surface = small_font.render("Vehicle Controls", True, WHITE)
    title_rect = title_surface.get_rect(center=(control_box.centerx, control_box.y + sy(15)))
    screen.blit(title_surface, title_rect)
    # Boundary
    pygame.draw.rect(screen, WHITE, PARKING_LANE_BOUNDS, 4)

    # Drive active car with arrow keys
    if active_car is not None and not vehicle_alert_active:
        dx = 0
        dy = 0
        if keys[pygame.K_LEFT] or mouse_left:
            dx -= CAR_SPEED
        if keys[pygame.K_RIGHT] or mouse_right:
            dx += CAR_SPEED
        if keys[pygame.K_UP] or mouse_up:
            dy -= CAR_SPEED
        if keys[pygame.K_DOWN] or mouse_down:
            dy += CAR_SPEED

        if dx != 0 or dy != 0:
            active_car_angle = math.degrees(math.atan2(dy, dx))
            wheel_phase = (wheel_phase + (abs(dx) + abs(dy)) * 3) % 360

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
                popup_color = (170, 20, 20)
                popup_until = pygame.time.get_ticks() + 1800
            active_car = previous_pos

    park_key = keys[pygame.K_p]
    if active_car is not None and not vehicle_alert_active and park_key and not previous_park_key:
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
            popup_color = (170, 20, 20)
            popup_until = pygame.time.get_ticks() + 1800
        else:
            parked_car = active_car.copy()
            parked_car.center = parking_slots[selected_slot].center
            parked_cars.append({"rect": parked_car, "angle": active_car_angle})
            parked_car_slots.append(selected_slot)
            occupied_slots.add(selected_slot)
            active_car = None
            if assigned_slot_idx is not None and selected_slot == assigned_slot_idx:
                status_message = f"Car parked in assigned slot B{selected_slot + 1}."
            else:
                status_message = f"Car parked in slot B{selected_slot + 1}."
            assigned_slot_idx = None
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

        slot_label = f"B{idx + 1}"
        slot_label_surface = small_font.render(slot_label, True, WHITE)
        slot_label_rect = slot_label_surface.get_rect(midtop=(slot.centerx, slot.top + sy(6)))
        screen.blit(slot_label_surface, slot_label_rect)
    if not vehicle_alert_active:
        camera.auto_rotate()
    camera.draw_camera(screen)
    camera.draw_fov(screen, fov_angle=CAMERA_FOV, distance=CAMERA_RANGE)

    all_cars = parked_cars + ([active_car] if active_car is not None else [])
    detected_count = 0
    for parked, slot_idx in zip(parked_cars, parked_car_slots):
        parked_rect = parked["rect"]
        car_seen = is_car_detected(
            parked_rect,
            camera,
            obstacle,
            PARKING_LANE_BOUNDS,
            fov=CAMERA_FOV,
            max_distance=CAMERA_RANGE,
        )
        if car_seen:
            detected_count += 1
            if slot_idx not in booked_alert_slots:
                booked_alert_slots.add(slot_idx)
                booking_popup_until = now + BOOKING_POPUP_MS
                vehicle_alert_active = True
                status_message = f"Camera confirmed slot {slot_idx + 1} booking."
        draw_animated_car(screen, parked_rect, parked["angle"], detected=car_seen, wheel_phase=0)

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
        draw_animated_car(
            screen,
            active_car,
            active_car_angle,
            detected=active_seen,
            wheel_phase=wheel_phase,
        )

    pygame.draw.rect(screen, DARK_GRAY, ADD_CAR_BUTTON, border_radius=6)
    pygame.draw.rect(screen, WHITE, ADD_CAR_BUTTON, 2, border_radius=6)
    add_label = small_font.render("Add Car", True, WHITE)
    add_label_rect = add_label.get_rect(center=ADD_CAR_BUTTON.center)
    screen.blit(add_label, add_label_rect)

    controls_enabled = active_car is not None and not vehicle_alert_active
    draw_control_button(UP_BUTTON, "UP", controls_enabled, mouse_up)
    draw_control_button(LEFT_BUTTON, "LEFT", controls_enabled, mouse_left)
    draw_control_button(DOWN_BUTTON, "DOWN", controls_enabled, mouse_down)
    draw_control_button(RIGHT_BUTTON, "RIGHT", controls_enabled, mouse_right)

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

    if now < popup_until:
        popup_rect = pygame.Rect(
            WIDTH // 2 - sx(240),
            PARKING_LANE_BOUNDS.top + sy(20),
            sx(480),
            sy(70),
        )
        pygame.draw.rect(screen, popup_color, popup_rect, border_radius=8)
        pygame.draw.rect(screen, WHITE, popup_rect, 2, border_radius=8)
        popup_label = font.render(popup_message, True, WHITE)
        popup_label_rect = popup_label.get_rect(center=popup_rect.center)
        screen.blit(popup_label, popup_label_rect)

    if vehicle_alert_active:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

        booking_rect = pygame.Rect(
            WIDTH // 2 - sx(240),
            HEIGHT // 2 - sy(80),
            sx(480),
            sy(160),
        )
        pygame.draw.rect(screen, (20, 110, 40), booking_rect, border_radius=10)
        pygame.draw.rect(screen, WHITE, booking_rect, 2, border_radius=10)

        booking_title = font.render("One slot booked", True, WHITE)
        booking_title_rect = booking_title.get_rect(
            center=(booking_rect.centerx, booking_rect.centery - sy(10))
        )
        screen.blit(booking_title, booking_title_rect)

        booking_sub = small_font.render("Camera detected parked vehicle", True, WHITE)
        booking_sub_rect = booking_sub.get_rect(
            center=(booking_rect.centerx, booking_rect.centery + sy(25))
        )
        screen.blit(booking_sub, booking_sub_rect)

    pygame.display.update()

pygame.quit()

import math
import pygame

# -------- Angle + Distance Visibility --------
def is_slot_visible(slot, camera, fov=60, max_distance=200):

    center_x = slot.x + slot.width / 2
    center_y = slot.y + slot.height / 2

    dx = center_x - camera.x
    dy = center_y - camera.y

    angle_to_slot = math.degrees(math.atan2(dy, dx))
    distance = math.sqrt(dx**2 + dy**2)

    left_bound = camera.angle - fov/2
    right_bound = camera.angle + fov/2

    if left_bound <= angle_to_slot <= right_bound and distance <= max_distance:
        return True

    return False


# -------- Obstacle Blocking (Occlusion) --------
def is_blocked(camera, slot, obstacle):

    center_x = slot.x + slot.width / 2
    center_y = slot.y + slot.height / 2

    # Create bounding rectangle between camera and slot center
    line_rect = pygame.Rect(
        min(camera.x, center_x),
        min(camera.y, center_y),
        abs(center_x - camera.x),
        abs(center_y - camera.y)
    )

    return line_rect.colliderect(obstacle)
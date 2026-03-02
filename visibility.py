import math
import pygame

def normalize_angle(angle):
    return (angle + 180) % 360 - 180

# -------- Angle + Distance Visibility --------
def is_slot_visible(slot, camera, fov=60, max_distance=200):

    center_x = slot.x + slot.width / 2
    center_y = slot.y + slot.height / 2

    dx = center_x - camera.x
    dy = center_y - camera.y

    angle_to_slot = math.degrees(math.atan2(dy, dx))
    distance = math.sqrt(dx**2 + dy**2)
    
    camera_angle = normalize_angle(camera.angle)
    angle_to_slot = normalize_angle(angle_to_slot)

    angle_difference = normalize_angle(angle_to_slot - camera_angle)

    if abs(angle_difference) <= fov/2 and distance <= max_distance:
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
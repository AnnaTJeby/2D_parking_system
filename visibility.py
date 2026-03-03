import math
import pygame

def normalize_angle(angle):
    return (angle + 180) % 360 - 180

def get_rect_center(target):
    return (target.x + target.width / 2, target.y + target.height / 2)

# -------- Angle + Distance Visibility --------
def is_target_visible(target, camera, fov=60, max_distance=200):
    center_x, center_y = get_rect_center(target)

    dx = center_x - camera.x
    dy = center_y - camera.y

    angle_to_target = math.degrees(math.atan2(dy, dx))
    distance = math.sqrt(dx**2 + dy**2)

    camera_angle = normalize_angle(camera.angle)
    angle_to_target = normalize_angle(angle_to_target)

    angle_difference = normalize_angle(angle_to_target - camera_angle)

    if abs(angle_difference) <= fov/2 and distance <= max_distance:
        return True

    return False

def is_slot_visible(slot, camera, fov=60, max_distance=200):
    return is_target_visible(slot, camera, fov=fov, max_distance=max_distance)

# -------- Obstacle Blocking (Occlusion) --------
def is_blocked(camera, target, obstacle):
    center_x, center_y = get_rect_center(target)
    return obstacle.clipline((camera.x, camera.y), (center_x, center_y))

def is_car_detected(car, camera, obstacle, lane_bounds, fov=60, max_distance=200):
    if not lane_bounds.contains(car):
        return False
    if not is_target_visible(car, camera, fov=fov, max_distance=max_distance):
        return False
    if is_blocked(camera, car, obstacle):
        return False
    return True

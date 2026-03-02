import pygame
import math

class Camera:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = 0  # in degrees

    def draw_camera(self, screen):
        pygame.draw.circle(screen, (0, 0, 255), (self.x, self.y), 10)

    def rotate(self, direction):
        if direction == "left":
            self.angle -= 2
        elif direction == "right":
            self.angle += 2

    def draw_fov(self, screen, fov_angle=60, distance=200):
        start_angle = math.radians(self.angle - fov_angle / 2)
        end_angle = math.radians(self.angle + fov_angle / 2)

        left_x = self.x + distance * math.cos(start_angle)
        left_y = self.y + distance * math.sin(start_angle)

        right_x = self.x + distance * math.cos(end_angle)
        right_y = self.y + distance * math.sin(end_angle)

        surface = pygame.Surface((900, 600), pygame.SRCALPHA)
        pygame.draw.polygon(surface, (0, 255, 0, 80), [
            (self.x, self.y),
            (left_x, left_y),
            (right_x, right_y)
        ])
        screen.blit(surface, (0, 0))
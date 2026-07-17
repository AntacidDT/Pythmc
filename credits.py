"""Pythmc - Credits Screen"""

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
from text_renderer import text_renderer


class CreditsScreen:
    """Credits screen showing project info."""
    
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.time = 0

        self.cam_yaw = 0
        self.world = None
        self.world_loaded = False

    def _ensure_world(self):
        if self.world_loaded:
            return
        from world import World
        self.world = World(seed=42)
        for cx in range(-2, 3):
            for cz in range(-2, 3):
                self.world.get_chunk(cx, cz)
        self.world_loaded = True

    def handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN:
            return "back"
        elif event.type == KEYDOWN:
            if event.key in (K_ESCAPE, K_RETURN):
                return "back"
        return None

    def update(self, dt, mouse_pos):
        self.time += dt
        self.cam_yaw += dt * 4

    def draw(self):
        self._ensure_world()

        # 3D world background
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)

        glClearColor(0.45, 0.55, 0.75, 1.0)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(60, self.screen_w / self.screen_h, 0.1, 500.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        cam_x = math.cos(math.radians(self.cam_yaw)) * 35
        cam_z = math.sin(math.radians(self.cam_yaw)) * 35
        cam_y = 28 + math.sin(self.time * 0.2) * 2
        gluLookAt(cam_x, cam_y, cam_z, 0, 18, 0, 0, 1, 0)

        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.4, 0.4, 0.5, 1.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.9, 0.85, 0.8, 1.0))
        glLightfv(GL_LIGHT0, GL_POSITION, (0.5, 1.0, 0.3, 0.0))

        if self.world:
            for cx in range(-2, 3):
                for cz in range(-2, 3):
                    self.world.get_chunk(cx, cz).draw_opaque()
            for cx in range(-2, 3):
                for cz in range(-2, 3):
                    self.world.get_chunk(cx, cz).draw_transparent()

        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)

        # 2D overlay
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.screen_w, 0, self.screen_h, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # Dark overlay
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(0, 0, 0, 0.3)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(self.screen_w, 0)
        glVertex2f(self.screen_w, self.screen_h)
        glVertex2f(0, self.screen_h)
        glEnd()

        cx = self.screen_w // 2
        y = self.screen_h - 120

        # Title
        text_renderer.draw_text_centered_shadow(cx, y, "PYTHMC", 
                                                "title", (0.3, 1.0, 0.3), (0.0, 0.2, 0.0))
        y -= 60

        # Subtitle
        text_renderer.draw_text_centered(cx, y, "A Minecraft Clone in Python", 
                                        "medium", (0.7, 0.7, 0.75))
        y -= 50

        # Separator line
        glColor4f(0.3, 0.3, 0.4, 0.5)
        glLineWidth(1)
        glBegin(GL_LINES)
        glVertex2f(cx - 200, y)
        glVertex2f(cx + 200, y)
        glEnd()
        y -= 30

        # Credits
        text_renderer.draw_text_centered(cx, y, "CREATED BY", 
                                        "small", (0.5, 0.5, 0.55))
        y -= 25
        text_renderer.draw_text_centered_shadow(cx, y, "AntacidDT", 
                                                "large", (1.0, 1.0, 1.0), (0.2, 0.2, 0.2))
        y -= 15
        text_renderer.draw_text_centered(cx, y, "github.com/AntacidDT", 
                                        "small", (0.4, 0.6, 0.8))
        y -= 50

        # Tools used
        text_renderer.draw_text_centered(cx, y, "BUILT WITH", 
                                        "small", (0.5, 0.5, 0.55))
        y -= 25

        tools = [
            ("Python 3", "Programming Language"),
            ("PyOpenGL", "3D Graphics"),
            ("Pygame", "Window & Input"),
            ("NumPy", "Array Operations"),
            ("noise", "Terrain Generation"),
        ]

        for tool_name, tool_desc in tools:
            text_renderer.draw_text(cx - 100, y, tool_name, 
                                   "medium", (0.9, 0.9, 0.95))
            text_renderer.draw_text(cx + 40, y, f"- {tool_desc}", 
                                   "small", (0.5, 0.5, 0.55))
            y -= 28

        y -= 20

        # Features
        text_renderer.draw_text_centered(cx, y, "FEATURES", 
                                        "small", (0.5, 0.5, 0.55))
        y -= 25

        features = [
            "Procedural World Generation",
            "Multiple Biomes & Structures",
            "Crafting & Inventory System",
            "Entity AI (Passive & Hostile Mobs)",
            "Save/Load World System",
            "Day/Night Cycle",
        ]

        for feat in features:
            text_renderer.draw_text_centered(cx, y, f"- {feat} -", 
                                            "small", (0.6, 0.7, 0.8))
            y -= 22

        y -= 20
        text_renderer.draw_text_centered(cx, y, "Click or press ESC to go back", 
                                        "small", (0.4, 0.4, 0.45))

        glDisable(GL_BLEND)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_FOG)

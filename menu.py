"""Pythmc - Menu System with 3D world background and bitmap font"""

import pygame
from pygame.locals import *
from OpenGL.GL import *
from sounds import sound_manager
from OpenGL.GLU import *
import math
import time
from constants import *
from text_renderer import text_renderer


class Button:
    def __init__(self, x, y, w, h, text, color=(0.25, 0.25, 0.35), hover_color=(0.35, 0.35, 0.5)):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.hovered = False
        self.hover_anim = 0

    def contains(self, mx, my):
        return self.x <= mx <= self.x + self.w and self.y <= my <= self.y + self.h

    def draw(self):
        target = 1.0 if self.hovered else 0.0
        self.hover_anim += (target - self.hover_anim) * 0.15

        r = self.color[0] + (self.hover_color[0] - self.color[0]) * self.hover_anim
        g = self.color[1] + (self.hover_color[1] - self.color[1]) * self.hover_anim
        b = self.color[2] + (self.hover_color[2] - self.color[2]) * self.hover_anim

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Shadow
        glColor4f(0, 0, 0, 0.4)
        self._draw_rect(self.x + 3, self.y - 3, self.w, self.h)

        # Button body (gradient effect)
        glColor3f(r * 0.4, g * 0.4, b * 0.4)
        self._draw_rect(self.x, self.y - 2, self.w, self.h)
        glColor3f(r, g, b)
        self._draw_rect(self.x, self.y, self.w, self.h)

        # Top highlight
        glColor4f(1, 1, 1, 0.1 + self.hover_anim * 0.12)
        self._draw_rect(self.x + 2, self.y + self.h - 8, self.w - 4, 6)

        # Border
        glColor4f(1, 1, 1, 0.15 + self.hover_anim * 0.2)
        glLineWidth(2)
        glBegin(GL_LINE_LOOP)
        glVertex2f(self.x, self.y)
        glVertex2f(self.x + self.w, self.y)
        glVertex2f(self.x + self.w, self.y + self.h)
        glVertex2f(self.x, self.y + self.h)
        glEnd()

        # Text with shadow
        text_color = (1.0, 1.0, 1.0) if self.hover_anim > 0.2 else (0.85, 0.85, 0.85)
        text_w = text_renderer.get_text_width(self.text, size="medium")
        text_x = self.x + (self.w - text_w) / 2
        text_y = self.y + (self.h - 14) / 2
        text_renderer.draw_text_shadow(text_x, text_y, self.text, size="medium", color=text_color)

        glDisable(GL_BLEND)

    def _draw_rect(self, x, y, w, h):
        glBegin(GL_QUADS)
        glVertex2f(x, y)
        glVertex2f(x + w, y)
        glVertex2f(x + w, y + h)
        glVertex2f(x, y + h)
        glEnd()


TIPS = [
    "You can configure physics in Settings!",
    "Press F5 to toggle third-person view!",
    "Use / to open the console if cheats are on!",
    "Right-click food to eat it!",
    "Right-click a furnace to open smelting!",
    "Diamond ore spawns below Y=15!",
    "Press Alt+F2 for the debug overlay!",
    "IO triggers can run commands on events!",
    "Craft armor to reduce damage!",
    "Sprint drains hunger faster!",
    "Electronics have polarity - watch out!",
    "Press E to open your inventory!",
    "Right-click armor to equip it!",
    "Leaves can drop apples!",
    "You can configure world settings per-world!",
    "Hold Space to swim up in water!",
    "F3 shows coordinates if enabled!",
    "Press G to freeze the day/night cycle!",
    "Each world can have custom physics!",
    "Press R to respawn when dead!",
]


class MainMenu:
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.time = 0

        cx = screen_w // 2
        cy = screen_h // 2

        self.buttons = [
            Button(cx - 150, cy + 100, 300, 40, "SINGLEPLAYER", (0.2, 0.55, 0.2), (0.3, 0.75, 0.3)),
            Button(cx - 150, cy + 50, 300, 40, "HOST MULTIPLAYER", (0.15, 0.45, 0.55), (0.25, 0.6, 0.7)),
            Button(cx - 150, cy, 300, 40, "JOIN MULTIPLAYER", (0.2, 0.4, 0.6), (0.3, 0.55, 0.75)),
            Button(cx - 150, cy - 50, 300, 40, "STRUCTURE BUILDER", (0.25, 0.45, 0.55), (0.35, 0.6, 0.7)),
            Button(cx - 150, cy - 100, 300, 40, "SETTINGS", (0.25, 0.3, 0.5), (0.35, 0.4, 0.65)),
            Button(cx - 150, cy - 150, 300, 40, "CREDITS", (0.3, 0.3, 0.45), (0.4, 0.4, 0.6)),
            Button(cx - 150, cy - 200, 300, 40, "QUIT GAME", (0.5, 0.18, 0.18), (0.65, 0.25, 0.25)),
        ]

        # 3D world background
        self.cam_yaw = 0
        self.world = None
        self.world_loaded = False

        # Rotating tips
        self.tip_timer = 0
        self.tip_interval = 5.0
        self.tip_index = 0
        self.tip_alpha = 0.0

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
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            my = self.screen_h - my
            for btn in self.buttons:
                if btn.contains(mx, my):
                    sound_manager.play('click')
                    text = btn.text.lower().replace(" ", "_")
                    if text == "singleplayer":
                        return "play"
                    return text
        return None

    def update(self, dt, mouse_pos):
        self.time += dt
        self.cam_yaw += dt * 4

        # Tip rotation
        self.tip_timer += dt
        if self.tip_timer >= self.tip_interval:
            self.tip_timer = 0
            self.tip_index = (self.tip_index + 1) % len(TIPS)
        self.tip_alpha = min(1.0, self.tip_timer * 0.5) if self.tip_timer < 0.5 else \
                         max(0.0, 1.0 - (self.tip_timer - self.tip_interval + 0.5) * 2) if self.tip_timer > self.tip_interval - 0.5 else 1.0

        mx, my = mouse_pos
        my = self.screen_h - my
        for btn in self.buttons:
            btn.hovered = btn.contains(mx, my)

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

        # Lighting
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.4, 0.4, 0.5, 1.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.9, 0.85, 0.8, 1.0))
        glLightfv(GL_LIGHT0, GL_POSITION, (0.5, 1.0, 0.3, 0.0))

        # Draw world
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

        # Title panel
        panel_y = self.screen_h - 210
        glColor4f(0.03, 0.03, 0.08, 0.75)
        glBegin(GL_QUADS)
        glVertex2f(cx - 300, panel_y)
        glVertex2f(cx + 300, panel_y)
        glVertex2f(cx + 300, panel_y + 140)
        glVertex2f(cx - 300, panel_y + 140)
        glEnd()

        # Title
        title_y = self.screen_h - 160
        text_renderer.draw_text_centered_shadow(cx, title_y, "PYTHMC", size="title",
                                                 color=(0.3, 1.0, 0.3),
                                                 shadow=(0.0, 0.2, 0.0))

        # Version
        text_renderer.draw_text(cx - 290, panel_y + 8, "V2.0  -  PYTHON + OPENGL", size="medium",
                                color=(0.45, 0.45, 0.5))

        # Buttons
        for btn in self.buttons:
            btn.draw()

        # Rotating tips
        tip = TIPS[self.tip_index]
        tip_alpha = max(0.0, min(1.0, self.tip_alpha))
        text_renderer.draw_text_centered(cx, 55, tip, size="small",
                                        color=(0.6, 0.7, 0.8))

        # Bottom text
        text_renderer.draw_text(10, 10, "CLICK TO CAPTURE MOUSE  |  ESC TO QUIT", size="small",
                                color=(0.4, 0.4, 0.45))

        glDisable(GL_BLEND)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)


class PauseMenu:
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.time = 0

        cx = screen_w // 2
        cy = screen_h // 2

        self.buttons = [
            Button(cx - 150, cy + 60, 300, 50, "BACK TO GAME", (0.2, 0.5, 0.2), (0.3, 0.7, 0.3)),
            Button(cx - 150, cy - 10, 300, 50, "SETTINGS", (0.25, 0.3, 0.5), (0.35, 0.4, 0.65)),
            Button(cx - 150, cy - 80, 300, 50, "SAVE AND QUIT", (0.5, 0.18, 0.18), (0.65, 0.25, 0.25)),
        ]

    def handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            my = self.screen_h - my
            for btn in self.buttons:
                if btn.contains(mx, my):
                    sound_manager.play('click')
                    text = btn.text.lower().replace(" ", "_")
                    if text == "back_to_game":
                        return "resume"
                    elif text == "save_and_quit":
                        return "quit_to_menu"
                    return text
        elif event.type == KEYDOWN and event.key == K_ESCAPE:
            sound_manager.play('click')
            return "resume"
        return None

    def update(self, dt, mouse_pos):
        self.time += dt
        mx, my = mouse_pos
        my = self.screen_h - my
        for btn in self.buttons:
            btn.hovered = btn.contains(mx, my)

    def draw(self):
        glDisable(GL_LIGHTING)
        glDisable(GL_FOG)
        glDisable(GL_DEPTH_TEST)

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
        glColor4f(0, 0, 0, 0.55)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(self.screen_w, 0)
        glVertex2f(self.screen_w, self.screen_h)
        glVertex2f(0, self.screen_h)
        glEnd()

        cx = self.screen_w // 2
        cy = self.screen_h // 2

        # Panel
        pw, ph = 360, 270
        glColor4f(0.05, 0.05, 0.1, 0.92)
        glBegin(GL_QUADS)
        glVertex2f(cx - pw // 2, cy - ph // 2)
        glVertex2f(cx + pw // 2, cy - ph // 2)
        glVertex2f(cx + pw // 2, cy + ph // 2)
        glVertex2f(cx - pw // 2, cy + ph // 2)
        glEnd()

        # Border
        glColor4f(0.3, 0.3, 0.4, 0.5)
        glLineWidth(2)
        glBegin(GL_LINE_LOOP)
        glVertex2f(cx - pw // 2, cy - ph // 2)
        glVertex2f(cx + pw // 2, cy - ph // 2)
        glVertex2f(cx + pw // 2, cy + ph // 2)
        glVertex2f(cx - pw // 2, cy + ph // 2)
        glEnd()

        # Title
        text_renderer.draw_text_centered_shadow(cx, cy + ph // 2 - 50, "GAME PAUSED", size="medium",
                                                color=(1.0, 1.0, 1.0),
                                                shadow=(0.2, 0.2, 0.2))

        # Separator
        glColor4f(0.3, 0.3, 0.4, 0.4)
        glLineWidth(1)
        glBegin(GL_LINES)
        glVertex2f(cx - pw // 2 + 20, cy + ph // 2 - 60)
        glVertex2f(cx + pw // 2 - 20, cy + ph // 2 - 60)
        glEnd()

        # Buttons
        for btn in self.buttons:
            btn.draw()

        glDisable(GL_BLEND)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_FOG)


class SettingsMenu:
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.sensitivity = 0.15
        self.render_distance = RENDER_DISTANCE
        self.time = 0

        cx = screen_w // 2
        cy = screen_h // 2

        self.buttons = [
            Button(cx - 170, cy + 60, 340, 50, f"SENSITIVITY: {self.sensitivity:.2f}", (0.25, 0.3, 0.5), (0.35, 0.4, 0.65)),
            Button(cx - 170, cy - 10, 340, 50, f"RENDER DIST: {self.render_distance}", (0.25, 0.3, 0.5), (0.35, 0.4, 0.65)),
            Button(cx - 170, cy - 80, 340, 50, "DONE", (0.2, 0.5, 0.2), (0.3, 0.7, 0.3)),
        ]

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
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            my = self.screen_h - my
            for i, btn in enumerate(self.buttons):
                if btn.contains(mx, my):
                    if i == 0:
                        self.sensitivity += 0.05
                        if self.sensitivity > 0.4:
                            self.sensitivity = 0.05
                        self.buttons[0].text = f"SENSITIVITY: {self.sensitivity:.2f}"
                    elif i == 1:
                        self.render_distance = (self.render_distance % 6) + 2
                        self.buttons[1].text = f"RENDER DIST: {self.render_distance}"
                    elif i == 2:
                        return "back"
        elif event.type == KEYDOWN and event.key == K_ESCAPE:
            return "back"
        return None

    def update(self, dt, mouse_pos):
        self.time += dt
        self.cam_yaw += dt * 4
        mx, my = mouse_pos
        my = self.screen_h - my
        for btn in self.buttons:
            btn.hovered = btn.contains(mx, my)

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
        cy = self.screen_h // 2

        # Panel
        pw, ph = 420, 270
        glColor4f(0.05, 0.05, 0.1, 0.85)
        glBegin(GL_QUADS)
        glVertex2f(cx - pw // 2, cy - ph // 2)
        glVertex2f(cx + pw // 2, cy - ph // 2)
        glVertex2f(cx + pw // 2, cy + ph // 2)
        glVertex2f(cx - pw // 2, cy + ph // 2)
        glEnd()

        # Border
        glColor4f(0.3, 0.3, 0.4, 0.5)
        glLineWidth(2)
        glBegin(GL_LINE_LOOP)
        glVertex2f(cx - pw // 2, cy - ph // 2)
        glVertex2f(cx + pw // 2, cy - ph // 2)
        glVertex2f(cx + pw // 2, cy + ph // 2)
        glVertex2f(cx - pw // 2, cy + ph // 2)
        glEnd()

        # Title
        text_renderer.draw_text_centered_shadow(cx, cy + ph // 2 - 50, "SETTINGS", size="medium",
                                                color=(1.0, 1.0, 1.0),
                                                shadow=(0.2, 0.2, 0.2))

        # Separator
        glColor4f(0.3, 0.3, 0.4, 0.4)
        glLineWidth(1)
        glBegin(GL_LINES)
        glVertex2f(cx - pw // 2 + 20, cy + ph // 2 - 60)
        glVertex2f(cx + pw // 2 - 20, cy + ph // 2 - 60)
        glEnd()

        # Buttons
        for btn in self.buttons:
            btn.draw()

        glDisable(GL_BLEND)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_FOG)

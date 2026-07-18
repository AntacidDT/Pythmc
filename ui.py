"""Pythmc - Shared UI Components (V2.7)
Unified stone-textured buttons, panels, and tab system."""

import pygame
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import random

from text_renderer import text_renderer

# ─── Procedural Stone Texture ────────────────────────────────────────────────

_stone_tex_id = None
_tex_initialized = False


def _gen_stone_texture(base_r=120, base_g=120, base_b=120, size=16):
    """Generate a procedural Minecraft-style stone texture."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    rng = random.Random(0)
    for y in range(size):
        for x in range(size):
            noise = rng.randint(-20, 20)
            r = max(0, min(255, base_r + noise))
            g = max(0, min(255, base_g + noise))
            b = max(0, min(255, base_b + noise))
            surf.set_at((x, y), (r, g, b, 255))
    return surf


def _gen_dirt_texture(size=16):
    """Generate a procedural dirt texture variant."""
    return _gen_stone_texture(base_r=134, base_g=96, base_b=67, size=size)


def _init_stone_tex():
    """Upload the stone texture to OpenGL."""
    global _stone_tex_id, _tex_initialized
    if _tex_initialized:
        return
    _tex_initialized = True

    surf = _gen_stone_texture()
    data = pygame.image.tostring(surf, "RGBA", True)

    _stone_tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, _stone_tex_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 16, 16, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)


# ─── Utility ─────────────────────────────────────────────────────────────────

def _draw_rect(x, y, w, h):
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + w, y)
    glVertex2f(x + w, y + h)
    glVertex2f(x, y + h)
    glEnd()


def draw_panel(x, y, w, h, color=(0.05, 0.05, 0.1), alpha=0.92, border=True):
    """Draw a dark panel with optional border."""
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    glColor4f(color[0], color[1], color[2], alpha)
    _draw_rect(x, y, w, h)

    if border:
        glColor4f(0.3, 0.3, 0.4, 0.5)
        glLineWidth(2)
        glBegin(GL_LINE_LOOP)
        glVertex2f(x, y)
        glVertex2f(x + w, y)
        glVertex2f(x + w, y + h)
        glVertex2f(x, y + h)
        glEnd()

    glDisable(GL_BLEND)


def draw_separator(x1, y, x2):
    """Draw a horizontal separator line."""
    glColor4f(0.3, 0.3, 0.4, 0.4)
    glLineWidth(1)
    glBegin(GL_LINES)
    glVertex2f(x1, y)
    glVertex2f(x2, y)
    glEnd()


def draw_title(screen_cx, y, text, color=(1.0, 1.0, 1.0), shadow=(0.2, 0.2, 0.2)):
    """Draw a centered title with shadow."""
    text_renderer.draw_text_centered_shadow(screen_cx, y, text, size="medium",
                                            color=color, shadow=shadow)


# ─── Button ──────────────────────────────────────────────────────────────────

class Button:
    """Stone-textured Minecraft-style button."""
    def __init__(self, x, y, w, h, text, color=(0.25, 0.25, 0.35), hover_color=(0.35, 0.35, 0.5)):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.hovered = False
        self.hover_anim = 0.0

    def contains(self, mx, my):
        return self.x <= mx <= self.x + self.w and self.y <= my <= self.y + self.h

    def draw(self):
        _init_stone_tex()

        target = 1.0 if self.hovered else 0.0
        self.hover_anim += (target - self.hover_anim) * 0.15

        r = self.color[0] + (self.hover_color[0] - self.color[0]) * self.hover_anim
        g = self.color[1] + (self.hover_color[1] - self.color[1]) * self.hover_anim
        b = self.color[2] + (self.hover_color[2] - self.color[2]) * self.hover_anim

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Shadow
        glColor4f(0, 0, 0, 0.4)
        _draw_rect(self.x + 3, self.y - 3, self.w, self.h)

        # Dark bottom edge
        glColor3f(r * 0.35, g * 0.35, b * 0.35)
        _draw_rect(self.x, self.y - 2, self.w, self.h)

        # Stone texture body
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, _stone_tex_id)
        # Tint stone with button color (multiply mode)
        glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
        glColor4f(r * 1.6, g * 1.6, b * 1.6, 1.0)

        # Map texture coords across button
        tw = self.w / 16.0
        th = self.h / 16.0
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0)
        glVertex2f(self.x, self.y)
        glTexCoord2f(tw, 0)
        glVertex2f(self.x + self.w, self.y)
        glTexCoord2f(tw, th)
        glVertex2f(self.x + self.w, self.y + self.h)
        glTexCoord2f(0, th)
        glVertex2f(self.x, self.y + self.h)
        glEnd()

        glDisable(GL_TEXTURE_2D)

        # Top highlight
        glColor4f(1, 1, 1, 0.15 + self.hover_anim * 0.15)
        _draw_rect(self.x + 2, self.y + self.h - 6, self.w - 4, 4)

        # Border
        brightness = 0.18 + self.hover_anim * 0.3
        if self.hover_anim > 0.3:
            glColor4f(0.9, 1.0, 0.9, brightness)
        else:
            glColor4f(1, 1, 1, brightness)
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


# ─── Tab Bar (Vertical) ───────────────────────────────────────────────────────

class TabBar:
    """Vertical tab bar widget — tabs stacked in the middle of the screen."""
    def __init__(self, cx, cy, tab_w, tab_h, names, gap=4):
        self.cx = cx
        self.cy = cy
        self.tab_w = tab_w
        self.tab_h = tab_h
        self.names = names
        self.gap = gap
        self.active = 0
        self.buttons = []
        total_h = len(names) * tab_h + (len(names) - 1) * gap
        start_y = cy + total_h // 2 - tab_h
        for i, name in enumerate(names):
            by = start_y - i * (tab_h + gap)
            self.buttons.append(Button(cx - tab_w // 2, by, tab_w, tab_h, name.upper(),
                                       (0.18, 0.18, 0.3), (0.28, 0.28, 0.45)))

    @property
    def active_name(self):
        return self.names[self.active]

    def handle_click(self, mx, my):
        for i, btn in enumerate(self.buttons):
            if btn.contains(mx, my):
                self.active = i
                return i
        return None

    def update(self, mx, my):
        for btn in self.buttons:
            btn.hovered = btn.contains(mx, my)

    def draw(self):
        _init_stone_tex()

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        for i, btn in enumerate(self.buttons):
            if i == self.active:
                glEnable(GL_TEXTURE_2D)
                glBindTexture(GL_TEXTURE_2D, _stone_tex_id)
                glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
                glColor4f(0.5, 0.6, 0.5, 0.95)
                tw = btn.w / 16.0
                th = btn.h / 16.0
                glBegin(GL_QUADS)
                glTexCoord2f(0, 0)
                glVertex2f(btn.x, btn.y)
                glTexCoord2f(tw, 0)
                glVertex2f(btn.x + btn.w, btn.y)
                glTexCoord2f(tw, th)
                glVertex2f(btn.x + btn.w, btn.y + btn.h)
                glTexCoord2f(0, th)
                glVertex2f(btn.x, btn.y + btn.h)
                glEnd()
                glDisable(GL_TEXTURE_2D)

                # Green accent bar on left edge
                glColor4f(0.3, 0.8, 0.3, 0.9)
                glLineWidth(3)
                glBegin(GL_LINES)
                glVertex2f(btn.x, btn.y)
                glVertex2f(btn.x, btn.y + btn.h)
                glEnd()

                text_color = (1.0, 1.0, 1.0)
            else:
                btn.draw()
                text_color = None

            if text_color:
                text_w = text_renderer.get_text_width(btn.text, size="large")
                text_x = btn.x + (btn.w - text_w) / 2
                text_y = btn.y + (btn.h - 18) / 2
                text_renderer.draw_text_shadow(text_x, text_y, btn.text, size="large", color=text_color)

        glDisable(GL_BLEND)

"""Pythmc - Text Renderer - String-based approach"""

import pygame
from OpenGL.GL import *


class TextRenderer:
    def __init__(self):
        self.cache = {}  # (text, size, color) -> (texture, width, height)
        self.ready = False
        self.fonts = {}

    def init(self):
        if self.ready:
            return
        pygame.font.init()
        self.fonts = {
            "small": pygame.font.SysFont("Arial", 16, bold=True),
            "medium": pygame.font.SysFont("Arial", 22, bold=True),
            "large": pygame.font.SysFont("Arial", 36, bold=True),
            "title": pygame.font.SysFont("Arial", 52, bold=True),
        }
        self.ready = True

    def _get_texture(self, text, size="medium", color=(255, 255, 255)):
        """Get or create a texture for this text string."""
        cache_key = (text, size, color)
        if cache_key in self.cache:
            return self.cache[cache_key]

        font = self.fonts.get(size, self.fonts["medium"])
        surface = font.render(text, True, color)
        w, h = surface.get_size()

        # Convert to string and create texture
        raw = pygame.image.tostring(surface, "RGBA", True)
        tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE, raw)

        self.cache[cache_key] = (tex, w, h)
        return tex, w, h

    def draw_text(self, x, y, text, size="medium", color=(1.0, 1.0, 1.0)):
        """Draw text at position."""
        if not self.ready or not text:
            return 0

        # Convert color from 0-1 to 0-255
        c255 = (int(color[0]*255), int(color[1]*255), int(color[2]*255))
        tex, w, h = self._get_texture(text, size, c255)

        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glBindTexture(GL_TEXTURE_2D, tex)
        glColor4f(1.0, 1.0, 1.0, 1.0)

        glBegin(GL_QUADS)
        glTexCoord2f(0, 1); glVertex2f(x, y + h)
        glTexCoord2f(1, 1); glVertex2f(x + w, y + h)
        glTexCoord2f(1, 0); glVertex2f(x + w, y)
        glTexCoord2f(0, 0); glVertex2f(x, y)
        glEnd()

        glDisable(GL_TEXTURE_2D)
        glDisable(GL_BLEND)
        return w

    def draw_text_centered(self, x, y, text, size="medium", color=(1.0, 1.0, 1.0)):
        """Draw text centered at position."""
        c255 = (int(color[0]*255), int(color[1]*255), int(color[2]*255))
        _, w, h = self._get_texture(text, size, c255)
        self.draw_text(x - w // 2, y, text, size, color)

    def draw_text_shadow(self, x, y, text, size="medium", color=(1.0, 1.0, 1.0), shadow=(0.0, 0.0, 0.0)):
        """Draw text with drop shadow."""
        self.draw_text(x + 2, y - 2, text, size, shadow)
        self.draw_text(x, y, text, size, color)

    def draw_text_centered_shadow(self, x, y, text, size="medium", color=(1.0, 1.0, 1.0), shadow=(0.0, 0.0, 0.0)):
        """Draw centered text with drop shadow."""
        c255 = (int(color[0]*255), int(color[1]*255), int(color[2]*255))
        _, w, _ = self._get_texture(text, size, c255)
        self.draw_text_shadow(x - w // 2, y, text, size, color, shadow)

    def get_text_width(self, text, size="medium"):
        """Get text width."""
        c255 = (255, 255, 255)
        _, w, _ = self._get_texture(text, size, c255)
        return w

    def get_text_height(self, size="medium"):
        """Get text height."""
        return self.fonts[size].get_linesize()


text_renderer = TextRenderer()

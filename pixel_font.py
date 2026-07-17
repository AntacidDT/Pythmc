"""Pythmc - Pixel Font Renderer - Retro blocky bitmap font"""

import pygame
from OpenGL.GL import *


# Each character is a list of rows, each row is a string of 1s and 0s
# 5 wide x 7 tall for letters, 5x7 for numbers, 3x7 for punctuation
GLYPH_DATA = {
    'A': [
        "01110",
        "10001",
        "10001",
        "11111",
        "10001",
        "10001",
        "10001",
    ],
    'B': [
        "11110",
        "10001",
        "10001",
        "11110",
        "10001",
        "10001",
        "11110",
    ],
    'C': [
        "01110",
        "10001",
        "10000",
        "10000",
        "10000",
        "10001",
        "01110",
    ],
    'D': [
        "11100",
        "10010",
        "10001",
        "10001",
        "10001",
        "10010",
        "11100",
    ],
    'E': [
        "11111",
        "10000",
        "10000",
        "11110",
        "10000",
        "10000",
        "11111",
    ],
    'F': [
        "11111",
        "10000",
        "10000",
        "11110",
        "10000",
        "10000",
        "10000",
    ],
    'G': [
        "01110",
        "10001",
        "10000",
        "10111",
        "10001",
        "10001",
        "01110",
    ],
    'H': [
        "10001",
        "10001",
        "10001",
        "11111",
        "10001",
        "10001",
        "10001",
    ],
    'I': [
        "01110",
        "00100",
        "00100",
        "00100",
        "00100",
        "00100",
        "01110",
    ],
    'J': [
        "00111",
        "00010",
        "00010",
        "00010",
        "00010",
        "10010",
        "01100",
    ],
    'K': [
        "10001",
        "10010",
        "10100",
        "11000",
        "10100",
        "10010",
        "10001",
    ],
    'L': [
        "10000",
        "10000",
        "10000",
        "10000",
        "10000",
        "10000",
        "11111",
    ],
    'M': [
        "10001",
        "11011",
        "10101",
        "10101",
        "10001",
        "10001",
        "10001",
    ],
    'N': [
        "10001",
        "10001",
        "11001",
        "10101",
        "10011",
        "10001",
        "10001",
    ],
    'O': [
        "01110",
        "10001",
        "10001",
        "10001",
        "10001",
        "10001",
        "01110",
    ],
    'P': [
        "11110",
        "10001",
        "10001",
        "11110",
        "10000",
        "10000",
        "10000",
    ],
    'Q': [
        "01110",
        "10001",
        "10001",
        "10001",
        "10101",
        "10010",
        "01101",
    ],
    'R': [
        "11110",
        "10001",
        "10001",
        "11110",
        "10100",
        "10010",
        "10001",
    ],
    'S': [
        "01110",
        "10001",
        "10000",
        "01110",
        "00001",
        "10001",
        "01110",
    ],
    'T': [
        "11111",
        "00100",
        "00100",
        "00100",
        "00100",
        "00100",
        "00100",
    ],
    'U': [
        "10001",
        "10001",
        "10001",
        "10001",
        "10001",
        "10001",
        "01110",
    ],
    'V': [
        "10001",
        "10001",
        "10001",
        "10001",
        "01010",
        "01010",
        "00100",
    ],
    'W': [
        "10001",
        "10001",
        "10001",
        "10101",
        "10101",
        "11011",
        "10001",
    ],
    'X': [
        "10001",
        "10001",
        "01010",
        "00100",
        "01010",
        "10001",
        "10001",
    ],
    'Y': [
        "10001",
        "10001",
        "01010",
        "00100",
        "00100",
        "00100",
        "00100",
    ],
    'Z': [
        "11111",
        "00001",
        "00010",
        "00100",
        "01000",
        "10000",
        "11111",
    ],
    '0': [
        "01110",
        "10001",
        "10011",
        "10101",
        "11001",
        "10001",
        "01110",
    ],
    '1': [
        "00100",
        "01100",
        "00100",
        "00100",
        "00100",
        "00100",
        "01110",
    ],
    '2': [
        "01110",
        "10001",
        "00001",
        "00010",
        "00100",
        "01000",
        "11111",
    ],
    '3': [
        "11111",
        "00010",
        "00100",
        "00010",
        "00001",
        "10001",
        "01110",
    ],
    '4': [
        "00010",
        "00110",
        "01010",
        "10010",
        "11111",
        "00010",
        "00010",
    ],
    '5': [
        "11111",
        "10000",
        "11110",
        "00001",
        "00001",
        "10001",
        "01110",
    ],
    '6': [
        "01110",
        "10000",
        "10000",
        "11110",
        "10001",
        "10001",
        "01110",
    ],
    '7': [
        "11111",
        "00001",
        "00010",
        "00100",
        "01000",
        "01000",
        "01000",
    ],
    '8': [
        "01110",
        "10001",
        "10001",
        "01110",
        "10001",
        "10001",
        "01110",
    ],
    '9': [
        "01110",
        "10001",
        "10001",
        "01111",
        "00001",
        "00001",
        "01110",
    ],
    ' ': [
        "00000",
        "00000",
        "00000",
        "00000",
        "00000",
        "00000",
        "00000",
    ],
    '.': [
        "00000",
        "00000",
        "00000",
        "00000",
        "00000",
        "00000",
        "00100",
    ],
    ',': [
        "00000",
        "00000",
        "00000",
        "00000",
        "00100",
        "00100",
        "01000",
    ],
    ':': [
        "00000",
        "00100",
        "00100",
        "00000",
        "00100",
        "00100",
        "00000",
    ],
    ';': [
        "00000",
        "00100",
        "00100",
        "00000",
        "00100",
        "00100",
        "01000",
    ],
    '!': [
        "00100",
        "00100",
        "00100",
        "00100",
        "00100",
        "00000",
        "00100",
    ],
    '?': [
        "01110",
        "10001",
        "00001",
        "00010",
        "00100",
        "00000",
        "00100",
    ],
    '-': [
        "00000",
        "00000",
        "00000",
        "11111",
        "00000",
        "00000",
        "00000",
    ],
    '+': [
        "00000",
        "00100",
        "00100",
        "11111",
        "00100",
        "00100",
        "00000",
    ],
    '=': [
        "00000",
        "00000",
        "11111",
        "00000",
        "11111",
        "00000",
        "00000",
    ],
    '/': [
        "00001",
        "00010",
        "00010",
        "00100",
        "01000",
        "01000",
        "10000",
    ],
    '(': [
        "00010",
        "00100",
        "01000",
        "01000",
        "01000",
        "00100",
        "00010",
    ],
    ')': [
        "01000",
        "00100",
        "00010",
        "00010",
        "00010",
        "00100",
        "01000",
    ],
    '[': [
        "01110",
        "01000",
        "01000",
        "01000",
        "01000",
        "01000",
        "01110",
    ],
    ']': [
        "01110",
        "00010",
        "00010",
        "00010",
        "00010",
        "00010",
        "01110",
    ],
    '_': [
        "00000",
        "00000",
        "00000",
        "00000",
        "00000",
        "00000",
        "11111",
    ],
    '#': [
        "01010",
        "01010",
        "11111",
        "01010",
        "11111",
        "01010",
        "01010",
    ],
    '%': [
        "10001",
        "00010",
        "00010",
        "00100",
        "01000",
        "01000",
        "10001",
    ],
    '*': [
        "00000",
        "10101",
        "01110",
        "11111",
        "01110",
        "10101",
        "00000",
    ],
    "'": [
        "00100",
        "00100",
        "01000",
        "00000",
        "00000",
        "00000",
        "00000",
    ],
    '"': [
        "01010",
        "01010",
        "10100",
        "00000",
        "00000",
        "00000",
        "00000",
    ],
    '@': [
        "01110",
        "10001",
        "10111",
        "10101",
        "10110",
        "10000",
        "01110",
    ],
    '$': [
        "00100",
        "01111",
        "10100",
        "01110",
        "00101",
        "11110",
        "00100",
    ],
    '^': [
        "00100",
        "01010",
        "10001",
        "00000",
        "00000",
        "00000",
        "00000",
    ],
    '<': [
        "00010",
        "00100",
        "01000",
        "10000",
        "01000",
        "00100",
        "00010",
    ],
    '>': [
        "01000",
        "00100",
        "00010",
        "00001",
        "00010",
        "00100",
        "01000",
    ],
    '|': [
        "00100",
        "00100",
        "00100",
        "00100",
        "00100",
        "00100",
        "00100",
    ],
    '~': [
        "00000",
        "00000",
        "01000",
        "10101",
        "00010",
        "00000",
        "00000",
    ],
}


class PixelFont:
    """Retro blocky bitmap font renderer."""

    def __init__(self):
        self.cache = {}
        self.ready = False
        self.pixel_size = 2
        self.char_width = 5
        self.char_height = 7
        self.char_spacing = 1

    def init(self):
        if self.ready:
            return
        pygame.font.init()
        self.ready = True

    def _render_glyph_surface(self, char, color):
        """Render a single character to a pygame surface."""
        data = GLYPH_DATA.get(char.upper(), GLYPH_DATA[' '])
        ps = self.pixel_size
        w = self.char_width * ps
        h = self.char_height * ps
        surface = pygame.Surface((w, h), pygame.SRCALPHA)
        for row_i, row in enumerate(data):
            for col_i, pixel in enumerate(row):
                if pixel == '1':
                    x = col_i * ps
                    y = (self.char_height - 1 - row_i) * ps
                    pygame.draw.rect(surface, color, (x, y, ps, ps))
        return surface

    def _get_texture(self, text, size="medium", color=(255, 255, 255)):
        """Get or create a texture for text."""
        cache_key = (text, size, color)
        if cache_key in self.cache:
            return self.cache[cache_key]

        scale = {"small": 1, "medium": 2, "large": 3, "title": 4}.get(size, 2)
        ps = scale
        spacing = max(1, scale - 1)

        total_w = 0
        for ch in text:
            data = GLYPH_DATA.get(ch.upper(), GLYPH_DATA[' '])
            total_w += len(data[0]) * ps + spacing
        total_w -= spacing
        total_h = self.char_height * ps

        if total_w <= 0:
            total_w = 1

        surface = pygame.Surface((total_w, total_h), pygame.SRCALPHA)
        x_off = 0
        for ch in text:
            data = GLYPH_DATA.get(ch.upper(), GLYPH_DATA[' '])
            glyph_w = len(data[0]) * ps
            glyph_h = len(data) * ps
            for row_i, row in enumerate(data):
                for col_i, pixel in enumerate(row):
                    if pixel == '1':
                        rx = x_off + col_i * ps
                        ry = row_i * ps
                        pygame.draw.rect(surface, color, (rx, ry, ps, ps))
            x_off += glyph_w + spacing

        w, h = surface.get_size()
        raw = pygame.image.tostring(surface, "RGBA", True)
        tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE, raw)

        self.cache[cache_key] = (tex, w, h)
        return tex, w, h

    def draw_text(self, x, y, text, size="medium", color=(1.0, 1.0, 1.0)):
        """Draw text at position."""
        if not self.ready or not text:
            return 0
        c255 = (int(color[0] * 255), int(color[1] * 255), int(color[2] * 255))
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
        c255 = (int(color[0] * 255), int(color[1] * 255), int(color[2] * 255))
        _, w, h = self._get_texture(text, size, c255)
        self.draw_text(x - w // 2, y, text, size, color)

    def draw_text_shadow(self, x, y, text, size="medium", color=(1.0, 1.0, 1.0), shadow=(0.0, 0.0, 0.0)):
        """Draw text with drop shadow."""
        self.draw_text(x + 2, y - 2, text, size, shadow)
        self.draw_text(x, y, text, size, color)

    def draw_text_centered_shadow(self, x, y, text, size="medium", color=(1.0, 1.0, 1.0), shadow=(0.0, 0.0, 0.0)):
        """Draw centered text with drop shadow."""
        c255 = (int(color[0] * 255), int(color[1] * 255), int(color[2] * 255))
        _, w, _ = self._get_texture(text, size, c255)
        self.draw_text_shadow(x - w // 2, y, text, size, color, shadow)

    def get_text_width(self, text, size="medium"):
        """Get text width."""
        c255 = (255, 255, 255)
        _, w, _ = self._get_texture(text, size, c255)
        return w

    def get_text_height(self, size="medium"):
        """Get text height."""
        scale = {"small": 1, "medium": 2, "large": 3, "title": 4}.get(size, 2)
        return self.char_height * scale


pixel_font = PixelFont()

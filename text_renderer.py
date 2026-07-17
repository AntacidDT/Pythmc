"""Pythmc - Text Renderer - Uses pixel font for retro blocky look"""

from pixel_font import pixel_font


class TextRenderer:
    """Wrapper that delegates to pixel_font for all rendering."""

    def __init__(self):
        self.ready = False

    def init(self):
        if self.ready:
            return
        pixel_font.init()
        self.ready = True

    def draw_text(self, x, y, text, size="medium", color=(1.0, 1.0, 1.0)):
        return pixel_font.draw_text(x, y, text, size, color)

    def draw_text_centered(self, x, y, text, size="medium", color=(1.0, 1.0, 1.0)):
        pixel_font.draw_text_centered(x, y, text, size, color)

    def draw_text_shadow(self, x, y, text, size="medium", color=(1.0, 1.0, 1.0), shadow=(0.0, 0.0, 0.0)):
        pixel_font.draw_text_shadow(x, y, text, size, color, shadow)

    def draw_text_centered_shadow(self, x, y, text, size="medium", color=(1.0, 1.0, 1.0), shadow=(0.0, 0.0, 0.0)):
        pixel_font.draw_text_centered_shadow(x, y, text, size, color, shadow)

    def get_text_width(self, text, size="medium"):
        return pixel_font.get_text_width(text, size)

    def get_text_height(self, size="medium"):
        return pixel_font.get_text_height(size)


text_renderer = TextRenderer()

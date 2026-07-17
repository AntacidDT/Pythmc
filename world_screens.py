"""Pythmc - World Selection and Creation Screens"""

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import time
from constants import *
from text_renderer import text_renderer
from world_manager import list_worlds, create_world, delete_world, world_exists


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
        glColor4f(0, 0, 0, 0.3)
        self._draw_rect(self.x + 2, self.y - 2, self.w, self.h)

        # Body
        glColor3f(r * 0.5, g * 0.5, b * 0.5)
        self._draw_rect(self.x, self.y - 1, self.w, self.h)
        glColor3f(r, g, b)
        self._draw_rect(self.x, self.y, self.w, self.h)

        # Highlight
        glColor4f(1, 1, 1, 0.08 + self.hover_anim * 0.1)
        self._draw_rect(self.x + 2, self.y + self.h - 6, self.w - 4, 4)

        # Border
        glColor4f(1, 1, 1, 0.12 + self.hover_anim * 0.2)
        glLineWidth(1)
        glBegin(GL_LINE_LOOP)
        glVertex2f(self.x, self.y)
        glVertex2f(self.x + self.w, self.y)
        glVertex2f(self.x + self.w, self.y + self.h)
        glVertex2f(self.x, self.y + self.h)
        glEnd()

        # Text
        tc = (1.0, 1.0, 1.0) if self.hover_anim > 0.2 else (0.85, 0.85, 0.85)
        text_renderer.draw_text_centered(self.x + self.w // 2, self.y + self.h // 2 - 8, 
                                         self.text, "medium", tc)
        glDisable(GL_BLEND)

    def _draw_rect(self, x, y, w, h):
        glBegin(GL_QUADS)
        glVertex2f(x, y)
        glVertex2f(x + w, y)
        glVertex2f(x + w, y + h)
        glVertex2f(x, y + h)
        glEnd()


class WorldSelectScreen:
    """Screen to select, create, or delete worlds."""
    
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.worlds = []
        self.selected_idx = -1
        self.scroll_offset = 0
        self.time = 0
        self.result = None  # None, "back", or world dict
        self.confirm_delete = None  # World name to confirm deletion
        
        # Buttons
        self._update_buttons()

    def _update_buttons(self):
        cx = self.screen_w // 2
        self.play_btn = Button(cx - 160, 80, 150, 45, "Play World", (0.2, 0.5, 0.2), (0.3, 0.7, 0.3))
        self.new_btn = Button(cx + 10, 80, 150, 45, "Create New", (0.25, 0.35, 0.55), (0.35, 0.5, 0.7))
        self.delete_btn = Button(cx - 160, 25, 150, 45, "Delete", (0.5, 0.2, 0.2), (0.7, 0.3, 0.3))
        self.back_btn = Button(cx + 10, 25, 150, 45, "Back", (0.35, 0.35, 0.35), (0.5, 0.5, 0.5))
        self.confirm_yes = Button(cx - 80, self.screen_h // 2, 70, 40, "Yes", (0.5, 0.2, 0.2), (0.7, 0.3, 0.3))
        self.confirm_no = Button(cx + 10, self.screen_h // 2, 70, 40, "No", (0.25, 0.5, 0.25), (0.35, 0.7, 0.35))

    def refresh(self):
        self.worlds = list_worlds()
        if self.selected_idx >= len(self.worlds):
            self.selected_idx = len(self.worlds) - 1

    def handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            my = self.screen_h - my

            # Confirm delete dialog
            if self.confirm_delete:
                if self.confirm_yes.contains(mx, my):
                    delete_world(self.confirm_delete)
                    self.confirm_delete = None
                    self.refresh()
                    return None
                if self.confirm_no.contains(mx, my):
                    self.confirm_delete = None
                    return None
                return None

            # Main buttons
            if self.back_btn.contains(mx, my):
                return "back"
            if self.new_btn.contains(mx, my):
                return "create_new"
            if self.play_btn.contains(mx, my) and self.selected_idx >= 0:
                return {"action": "play", "world": self.worlds[self.selected_idx]}
            if self.delete_btn.contains(mx, my) and self.selected_idx >= 0:
                self.confirm_delete = self.worlds[self.selected_idx]["name"]
                return None

            # World list clicks
            list_y_start = self.screen_h - 160
            item_h = 55
            for i in range(min(len(self.worlds), 8)):
                idx = i + self.scroll_offset
                if idx >= len(self.worlds):
                    break
                item_y = list_y_start - i * item_h
                if item_y <= my <= item_y + item_h - 5:
                    # Check if clicking in the list area
                    list_x = self.screen_w // 2 - 250
                    if list_x <= mx <= list_x + 500:
                        self.selected_idx = idx
                        return None

        elif event.type == MOUSEWHEEL:
            self.scroll_offset = max(0, min(len(self.worlds) - 8, 
                                           self.scroll_offset - event.y))

        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                if self.confirm_delete:
                    self.confirm_delete = None
                else:
                    return "back"

        return None

    def update(self, dt, mouse_pos):
        self.time += dt
        mx, my = mouse_pos
        my = self.screen_h - my

        if not self.confirm_delete:
            self.play_btn.hovered = self.play_btn.contains(mx, my) and self.selected_idx >= 0
            self.new_btn.hovered = self.new_btn.contains(mx, my)
            self.delete_btn.hovered = self.delete_btn.contains(mx, my) and self.selected_idx >= 0
            self.back_btn.hovered = self.back_btn.contains(mx, my)
        else:
            self.confirm_yes.hovered = self.confirm_yes.contains(mx, my)
            self.confirm_no.hovered = self.confirm_no.contains(mx, my)

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

        # Background
        glBegin(GL_QUADS)
        glColor3f(0.06, 0.06, 0.1)
        glVertex2f(0, 0)
        glVertex2f(self.screen_w, 0)
        glColor3f(0.1, 0.12, 0.18)
        glVertex2f(self.screen_w, self.screen_h)
        glVertex2f(0, self.screen_h)
        glEnd()

        cx = self.screen_w // 2

        # Title
        text_renderer.draw_text_centered_shadow(cx, self.screen_h - 60, "SELECT WORLD", 
                                                "title", (1.0, 1.0, 1.0), (0.2, 0.2, 0.2))

        # World list
        list_x = cx - 250
        list_y_start = self.screen_h - 140
        item_h = 55

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        if not self.worlds:
            text_renderer.draw_text_centered(cx, list_y_start - 80, "No worlds yet. Create one!", 
                                            "medium", (0.5, 0.5, 0.5))
        else:
            for i in range(min(len(self.worlds), 8)):
                idx = i + self.scroll_offset
                if idx >= len(self.worlds):
                    break
                world = self.worlds[idx]
                item_y = list_y_start - i * item_h

                # Selection highlight
                if idx == self.selected_idx:
                    glColor4f(0.2, 0.4, 0.6, 0.5)
                    self._draw_rect(list_x, item_y, 500, item_h - 5)
                    glColor4f(0.3, 0.5, 0.7, 0.8)
                    glLineWidth(2)
                    glBegin(GL_LINE_LOOP)
                    glVertex2f(list_x, item_y)
                    glVertex2f(list_x + 500, item_y)
                    glVertex2f(list_x + 500, item_y + item_h - 5)
                    glVertex2f(list_x, item_y + item_h - 5)
                    glEnd()
                else:
                    glColor4f(0.12, 0.12, 0.16, 0.7)
                    self._draw_rect(list_x, item_y, 500, item_h - 5)

                # World info
                mode_color = (0.3, 0.8, 0.3) if world["gamemode"] == "survival" else (0.5, 0.5, 0.8)
                text_renderer.draw_text_shadow(list_x + 15, item_y + item_h - 25, 
                                              world["name"], "medium", (1.0, 1.0, 1.0), (0.1, 0.1, 0.1))
                text_renderer.draw_text(list_x + 15, item_y + 8, 
                                       f"{world['gamemode'].capitalize()} | Seed: {world['seed']}", 
                                       "small", (0.6, 0.6, 0.6))

                # Play time
                pt = world.get("play_time", 0)
                if pt > 0:
                    hours = int(pt // 3600)
                    mins = int((pt % 3600) // 60)
                    text_renderer.draw_text(list_x + 380, item_y + item_h - 25, 
                                           f"{hours}h {mins}m", "small", (0.5, 0.5, 0.5))

        glDisable(GL_BLEND)

        # Buttons
        self.play_btn.draw()
        self.new_btn.draw()
        self.delete_btn.draw()
        self.back_btn.draw()

        # Confirm delete dialog
        if self.confirm_delete:
            self._draw_confirm_dialog()

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_FOG)

    def _draw_confirm_dialog(self):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Overlay
        glColor4f(0, 0, 0, 0.5)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(self.screen_w, 0)
        glVertex2f(self.screen_w, self.screen_h)
        glVertex2f(0, self.screen_h)
        glEnd()

        cx = self.screen_w // 2
        cy = self.screen_h // 2

        # Dialog box
        glColor4f(0.08, 0.08, 0.12, 0.95)
        self._draw_rect(cx - 150, cy - 50, 300, 120)
        glColor4f(0.3, 0.3, 0.4, 0.6)
        glLineWidth(2)
        glBegin(GL_LINE_LOOP)
        glVertex2f(cx - 150, cy - 50)
        glVertex2f(cx + 150, cy - 50)
        glVertex2f(cx + 150, cy + 70)
        glVertex2f(cx - 150, cy + 70)
        glEnd()

        text_renderer.draw_text_centered(cx, cy + 35, f"Delete '{self.confirm_delete}'?", 
                                        "medium", (1.0, 0.8, 0.8))
        text_renderer.draw_text_centered(cx, cy + 10, "This cannot be undone!", 
                                        "small", (0.7, 0.5, 0.5))

        glDisable(GL_BLEND)

        self.confirm_yes.draw()
        self.confirm_no.draw()

    def _draw_rect(self, x, y, w, h):
        glBegin(GL_QUADS)
        glVertex2f(x, y)
        glVertex2f(x + w, y)
        glVertex2f(x + w, y + h)
        glVertex2f(x, y + h)
        glEnd()


class WorldCreateScreen:
    """Screen to configure and create a new world."""
    
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.time = 0
        self.result = None  # None, "back", or world settings dict
        
        # Settings
        self.world_name = "New World"
        self.gamemode = "survival"
        self.show_coords = True
        self.seed_text = ""
        self.typing = "name"  # "name", "seed", or None
        
        # Buttons
        cx = screen_w // 2
        self.survival_btn = Button(cx - 155, 0, 150, 40, "Survival", (0.2, 0.5, 0.2), (0.3, 0.7, 0.3))
        self.creative_btn = Button(cx + 5, 0, 150, 40, "Creative", (0.3, 0.3, 0.6), (0.4, 0.4, 0.7))
        self.coords_btn = Button(cx - 75, 0, 150, 35, "Show Coords: ON", (0.3, 0.3, 0.3), (0.4, 0.4, 0.4))
        self.create_btn = Button(cx - 155, 0, 150, 45, "Create World", (0.2, 0.55, 0.2), (0.3, 0.75, 0.3))
        self.back_btn = Button(cx + 5, 0, 150, 45, "Cancel", (0.4, 0.2, 0.2), (0.6, 0.3, 0.3))

    def handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            my = self.screen_h - my
            cx = self.screen_w // 2

            # Check text field clicks
            name_field_y = self.screen_h - 160
            seed_field_y = self.screen_h - 260
            if cx - 150 <= mx <= cx + 150:
                if name_field_y - 5 <= my <= name_field_y + 30:
                    self.typing = "name"
                    return None
                elif seed_field_y - 5 <= my <= seed_field_y + 30:
                    self.typing = "seed"
                    return None

            self.typing = None

            # Buttons
            if self.survival_btn.contains(mx, my):
                self.gamemode = "survival"
            elif self.creative_btn.contains(mx, my):
                self.gamemode = "creative"
            elif self.coords_btn.contains(mx, my):
                self.show_coords = not self.show_coords
                self.coords_btn.text = f"Show Coords: {'ON' if self.show_coords else 'OFF'}"
            elif self.create_btn.contains(mx, my):
                if self.world_name.strip():
                    seed = int(self.seed_text) if self.seed_text.strip().isdigit() else None
                    return {
                        "action": "create",
                        "name": self.world_name.strip(),
                        "gamemode": self.gamemode,
                        "seed": seed,
                        "show_coords": self.show_coords,
                    }
            elif self.back_btn.contains(mx, my):
                return "back"

        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                return "back"
            elif event.key == K_RETURN:
                self.typing = None
            elif event.key == K_BACKSPACE:
                if self.typing == "name":
                    self.world_name = self.world_name[:-1]
                elif self.typing == "seed":
                    self.seed_text = self.seed_text[:-1]
            elif event.unicode and self.typing:
                if self.typing == "name" and len(self.world_name) < 30:
                    self.world_name += event.unicode
                elif self.typing == "seed" and event.unicode.isdigit() and len(self.seed_text) < 10:
                    self.seed_text += event.unicode

        return None

    def update(self, dt, mouse_pos):
        self.time += dt
        mx, my = mouse_pos
        my = self.screen_h - my

        self.survival_btn.hovered = self.survival_btn.contains(mx, my)
        self.creative_btn.hovered = self.creative_btn.contains(mx, my)
        self.coords_btn.hovered = self.coords_btn.contains(mx, my)
        self.create_btn.hovered = self.create_btn.contains(mx, my)
        self.back_btn.hovered = self.back_btn.contains(mx, my)

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

        # Background
        glBegin(GL_QUADS)
        glColor3f(0.06, 0.06, 0.1)
        glVertex2f(0, 0)
        glVertex2f(self.screen_w, 0)
        glColor3f(0.1, 0.12, 0.18)
        glVertex2f(self.screen_w, self.screen_h)
        glVertex2f(0, self.screen_h)
        glEnd()

        cx = self.screen_w // 2

        # Title
        text_renderer.draw_text_centered_shadow(cx, self.screen_h - 60, "CREATE NEW WORLD", 
                                                "title", (1.0, 1.0, 1.0), (0.2, 0.2, 0.2))

        # World Name field
        name_y = self.screen_h - 160
        text_renderer.draw_text_shadow(cx - 150, name_y + 35, "World Name:", 
                                       "medium", (0.8, 0.8, 0.8), (0.1, 0.1, 0.1))
        
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Name input box
        box_color = (0.15, 0.15, 0.2) if self.typing == "name" else (0.1, 0.1, 0.14)
        glColor4f(box_color[0], box_color[1], box_color[2], 0.9)
        self._draw_rect(cx - 150, name_y - 5, 300, 30)
        if self.typing == "name":
            glColor4f(0.3, 0.5, 0.7, 0.8)
        else:
            glColor4f(0.2, 0.2, 0.3, 0.6)
        glLineWidth(1)
        glBegin(GL_LINE_LOOP)
        glVertex2f(cx - 150, name_y - 5)
        glVertex2f(cx + 150, name_y - 5)
        glVertex2f(cx + 150, name_y + 25)
        glVertex2f(cx - 150, name_y + 25)
        glEnd()
        
        name_display = self.world_name
        if self.typing == "name" and int(self.time * 2) % 2 == 0:
            name_display += "_"
        text_renderer.draw_text(cx - 145, name_y, name_display, "medium", (1.0, 1.0, 1.0))

        glDisable(GL_BLEND)

        # Game Mode
        mode_y = self.screen_h - 220
        text_renderer.draw_text_shadow(cx - 150, mode_y + 35, "Game Mode:", 
                                       "medium", (0.8, 0.8, 0.8), (0.1, 0.1, 0.1))
        
        # Position buttons
        self.survival_btn.y = mode_y - 5
        self.creative_btn.y = mode_y - 5
        self.survival_btn.color = (0.2, 0.5, 0.2) if self.gamemode == "survival" else (0.2, 0.2, 0.2)
        self.creative_btn.color = (0.3, 0.3, 0.6) if self.gamemode == "creative" else (0.2, 0.2, 0.2)
        self.survival_btn.draw()
        self.creative_btn.draw()

        # Seed field
        seed_y = self.screen_h - 290
        text_renderer.draw_text_shadow(cx - 150, seed_y + 35, "Seed (optional):", 
                                       "medium", (0.8, 0.8, 0.8), (0.1, 0.1, 0.1))
        
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        box_color = (0.15, 0.15, 0.2) if self.typing == "seed" else (0.1, 0.1, 0.14)
        glColor4f(box_color[0], box_color[1], box_color[2], 0.9)
        self._draw_rect(cx - 150, seed_y - 5, 300, 30)
        if self.typing == "seed":
            glColor4f(0.3, 0.5, 0.7, 0.8)
        else:
            glColor4f(0.2, 0.2, 0.3, 0.6)
        glLineWidth(1)
        glBegin(GL_LINE_LOOP)
        glVertex2f(cx - 150, seed_y - 5)
        glVertex2f(cx + 150, seed_y - 5)
        glVertex2f(cx + 150, seed_y + 25)
        glVertex2f(cx - 150, seed_y + 25)
        glEnd()
        
        seed_display = self.seed_text if self.seed_text else "Random"
        if self.typing == "seed" and int(self.time * 2) % 2 == 0:
            seed_display = self.seed_text + "_"
        text_renderer.draw_text(cx - 145, seed_y, seed_display, "medium", 
                               (1.0, 1.0, 1.0) if self.seed_text else (0.4, 0.4, 0.4))
        
        glDisable(GL_BLEND)

        # Show Coordinates toggle
        coords_y = self.screen_h - 350
        self.coords_btn.y = coords_y - 5
        self.coords_btn.draw()

        # Create/Cancel buttons
        btn_y = 60
        self.create_btn.y = btn_y
        self.back_btn.y = btn_y
        self.create_btn.draw()
        self.back_btn.draw()

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_FOG)

    def _draw_rect(self, x, y, w, h):
        glBegin(GL_QUADS)
        glVertex2f(x, y)
        glVertex2f(x + w, y)
        glVertex2f(x + w, y + h)
        glVertex2f(x, y + h)
        glEnd()

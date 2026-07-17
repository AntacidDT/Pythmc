"""Pythmc - World Selection and Creation Screens (V2.0)"""

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import time
from constants import *
from settings_manager import settings_manager, DISPLAY_NAMES, RANGES, DEFAULTS
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

        glColor4f(0, 0, 0, 0.3)
        self._draw_rect(self.x + 2, self.y - 2, self.w, self.h)

        glColor3f(r * 0.5, g * 0.5, b * 0.5)
        self._draw_rect(self.x, self.y - 1, self.w, self.h)
        glColor3f(r, g, b)
        self._draw_rect(self.x, self.y, self.w, self.h)

        glColor4f(1, 1, 1, 0.08 + self.hover_anim * 0.1)
        self._draw_rect(self.x + 2, self.y + self.h - 6, self.w - 4, 4)

        glColor4f(1, 1, 1, 0.12 + self.hover_anim * 0.2)
        glLineWidth(1)
        glBegin(GL_LINE_LOOP)
        glVertex2f(self.x, self.y)
        glVertex2f(self.x + self.w, self.y)
        glVertex2f(self.x + self.w, self.y + self.h)
        glVertex2f(self.x, self.y + self.h)
        glEnd()

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
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.worlds = []
        self.selected_idx = -1
        self.scroll_offset = 0
        self.time = 0
        self.result = None
        self.confirm_delete = None
        self.cam_yaw = 0
        self.bg_world = None
        self.bg_world_loaded = False
        self._update_buttons()

    def _update_buttons(self):
        cx = self.screen_w // 2
        self.play_btn = Button(cx - 160, 80, 150, 45, "Play World", (0.2, 0.5, 0.2), (0.3, 0.7, 0.3))
        self.new_btn = Button(cx + 10, 80, 150, 45, "Make New", (0.25, 0.35, 0.55), (0.35, 0.5, 0.7))
        self.delete_btn = Button(cx - 160, 25, 150, 45, "Delete", (0.5, 0.2, 0.2), (0.7, 0.3, 0.3))
        self.back_btn = Button(cx + 10, 25, 150, 45, "Back", (0.35, 0.35, 0.35), (0.5, 0.5, 0.5))
        self.confirm_yes = Button(cx - 80, self.screen_h // 2, 70, 40, "Yes", (0.5, 0.2, 0.2), (0.7, 0.3, 0.3))
        self.confirm_no = Button(cx + 10, self.screen_h // 2, 70, 40, "No", (0.25, 0.5, 0.25), (0.35, 0.7, 0.35))

    def _ensure_bg_world(self):
        if self.bg_world_loaded:
            return
        from world import World
        self.bg_world = World(seed=42)
        for cx in range(-2, 3):
            for cz in range(-2, 3):
                self.bg_world.get_chunk(cx, cz)
        self.bg_world_loaded = True

    def refresh(self):
        self.worlds = list_worlds()
        if self.selected_idx >= len(self.worlds):
            self.selected_idx = len(self.worlds) - 1

    def handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            my = self.screen_h - my
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
            if self.back_btn.contains(mx, my):
                return "back"
            if self.new_btn.contains(mx, my):
                return "create_new"
            if self.play_btn.contains(mx, my) and self.selected_idx >= 0:
                return {"action": "play", "world": self.worlds[self.selected_idx]}
            if self.delete_btn.contains(mx, my) and self.selected_idx >= 0:
                self.confirm_delete = self.worlds[self.selected_idx]["name"]
                return None
            list_y_start = self.screen_h - 160
            item_h = 60
            for i in range(min(len(self.worlds), 8)):
                idx = i + self.scroll_offset
                if idx >= len(self.worlds):
                    break
                item_y = list_y_start - i * item_h
                if item_y <= my <= item_y + item_h - 5:
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
        self.cam_yaw += dt * 4
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
        self._ensure_bg_world()

        # 3D world background
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)
        glClearColor(0.45, 0.55, 0.75, 1.0)

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluPerspective(60, self.screen_w / self.screen_h, 0.1, 500.0)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
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

        if self.bg_world:
            for cx in range(-2, 3):
                for cz in range(-2, 3):
                    self.bg_world.get_chunk(cx, cz).draw_opaque()
            for cx in range(-2, 3):
                for cz in range(-2, 3):
                    self.bg_world.get_chunk(cx, cz).draw_transparent()

        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

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
        text_renderer.draw_text_centered_shadow(cx, self.screen_h - 60, "SELECT WORLD",
                                                "title", (1.0, 1.0, 1.0), (0.2, 0.2, 0.2))

        list_x = cx - 250
        list_y_start = self.screen_h - 140
        item_h = 60

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        if not self.worlds:
            text_renderer.draw_text_centered(cx, list_y_start - 80, "No worlds yet. Make one!",
                                            "medium", (0.5, 0.5, 0.5))
        else:
            for i in range(min(len(self.worlds), 8)):
                idx = i + self.scroll_offset
                if idx >= len(self.worlds):
                    break
                world = self.worlds[idx]
                item_y = list_y_start - i * item_h

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

                text_renderer.draw_text_shadow(list_x + 15, item_y + item_h - 22,
                                              world["name"], "medium", (1.0, 1.0, 1.0), (0.1, 0.1, 0.1))

                mode_color = (0.3, 0.8, 0.3) if world["gamemode"] == "survival" else (0.5, 0.5, 0.8)
                mode_str = f"{world['gamemode'].capitalize()} | Seed: {world['seed']}"
                if world.get("io_enabled"):
                    mode_str += " | IO"
                text_renderer.draw_text(list_x + 15, item_y + 5, mode_str, "small", mode_color)

                # Stats line
                days = world.get("days_survived", 0)
                dug = world.get("blocks_dug", 0)
                placed = world.get("blocks_placed", 0)
                if days > 0 or dug > 0 or placed > 0:
                    stats_str = f"Day {days} | Dug: {dug} | Placed: {placed}"
                    text_renderer.draw_text(list_x + 15, item_y - 8, stats_str, "small", (0.45, 0.45, 0.5))

                pt = world.get("play_time", 0)
                if pt > 0:
                    hours = int(pt // 3600)
                    mins = int((pt % 3600) // 60)
                    text_renderer.draw_text(list_x + 380, item_y + item_h - 22,
                                           f"{hours}h {mins}m", "small", (0.5, 0.5, 0.5))

        glDisable(GL_BLEND)

        self.play_btn.draw()
        self.new_btn.draw()
        self.delete_btn.draw()
        self.back_btn.draw()

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
        glColor4f(0, 0, 0, 0.5)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(self.screen_w, 0)
        glVertex2f(self.screen_w, self.screen_h)
        glVertex2f(0, self.screen_h)
        glEnd()

        cx = self.screen_w // 2
        cy = self.screen_h // 2
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


# ─── Settings tabs ────────────────────────────────────────────────────────
SETTING_TABS = ["physics", "world", "screen"]
SETTING_TAB_LABELS = {"physics": "Physics", "world": "World", "screen": "Screen"}


class WorldCreateScreen:
    """Screen to configure and make a new world (V2.0)."""

    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.time = 0
        self.cam_yaw = 0
        self.bg_world = None
        self.bg_world_loaded = False

        self.world_name = "New World"
        self.gamemode = "survival"
        self.show_coords = True
        self.io_enabled = False
        self.seed_text = ""
        self.typing = "name"

        # Per-world settings (copies of defaults)
        self.world_settings = {}
        for cat in SETTING_TABS:
            self.world_settings[cat] = dict(DEFAULTS.get(cat, {}))
        self.active_tab = "physics"
        self.setting_scroll = 0

        cx = screen_w // 2
        self.survival_btn = Button(cx - 155, 0, 150, 40, "Survival", (0.2, 0.5, 0.2), (0.3, 0.7, 0.3))
        self.creative_btn = Button(cx + 5, 0, 150, 40, "Creative", (0.3, 0.3, 0.6), (0.4, 0.4, 0.7))
        self.coords_btn = Button(cx - 75, 0, 150, 35, "Show Coords: ON", (0.3, 0.3, 0.3), (0.4, 0.4, 0.4))
        self.io_btn = Button(cx - 75, 0, 150, 35, "IO: OFF", (0.3, 0.3, 0.3), (0.4, 0.4, 0.4))
        self.create_btn = Button(cx - 155, 0, 150, 45, "Make World", (0.2, 0.55, 0.2), (0.3, 0.75, 0.3))
        self.back_btn = Button(cx + 5, 0, 150, 45, "Cancel", (0.4, 0.2, 0.2), (0.6, 0.3, 0.3))
        self.reset_btn = Button(cx - 75, 0, 150, 35, "Reset Defaults", (0.5, 0.3, 0.2), (0.65, 0.4, 0.3))

        # Tab buttons
        self.tab_buttons = []
        tab_w = 120
        tab_start_x = cx - (len(SETTING_TABS) * tab_w + (len(SETTING_TABS) - 1) * 5) // 2
        for i, tab_key in enumerate(SETTING_TABS):
            self.tab_buttons.append(Button(
                tab_start_x + i * (tab_w + 5), 0, tab_w, 30,
                SETTING_TAB_LABELS[tab_key],
                (0.2, 0.25, 0.4), (0.3, 0.35, 0.55)
            ))

    def _ensure_bg_world(self):
        if self.bg_world_loaded:
            return
        from world import World
        self.bg_world = World(seed=42)
        for cx in range(-2, 3):
            for cz in range(-2, 3):
                self.bg_world.get_chunk(cx, cz)
        self.bg_world_loaded = True

    def _get_setting_items(self):
        """Get list of (key, display_name, value, default, range) for active tab."""
        cat = self.active_tab
        items = []
        keys = list(self.world_settings.get(cat, {}).keys())
        for key in keys:
            val = self.world_settings[cat][key]
            display = DISPLAY_NAMES.get(cat, {}).get(key, key)
            default = DEFAULTS.get(cat, {}).get(key, val)
            rng = RANGES.get(cat, {}).get(key, (None, None))
            items.append((key, display, val, default, rng))
        return items

    def handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            my = self.screen_h - my
            cx = self.screen_w // 2

            # Tab clicks
            for i, tab_btn in enumerate(self.tab_buttons):
                tab_btn.y = self.screen_h - 540
                if tab_btn.contains(mx, my):
                    self.active_tab = SETTING_TABS[i]
                    self.setting_scroll = 0
                    return None

            # Setting value +/- clicks
            items = self._get_setting_items()
            for i, (key, display, val, default, rng) in enumerate(items):
                row_y = self.screen_h - 580 - i * 30 + self.setting_scroll
                if row_y < 100 or row_y > self.screen_h - 200:
                    continue
                # Minus button
                if cx + 140 <= mx <= cx + 170 and row_y <= my <= row_y + 22:
                    step = 1 if isinstance(val, int) else 0.1
                    self.world_settings[self.active_tab][key] = round(val - step, 2)
                    if rng[0] is not None:
                        self.world_settings[self.active_tab][key] = max(rng[0], self.world_settings[self.active_tab][key])
                    return None
                # Plus button
                if cx + 175 <= mx <= cx + 205 and row_y <= my <= row_y + 22:
                    step = 1 if isinstance(val, int) else 0.1
                    self.world_settings[self.active_tab][key] = round(val + step, 2)
                    if rng[1] is not None:
                        self.world_settings[self.active_tab][key] = min(rng[1], self.world_settings[self.active_tab][key])
                    return None
                # Reset to default
                if cx + 210 <= mx <= cx + 250 and row_y <= my <= row_y + 22:
                    self.world_settings[self.active_tab][key] = default
                    return None

            # Reset defaults button
            reset_y = 130
            self.reset_btn.y = reset_y
            if self.reset_btn.contains(mx, my):
                self.world_settings[self.active_tab] = dict(DEFAULTS.get(self.active_tab, {}))
                return None

            # Text field clicks
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
            elif self.io_btn.contains(mx, my):
                self.io_enabled = not self.io_enabled
                self.io_btn.text = f"IO: {'ON' if self.io_enabled else 'OFF'}"
                self.io_btn.color = (0.2, 0.5, 0.2) if self.io_enabled else (0.3, 0.3, 0.3)
            elif self.create_btn.contains(mx, my):
                if self.world_name.strip():
                    seed = int(self.seed_text) if self.seed_text.strip().isdigit() else None
                    return {
                        "action": "create",
                        "name": self.world_name.strip(),
                        "gamemode": self.gamemode,
                        "seed": seed,
                        "show_coords": self.show_coords,
                        "io_enabled": self.io_enabled,
                        "world_settings": dict(self.world_settings),
                    }
            elif self.back_btn.contains(mx, my):
                return "back"

        elif event.type == MOUSEWHEEL:
            # Scroll settings
            mx, my = pygame.mouse.get_pos()
            my = self.screen_h - my
            if my < self.screen_h - 200 and my > 100:
                self.setting_scroll += event.y * 30
                max_scroll = max(0, len(self._get_setting_items()) * 30 - 300)
                self.setting_scroll = max(-max_scroll, min(0, self.setting_scroll))

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
        self.cam_yaw += dt * 4
        mx, my = mouse_pos
        my = self.screen_h - my

        self.survival_btn.hovered = self.survival_btn.contains(mx, my)
        self.creative_btn.hovered = self.creative_btn.contains(mx, my)
        self.coords_btn.hovered = self.coords_btn.contains(mx, my)
        self.io_btn.hovered = self.io_btn.contains(mx, my)
        self.create_btn.hovered = self.create_btn.contains(mx, my)
        self.back_btn.hovered = self.back_btn.contains(mx, my)
        self.reset_btn.hovered = self.reset_btn.contains(mx, my)

        for i, tab_btn in enumerate(self.tab_buttons):
            tab_btn.y = self.screen_h - 540
            tab_btn.hovered = tab_btn.contains(mx, my)

    def draw(self):
        self._ensure_bg_world()

        # 3D world background
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)
        glClearColor(0.45, 0.55, 0.75, 1.0)

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluPerspective(60, self.screen_w / self.screen_h, 0.1, 500.0)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
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

        if self.bg_world:
            for cx in range(-2, 3):
                for cz in range(-2, 3):
                    self.bg_world.get_chunk(cx, cz).draw_opaque()
            for cx in range(-2, 3):
                for cz in range(-2, 3):
                    self.bg_world.get_chunk(cx, cz).draw_transparent()

        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

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

        # Title
        text_renderer.draw_text_centered_shadow(cx, self.screen_h - 60, "MAKE NEW WORLD",
                                                "title", (1.0, 1.0, 1.0), (0.2, 0.2, 0.2))

        # ─── Left side: basic settings ────────────────────────────────────
        left_x = cx - 310

        # World Name
        name_y = self.screen_h - 160
        text_renderer.draw_text_shadow(left_x, name_y + 35, "World Name:",
                                       "medium", (0.8, 0.8, 0.8), (0.1, 0.1, 0.1))
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        box_color = (0.15, 0.15, 0.2) if self.typing == "name" else (0.1, 0.1, 0.14)
        glColor4f(box_color[0], box_color[1], box_color[2], 0.9)
        self._draw_rect(left_x, name_y - 5, 280, 30)
        if self.typing == "name":
            glColor4f(0.3, 0.5, 0.7, 0.8)
        else:
            glColor4f(0.2, 0.2, 0.3, 0.6)
        glLineWidth(1)
        glBegin(GL_LINE_LOOP)
        glVertex2f(left_x, name_y - 5)
        glVertex2f(left_x + 280, name_y - 5)
        glVertex2f(left_x + 280, name_y + 25)
        glVertex2f(left_x, name_y + 25)
        glEnd()
        name_display = self.world_name
        if self.typing == "name" and int(self.time * 2) % 2 == 0:
            name_display += "_"
        text_renderer.draw_text(left_x + 5, name_y, name_display, "medium", (1.0, 1.0, 1.0))

        # Game Mode
        mode_y = self.screen_h - 220
        text_renderer.draw_text_shadow(left_x, mode_y + 35, "Game Mode:",
                                       "medium", (0.8, 0.8, 0.8), (0.1, 0.1, 0.1))
        self.survival_btn.x = left_x
        self.creative_btn.x = left_x + 155
        self.survival_btn.y = mode_y - 5
        self.creative_btn.y = mode_y - 5
        self.survival_btn.color = (0.2, 0.5, 0.2) if self.gamemode == "survival" else (0.2, 0.2, 0.2)
        self.creative_btn.color = (0.3, 0.3, 0.6) if self.gamemode == "creative" else (0.2, 0.2, 0.2)
        self.survival_btn.draw()
        self.creative_btn.draw()

        # Seed
        seed_y = self.screen_h - 290
        text_renderer.draw_text_shadow(left_x, seed_y + 35, "Seed (optional):",
                                       "medium", (0.8, 0.8, 0.8), (0.1, 0.1, 0.1))
        box_color = (0.15, 0.15, 0.2) if self.typing == "seed" else (0.1, 0.1, 0.14)
        glColor4f(box_color[0], box_color[1], box_color[2], 0.9)
        self._draw_rect(left_x, seed_y - 5, 280, 30)
        if self.typing == "seed":
            glColor4f(0.3, 0.5, 0.7, 0.8)
        else:
            glColor4f(0.2, 0.2, 0.3, 0.6)
        glLineWidth(1)
        glBegin(GL_LINE_LOOP)
        glVertex2f(left_x, seed_y - 5)
        glVertex2f(left_x + 280, seed_y - 5)
        glVertex2f(left_x + 280, seed_y + 25)
        glVertex2f(left_x, seed_y + 25)
        glEnd()
        seed_display = self.seed_text if self.seed_text else "Random"
        if self.typing == "seed" and int(self.time * 2) % 2 == 0:
            seed_display = (self.seed_text or "") + "_"
        text_renderer.draw_text(left_x + 5, seed_y, seed_display, "medium",
                               (1.0, 1.0, 1.0) if self.seed_text else (0.4, 0.4, 0.4))

        # Toggles
        toggle_y = self.screen_h - 350
        self.coords_btn.x = left_x
        self.coords_btn.y = toggle_y
        self.coords_btn.draw()

        self.io_btn.x = left_x
        self.io_btn.y = toggle_y - 40
        self.io_btn.draw()

        glDisable(GL_BLEND)

        # ─── Right side: settings tabs ────────────────────────────────────
        right_x = cx + 20
        panel_w = 310

        # Tab panel background
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(0.08, 0.08, 0.12, 0.85)
        self._draw_rect(right_x, 85, panel_w, self.screen_h - 170)
        glColor4f(0.2, 0.2, 0.3, 0.4)
        glLineWidth(1)
        glBegin(GL_LINE_LOOP)
        glVertex2f(right_x, 85)
        glVertex2f(right_x + panel_w, 85)
        glVertex2f(right_x + panel_w, self.screen_h - 85)
        glVertex2f(right_x, self.screen_h - 85)
        glEnd()

        # Tabs
        for i, tab_btn in enumerate(self.tab_buttons):
            tab_btn.y = self.screen_h - 540
            if SETTING_TABS[i] == self.active_tab:
                tab_btn.color = (0.3, 0.4, 0.6)
            else:
                tab_btn.color = (0.2, 0.25, 0.4)
            tab_btn.draw()

        # Setting items
        items = self._get_setting_items()
        for i, (key, display, val, default, rng) in enumerate(items):
            row_y = self.screen_h - 580 - i * 30 + self.setting_scroll
            if row_y < 100 or row_y > self.screen_h - 200:
                continue

            is_default = (val == default)
            val_color = (0.6, 0.7, 0.6) if is_default else (1.0, 0.85, 0.4)

            # Label
            text_renderer.draw_text(right_x + 10, row_y, display, "small", (0.7, 0.7, 0.75))

            # Value
            val_str = f"{val:.1f}" if isinstance(val, float) else str(val)
            text_renderer.draw_text(right_x + 150, row_y, val_str, "small", val_color)

            # - button
            glColor4f(0.3, 0.3, 0.4, 0.7)
            self._draw_rect(right_x + 140, row_y - 2, 22, 18)
            text_renderer.draw_text(right_x + 144, row_y, "-", "small", (0.8, 0.8, 0.8))

            # + button
            glColor4f(0.3, 0.3, 0.4, 0.7)
            self._draw_rect(right_x + 175, row_y - 2, 22, 18)
            text_renderer.draw_text(right_x + 179, row_y, "+", "small", (0.8, 0.8, 0.8))

            # Reset button
            if not is_default:
                glColor4f(0.5, 0.3, 0.2, 0.7)
                self._draw_rect(right_x + 210, row_y - 2, 35, 18)
                text_renderer.draw_text(right_x + 215, row_y, "RST", "small", (0.9, 0.6, 0.5))

        glDisable(GL_BLEND)

        # Reset defaults button
        self.reset_btn.y = 130
        self.reset_btn.draw()

        # Create/Cancel buttons
        btn_y = 30
        self.create_btn.y = btn_y
        self.back_btn.y = btn_y
        self.create_btn.x = left_x
        self.back_btn.x = left_x + 155
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

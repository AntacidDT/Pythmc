"""Pythmc - Furnace UI with Smelting System"""

import pygame
from pygame.locals import *
from OpenGL.GL import *
from constants import *
from inventory_ui import InventorySlot


class FurnaceUI:
    """Furnace smelting interface."""
    
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.open = False
        self.slot_rects = {}
        
        # Furnace slots
        self.input_slot = InventorySlot()
        self.fuel_slot = InventorySlot()
        self.output_slot = InventorySlot()
        
        # Smelting state
        self.smelt_progress = 0.0  # 0 to 1
        self.smelt_time = 10.0  # seconds per item
        self.fuel_burn_time = 0.0  # remaining fuel burn time
        self.fuel_total_time = 0.0
        
        # Cooking state
        self.cooking = False
        self.cook_item = None
        
    def toggle(self):
        self.open = not self.open
        
    def handle_click(self, mx, my, inventory, button=1):
        """Handle mouse click on furnace UI."""
        my = self.screen_h - my
        
        for key, (sx, sy, sw, sh) in self.slot_rects.items():
            if sx <= mx <= sx + sw and sy <= my <= sy + sh:
                self._handle_slot_click(key, inventory, button)
                return True
        return False
    
    def _handle_slot_click(self, key, inventory, button):
        if key == "furnace_input":
            self._swap_slot(self.input_slot, inventory)
        elif key == "furnace_fuel":
            self._swap_slot(self.fuel_slot, inventory)
        elif key == "furnace_output":
            if not self.output_slot.is_empty() and inventory.held.is_empty():
                inventory.held.item = self.output_slot.item
                inventory.held.count = self.output_slot.count
                self.output_slot.clear()
        elif key.startswith("inv_"):
            parts = key.split("_")
            section = parts[1]
            idx = int(parts[2])
            if section == "hotbar":
                slot = inventory.hotbar[idx]
            elif section == "main":
                y, x = divmod(idx, 9)
                slot = inventory.main[y][x]
            else:
                return
            if button == 1:
                if inventory.held.is_empty():
                    if not slot.is_empty():
                        inventory.held.item = slot.item
                        inventory.held.count = slot.count
                        slot.clear()
                else:
                    if slot.is_empty():
                        slot.item = inventory.held.item
                        slot.count = inventory.held.count
                        inventory.held.clear()
                    elif slot.item == inventory.held.item:
                        can_add = min(inventory.held.count, 64 - slot.count)
                        slot.count += can_add
                        inventory.held.count -= can_add
                        if inventory.held.count <= 0:
                            inventory.held.clear()
                    else:
                        temp_item, temp_count = slot.item, slot.count
                        slot.item = inventory.held.item
                        slot.count = inventory.held.count
                        inventory.held.item = temp_item
                        inventory.held.count = temp_count
    
    def _swap_slot(self, furnace_slot, inventory):
        if inventory.held.is_empty():
            if not furnace_slot.is_empty():
                inventory.held.item = furnace_slot.item
                inventory.held.count = furnace_slot.count
                furnace_slot.clear()
        else:
            if furnace_slot.is_empty():
                furnace_slot.item = inventory.held.item
                furnace_slot.count = inventory.held.count
                inventory.held.clear()
            elif furnace_slot.item == inventory.held.item:
                can_add = min(inventory.held.count, 64 - furnace_slot.count)
                furnace_slot.count += can_add
                inventory.held.count -= can_add
                if inventory.held.count <= 0:
                    inventory.held.clear()
    
    def update(self, dt):
        """Update smelting progress."""
        if not self.open:
            return
        
        # Check if we can smelt
        can_smelt = False
        if not self.input_slot.is_empty() and self.input_slot.item in FURNACE_RECIPES:
            output_item = FURNACE_RECIPES[self.input_slot.item]
            # Check output has space
            if self.output_slot.is_empty() or (self.output_slot.item == output_item and self.output_slot.count < 64):
                can_smelt = True
        
        # Fuel management
        if self.fuel_burn_time > 0:
            self.fuel_burn_time -= dt
            if can_smelt:
                self.smelt_progress += dt / self.smelt_time
                if self.smelt_progress >= 1.0:
                    self._complete_smelt()
        elif can_smelt and not self.fuel_slot.is_empty():
            # Try to consume fuel
            if self.fuel_slot.item in FUEL_VALUES:
                self.fuel_burn_time = FUEL_VALUES[self.fuel_slot.item]
                self.fuel_total_time = self.fuel_burn_time
                self.fuel_slot.count -= 1
                if self.fuel_slot.count <= 0:
                    self.fuel_slot.clear()
        else:
            self.smelt_progress = 0.0
    
    def _complete_smelt(self):
        output_item = FURNACE_RECIPES[self.input_slot.item]
        
        if self.output_slot.is_empty():
            self.output_slot.item = output_item
            self.output_slot.count = 1
        else:
            self.output_slot.count += 1
        
        self.input_slot.count -= 1
        if self.input_slot.count <= 0:
            self.input_slot.clear()
        
        self.smelt_progress = 0.0
    
    def draw(self, inventory):
        if not self.open:
            return
        
        glDisable(GL_LIGHTING)
        glDisable(GL_FOG)
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.screen_w, 0, self.screen_h, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        cx = self.screen_w // 2
        cy = self.screen_h // 2

        # Dark overlay
        glColor4f(0, 0, 0, 0.5)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(self.screen_w, 0)
        glVertex2f(self.screen_w, self.screen_h)
        glVertex2f(0, self.screen_h)
        glEnd()

        self.slot_rects.clear()
        slot_size = 40
        gap = 4

        # ─── Furnace Panel ───────────────────────────────────────────────
        panel_x = cx - 100
        panel_y = cy + 20

        # Panel background
        glColor4f(0.15, 0.15, 0.2, 0.9)
        self._draw_rect(panel_x - 15, panel_y - 15, 230, 160)

        # Title
        glColor3f(0.8, 0.8, 0.8)
        self._draw_small_text(panel_x, panel_y + 130, "Furnace")

        # Input slot
        in_x = panel_x
        in_y = panel_y + slot_size + gap + 10
        self._draw_slot(in_x, in_y, slot_size, self.input_slot)
        self.slot_rects["furnace_input"] = (in_x, in_y, slot_size, slot_size)

        # Arrow
        arrow_x = in_x + slot_size + 10
        arrow_y = in_y + slot_size // 2
        self._draw_arrow(arrow_x, arrow_y, 25, 12)

        # Progress indicator
        if self.smelt_progress > 0:
            progress_w = 25 * self.smelt_progress
            glColor3f(0.9, 0.6, 0.1)
            glBegin(GL_QUADS)
            glVertex2f(arrow_x, arrow_y - 4)
            glVertex2f(arrow_x + progress_w, arrow_y - 4)
            glVertex2f(arrow_x + progress_w, arrow_y + 4)
            glVertex2f(arrow_x, arrow_y + 4)
            glEnd()

        # Output slot
        out_x = arrow_x + 35
        out_y = in_y
        self._draw_slot(out_x, out_y, slot_size, self.output_slot, highlight=True)
        self.slot_rects["furnace_output"] = (out_x, out_y, slot_size, slot_size)

        # Fuel slot (below input)
        fuel_x = in_x
        fuel_y = in_y - slot_size - gap - 15
        self._draw_slot(fuel_x, fuel_y, slot_size, self.fuel_slot)
        self.slot_rects["furnace_fuel"] = (fuel_x, fuel_y, slot_size, slot_size)

        # Fuel label
        glColor3f(0.6, 0.6, 0.6)
        self._draw_small_text(fuel_x + slot_size + 5, fuel_y + 15, "Fuel")

        # Flame indicator
        if self.fuel_burn_time > 0:
            flame_progress = self.fuel_burn_time / self.fuel_total_time if self.fuel_total_time > 0 else 0
            glColor3f(0.9, 0.4, 0.1)
            flame_h = 20 * flame_progress
            glBegin(GL_QUADS)
            glVertex2f(fuel_x + slot_size + 5, fuel_y + flame_h)
            glVertex2f(fuel_x + slot_size + 15, fuel_y + flame_h)
            glVertex2f(fuel_x + slot_size + 15, fuel_y + 20)
            glVertex2f(fuel_x + slot_size + 5, fuel_y + 20)
            glEnd()

        # ─── Player Inventory ────────────────────────────────────────────
        inv_panel_y = cy - 160
        inv_x = cx - (9 * (slot_size + gap)) // 2

        glColor4f(0.15, 0.15, 0.2, 0.9)
        self._draw_rect(inv_x - 10, inv_panel_y - 10,
                       9 * (slot_size + gap) + 16,
                       3 * (slot_size + gap) + 50)

        glColor3f(0.8, 0.8, 0.8)
        self._draw_small_text(inv_x, inv_panel_y + 3 * (slot_size + gap) + 10, "Inventory")

        for row in range(3):
            for col in range(9):
                sx = inv_x + col * (slot_size + gap)
                sy = inv_panel_y + (2 - row) * (slot_size + gap)
                slot = inventory.main[row][col]
                self._draw_slot(sx, sy, slot_size, slot)
                self.slot_rects[f"inv_main_{row * 9 + col}"] = (sx, sy, slot_size, slot_size)

        hotbar_y = inv_panel_y - slot_size - gap - 15
        for i in range(9):
            sx = inv_x + i * (slot_size + gap)
            slot = inventory.hotbar[i]
            self._draw_slot(sx, hotbar_y, slot_size, slot)
            self.slot_rects[f"inv_hotbar_{i}"] = (sx, hotbar_y, slot_size, slot_size)

        # Held item
        if not inventory.held.is_empty():
            mx, my = pygame.mouse.get_pos()
            my = self.screen_h - my
            self._draw_slot(mx - slot_size // 2, my - slot_size // 2,
                          slot_size, inventory.held)

        # Hints
        hint_y = cy - 220
        glColor4f(0.6, 0.6, 0.6, 0.7)
        self._draw_small_text(cx - 80, hint_y, "ESC to close")

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_FOG)

    def _draw_slot(self, x, y, size, slot, highlight=False):
        if highlight:
            glColor4f(0.25, 0.35, 0.2, 0.9)
        else:
            glColor4f(0.12, 0.12, 0.15, 0.9)
        self._draw_rect(x, y, size, size)

        glColor4f(0.4, 0.4, 0.45, 0.8)
        glLineWidth(1)
        glBegin(GL_LINE_LOOP)
        glVertex2f(x, y)
        glVertex2f(x + size, y)
        glVertex2f(x + size, y + size)
        glVertex2f(x, y + size)
        glEnd()

        if not slot.is_empty():
            colors = ITEM_COLORS.get(slot.item)
            if colors:
                color = colors[1]
                pad = 4
                glColor3f(*color)
                glBegin(GL_QUADS)
                glVertex2f(x + pad, y + pad)
                glVertex2f(x + size - pad, y + pad)
                glVertex2f(x + size - pad, y + size - pad)
                glVertex2f(x + pad, y + size - pad)
                glEnd()

            if slot.count > 1:
                glColor3f(1, 1, 1)
                self._draw_tiny_number(x + size - 14, y + 2, slot.count)

    def _draw_rect(self, x, y, w, h):
        glBegin(GL_QUADS)
        glVertex2f(x, y)
        glVertex2f(x + w, y)
        glVertex2f(x + w, y + h)
        glVertex2f(x, y + h)
        glEnd()

    def _draw_arrow(self, x, y, w, h):
        glBegin(GL_TRIANGLES)
        glVertex2f(x, y + h // 2)
        glVertex2f(x + w, y + h)
        glVertex2f(x + w, y)
        glEnd()

    def _draw_small_text(self, x, y, text):
        for i, ch in enumerate(text):
            self._draw_small_char(x + i * 8, y, ch)

    def _draw_small_char(self, x, y, ch):
        glyphs = {
            'C': [(8,0,0,0),(0,0,0,10),(0,10,8,10)],
            'r': [(0,0,0,6),(0,6,4,6)],
            'a': [(0,0,0,6),(0,6,8,6),(8,6,8,0),(8,0,0,0)],
            'f': [(8,10,0,10),(0,10,0,0),(0,5,4,5)],
            't': [(4,0,4,10),(2,8,6,8)],
            'i': [(4,0,4,10)],
            'n': [(0,0,0,6),(0,6,8,6),(8,6,8,0)],
            'g': [(0,0,0,6),(0,6,8,6),(8,6,8,0),(8,0,0,0),(8,0,8,-2)],
            'I': [(2,0,6,0),(4,0,4,10),(2,10,6,10)],
            'v': [(0,10,4,0),(4,0,8,10)],
            'e': [(0,0,0,6),(0,6,8,6),(8,6,8,8),(8,8,0,8),(0,0,8,0)],
            'o': [(0,0,0,6),(0,6,8,6),(8,6,8,0),(8,0,0,0)],
            'y': [(0,10,4,4),(8,10,4,4),(4,4,4,0)],
            'l': [(4,0,4,10)],
            'k': [(0,0,0,10),(8,10,0,5),(0,5,8,0)],
            ' ': [],
            'p': [(0,0,0,6),(0,6,8,6),(8,6,8,0),(8,0,0,0),(0,0,0,-4)],
            'u': [(0,6,0,0),(0,0,8,0),(8,0,8,6)],
            'h': [(0,0,0,10),(0,5,8,5),(8,5,8,0)],
            's': [(8,0,0,0),(0,0,0,4),(0,4,8,4),(8,4,8,8),(8,8,0,8)],
            'd': [(0,6,0,0),(0,0,8,0),(8,0,8,6),(8,6,0,6)],
            'm': [(0,0,0,6),(0,6,4,3),(4,3,8,6),(8,6,8,0)],
            'b': [(0,0,0,10),(0,10,6,10),(6,10,8,8),(8,8,8,2),(8,2,6,0),(6,0,0,0)],
            'w': [(0,10,0,0),(0,0,4,4),(4,4,8,0),(8,0,8,10)],
            'R': [(0,0,0,10),(0,10,8,10),(8,10,8,5),(8,5,0,5),(4,5,8,0)],
            'S': [(8,0,0,0),(0,0,0,5),(0,5,8,5),(8,5,8,10),(8,10,0,10)],
            'P': [(0,0,0,10),(0,10,8,10),(8,10,8,5),(8,5,0,5)],
            'E': [(8,0,0,0),(0,0,0,10),(0,10,8,10),(0,5,5,5)],
            '1': [(4,0,4,10),(2,8,4,10)],
            '2': [(0,10,8,10),(8,10,8,5),(8,5,0,5),(0,5,0,0),(0,0,8,0)],
            'x': [(0,0,8,8),(0,8,8,0)],
        }
        segs = glyphs.get(ch, [])
        glBegin(GL_LINES)
        for s in segs:
            glVertex2f(x + s[0] * 0.6, y + s[1] * 0.6)
            glVertex2f(x + s[2] * 0.6, y + s[3] * 0.6)
        glEnd()

    def _draw_tiny_number(self, x, y, num):
        text = str(num)
        for i, ch in enumerate(text):
            self._draw_tiny_digit(x + i * 7, y, ch)

    def _draw_tiny_digit(self, x, y, ch):
        glyphs = {
            '0': [(0,0,0,10),(0,10,6,10),(6,10,6,0),(6,0,0,0)],
            '1': [(3,0,3,10),(1,8,3,10)],
            '2': [(0,10,6,10),(6,10,6,5),(6,5,0,5),(0,5,0,0),(0,0,6,0)],
            '3': [(0,10,6,10),(6,10,6,0),(0,0,6,0),(0,5,6,5)],
            '4': [(0,10,0,5),(0,5,6,5),(6,10,6,0)],
            '5': [(6,10,0,10),(0,10,0,5),(0,5,6,5),(6,5,6,0),(6,0,0,0)],
            '6': [(6,10,0,10),(0,10,0,0),(0,0,6,0),(6,0,6,5),(6,5,0,5)],
            '7': [(0,10,6,10),(6,10,3,0)],
            '8': [(0,0,0,10),(0,10,6,10),(6,10,6,0),(6,0,0,0),(0,5,6,5)],
            '9': [(6,0,6,10),(0,10,6,10),(0,10,0,5),(0,5,6,5)],
        }
        segs = glyphs.get(ch, [])
        glLineWidth(1)
        glBegin(GL_LINES)
        for s in segs:
            glVertex2f(x + s[0] * 0.5, y + s[1] * 0.5)
            glVertex2f(x + s[2] * 0.5, y + s[3] * 0.5)
        glEnd()

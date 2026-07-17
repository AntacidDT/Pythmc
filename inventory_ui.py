"""Pythmc - Inventory and Crafting UI"""

import pygame
from pygame.locals import *
from OpenGL.GL import *
import math
from constants import *
from crafting import find_recipe


class InventorySlot:
    """A single inventory slot holding an item and count."""
    __slots__ = ('item', 'count')

    def __init__(self, item=AIR, count=0):
        self.item = item
        self.count = count

    def is_empty(self):
        return self.item == AIR or self.count <= 0

    def clear(self):
        self.item = AIR
        self.count = 0

    def set(self, item, count):
        self.item = item
        self.count = count

    def add(self, item, count=1):
        if self.is_empty():
            self.item = item
            self.count = count
            return 0
        if self.item == item:
            self.count += count
            return 0
        return count  # Couldn't add

    def remove(self, count=1):
        if self.count <= count:
            item = self.item
            total = self.count
            self.clear()
            return item, total
        else:
            self.count -= count
            return self.item, count


class Inventory:
    """Player inventory with hotbar, main inventory, crafting grid, and armor."""
    HOTBAR_SIZE = 9
    MAIN_ROWS = 3
    MAIN_COLS = 9
    CRAFT_SIZE = 3

    def __init__(self, creative=True):
        self.hotbar = [InventorySlot() for _ in range(self.HOTBAR_SIZE)]

        self.main = [[InventorySlot() for _ in range(self.MAIN_COLS)]
                     for _ in range(self.MAIN_ROWS)]

        self.craft_grid = [[InventorySlot() for _ in range(self.CRAFT_SIZE)]
                           for _ in range(self.CRAFT_SIZE)]

        self.craft_output = InventorySlot()

        self.held = InventorySlot()

        if creative:
            default_items = [GRASS, DIRT, STONE, WOOD, PLANKS, COBBLESTONE, SAND, GLASS, BRICK]
            for i, item in enumerate(default_items):
                self.hotbar[i].set(item, 64)

    def get_hotbar_item(self):
        """Get the currently selected hotbar item."""
        # This is handled by selected_slot in Game
        return self.hotbar

    def add_item(self, item, count=1):
        """Add item to inventory. Returns leftover count."""
        remaining = count

        # Try hotbar first
        for slot in self.hotbar:
            if remaining <= 0:
                break
            if slot.item == item and slot.count < 64:
                can_add = min(remaining, 64 - slot.count)
                slot.count += can_add
                remaining -= can_add

        # Then main inventory
        for row in self.main:
            for slot in row:
                if remaining <= 0:
                    break
                if slot.item == item and slot.count < 64:
                    can_add = min(remaining, 64 - slot.count)
                    slot.count += can_add
                    remaining -= can_add

        # Try empty slots
        if remaining > 0:
            for slot in self.hotbar:
                if remaining <= 0:
                    break
                if slot.is_empty():
                    slot.set(item, min(remaining, 64))
                    remaining -= min(remaining, 64)

        if remaining > 0:
            for row in self.main:
                for slot in row:
                    if remaining <= 0:
                        break
                    if slot.is_empty():
                        slot.set(item, min(remaining, 64))
                        remaining -= min(remaining, 64)

        return remaining

    def remove_item(self, item, count=1):
        """Remove item from inventory. Returns True if successful."""
        remaining = count

        # Check hotbar
        for slot in self.hotbar:
            if remaining <= 0:
                break
            if slot.item == item:
                take = min(remaining, slot.count)
                slot.count -= take
                remaining -= take
                if slot.count <= 0:
                    slot.clear()

        # Check main
        for row in self.main:
            for slot in row:
                if remaining <= 0:
                    break
                if slot.item == item:
                    take = min(remaining, slot.count)
                    slot.count -= take
                    remaining -= take
                    if slot.count <= 0:
                        slot.clear()

        return remaining <= 0

    def has_item(self, item, count=1):
        """Check if inventory has enough of an item."""
        total = 0
        for slot in self.hotbar:
            if slot.item == item:
                total += slot.count
        for row in self.main:
            for slot in row:
                if slot.item == item:
                    total += slot.count
        return total >= count

    def count_item(self, item):
        """Count total of an item in inventory."""
        total = 0
        for slot in self.hotbar:
            if slot.item == item:
                total += slot.count
        for row in self.main:
            for slot in row:
                if slot.item == item:
                    total += slot.count
        return total

    def update_craft(self):
        """Check crafting grid and update output."""
        grid = [[self.craft_grid[y][x].item for x in range(self.CRAFT_SIZE)]
                for y in range(self.CRAFT_SIZE)]
        result, count = find_recipe(grid, self.CRAFT_SIZE)
        if result != AIR:
            self.craft_output.set(result, count)
        else:
            self.craft_output.clear()

    def craft(self):
        """Craft the output item. Returns True if successful."""
        if self.craft_output.is_empty():
            return False

        result_item = self.craft_output.item
        result_count = self.craft_output.count

        # Check if we can add the result
        # (simplified - just try to add)
        leftover = self.add_item(result_item, result_count)
        if leftover > 0:
            return False  # Inventory full

        # Consume crafting ingredients
        for row in self.craft_grid:
            for slot in row:
                if not slot.is_empty():
                    slot.count -= 1
                    if slot.count <= 0:
                        slot.clear()

        # Recalculate output
        self.update_craft()
        return True

    def get_all_slots(self):
        """Get all slots for rendering."""
        slots = []
        # Hotbar
        for slot in self.hotbar:
            slots.append(slot)
        # Main
        for row in self.main:
            for slot in row:
                slots.append(slot)
        return slots


class CraftingUI:
    """Crafting interface overlay."""

    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.open = False
        self.hovered_slot = None
        self.slot_rects = {}  # For click detection

    def toggle(self):
        self.open = not self.open

    def handle_click(self, mx, my, inventory, button=1):
        """Handle mouse click on crafting UI."""
        my = self.screen_h - my  # Convert to OpenGL coords

        # Check all slot rects
        for key, (sx, sy, sw, sh) in self.slot_rects.items():
            if sx <= mx <= sx + sw and sy <= my <= sy + sh:
                self._handle_slot_click(key, inventory, button)
                return True
        return False

    def _handle_slot_click(self, key, inventory, button):
        """Handle clicking on a specific slot."""
        if key.startswith("craft_in_"):
            # Crafting input grid
            idx = int(key.split("_")[2])
            y, x = divmod(idx, 3)
            slot = inventory.craft_grid[y][x]

            if button == 1:  # Left click
                if inventory.held.is_empty():
                    # Pick up from slot
                    if not slot.is_empty():
                        inventory.held.item = slot.item
                        inventory.held.count = slot.count
                        slot.clear()
                else:
                    # Place into slot
                    if slot.is_empty():
                        slot.item = inventory.held.item
                        slot.count = inventory.held.count
                        inventory.held.clear()
                    elif slot.item == inventory.held.item:
                        # Stack
                        can_add = min(inventory.held.count, 64 - slot.count)
                        slot.count += can_add
                        inventory.held.count -= can_add
                        if inventory.held.count <= 0:
                            inventory.held.clear()

                inventory.update_craft()

        elif key == "craft_out":
            # Crafting output
            slot = inventory.craft_output
            if not slot.is_empty() and inventory.held.is_empty():
                inventory.craft()
                inventory.held.item = slot.item
                inventory.held.count = slot.count
                inventory.update_craft()

        elif key.startswith("inv_"):
            # Main inventory / hotbar
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
                        # Swap
                        temp_item, temp_count = slot.item, slot.count
                        slot.item = inventory.held.item
                        slot.count = inventory.held.count
                        inventory.held.item = temp_item
                        inventory.held.count = temp_count

    def draw(self, inventory):
        """Draw the crafting UI overlay."""
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

        # ─── Crafting Grid Panel ──────────────────────────────────────────
        panel_x = cx - 80
        panel_y = cy + 30

        # Panel background
        glColor4f(0.15, 0.15, 0.2, 0.9)
        self._draw_rect(panel_x - 15, panel_y - 15, 160, 160)

        # Crafting grid label
        glColor3f(0.8, 0.8, 0.8)
        self._draw_small_text(panel_x, panel_y + 130, "Crafting")

        # 3x3 crafting grid
        for y in range(3):
            for x in range(3):
                sx = panel_x + x * (slot_size + gap)
                sy = panel_y + (2 - y) * (slot_size + gap)
                slot = inventory.craft_grid[y][x]
                self._draw_slot(sx, sy, slot_size, slot)
                self.slot_rects[f"craft_in_{y * 3 + x}"] = (sx, sy, slot_size, slot_size)

        # Arrow
        arrow_x = panel_x + 3 * (slot_size + gap) + 10
        arrow_y = panel_y + slot_size + gap
        glColor3f(0.7, 0.7, 0.7)
        self._draw_arrow(arrow_x, arrow_y + slot_size // 2, 20, 12)

        # Output slot
        out_x = arrow_x + 30
        out_y = arrow_y
        output = inventory.craft_output
        self._draw_slot(out_x, out_y, slot_size, output, highlight=True)
        self.slot_rects["craft_out"] = (out_x, out_y, slot_size, slot_size)

        # ─── Inventory Panel ──────────────────────────────────────────────
        inv_panel_y = cy - 160

        # Main inventory (3 rows x 9 cols)
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
                sy = inv_y = inv_panel_y + (2 - row) * (slot_size + gap)
                slot = inventory.main[row][col]
                self._draw_slot(sx, sy, slot_size, slot)
                self.slot_rects[f"inv_main_{row * 9 + col}"] = (sx, sy, slot_size, slot_size)

        # Hotbar
        hotbar_y = inv_panel_y - slot_size - gap - 15
        for i in range(9):
            sx = inv_x + i * (slot_size + gap)
            slot = inventory.hotbar[i]
            self._draw_slot(sx, hotbar_y, slot_size, slot)
            self.slot_rects[f"inv_hotbar_{i}"] = (sx, hotbar_y, slot_size, slot_size)

        # ─── Held Item ────────────────────────────────────────────────────
        if not inventory.held.is_empty():
            mx, my = pygame.mouse.get_pos()
            my = self.screen_h - my
            self._draw_slot(mx - slot_size // 2, my - slot_size // 2,
                          slot_size, inventory.held)

        # ─── Recipe hints ─────────────────────────────────────────────────
        hint_y = cy - 220
        glColor4f(0.6, 0.6, 0.6, 0.7)
        self._draw_small_text(cx - 100, hint_y, "Click to move items")
        self._draw_small_text(cx - 80, hint_y - 15, "ESC to close")

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_FOG)

    def _draw_slot(self, x, y, size, slot, highlight=False):
        """Draw a single inventory slot."""
        # Background
        if highlight:
            glColor4f(0.25, 0.35, 0.2, 0.9)
        else:
            glColor4f(0.12, 0.12, 0.15, 0.9)
        self._draw_rect(x, y, size, size)

        # Border
        glColor4f(0.4, 0.4, 0.45, 0.8)
        glLineWidth(1)
        glBegin(GL_LINE_LOOP)
        glVertex2f(x, y)
        glVertex2f(x + size, y)
        glVertex2f(x + size, y + size)
        glVertex2f(x, y + size)
        glEnd()

        # Item
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

                # Top highlight
                top_color = colors[0]
                glColor3f(top_color[0] * 0.8, top_color[1] * 0.8, top_color[2] * 0.8)
                glBegin(GL_QUADS)
                glVertex2f(x + pad, y + size - pad - 6)
                glVertex2f(x + size - pad, y + size - pad - 6)
                glVertex2f(x + size - pad, y + size - pad)
                glVertex2f(x + pad, y + size - pad)
                glEnd()

            # Count
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
        """Draw a right-pointing arrow."""
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
            'C': [(8,0,0,0),(0,0,0,10),(0,10,8,10)],
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
        """Draw a small number."""
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

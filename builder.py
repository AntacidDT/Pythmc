"""Pythmc - Structure Builder Tool

A flat world mode for building structures.
Export builds as JSON to import into the main game.

Controls:
  WASD - Move | Space - Jump | Shift - Descend
  Mouse - Look | LClick - Break | RClick - Place
  1-9 - Select Block | Scroll - Cycle Blocks
  F - Toggle Fly | Ctrl+S - Save Structure | Ctrl+L - Load Structure
  F5 - Toggle Grid | Esc - Menu
"""

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import json
import os
import math
import time
from constants import *
from text_renderer import text_renderer


# Builder world size
BUILDER_SIZE = 48  # 48x48 flat world
BUILDER_HEIGHT = 32
GRID_COLOR = (0.3, 0.3, 0.3, 0.3)


class BuilderWorld:
    """Simple flat world for building."""
    
    def __init__(self):
        self.blocks = np.zeros((BUILDER_SIZE, BUILDER_HEIGHT, BUILDER_SIZE), dtype=np.uint8)
        self.display_list = None
        self.mesh_dirty = True
        self._generate_flat()
    
    def _generate_flat(self):
        """Generate a flat world with bedrock and grass."""
        for x in range(BUILDER_SIZE):
            for z in range(BUILDER_SIZE):
                self.blocks[x, 0, z] = BEDROCK
                self.blocks[x, 1, z] = DIRT
                self.blocks[x, 2, z] = GRASS
    
    def get_block(self, x, y, z):
        if 0 <= x < BUILDER_SIZE and 0 <= y < BUILDER_HEIGHT and 0 <= z < BUILDER_SIZE:
            return self.blocks[x, y, z]
        return AIR
    
    def set_block(self, x, y, z, block_type):
        if 0 <= x < BUILDER_SIZE and 0 <= y < BUILDER_HEIGHT and 0 <= z < BUILDER_SIZE:
            if y > 1:  # Don't replace bedrock/dirt base
                self.blocks[x, y, z] = block_type
                self.mesh_dirty = True
    
    def build_mesh(self):
        """Build display list for rendering."""
        if self.display_list is None:
            self.display_list = glGenLists(1)
        
        glNewList(self.display_list, GL_COMPILE)
        glBegin(GL_QUADS)
        
        for x in range(BUILDER_SIZE):
            for y in range(BUILDER_HEIGHT):
                for z in range(BUILDER_SIZE):
                    block = self.blocks[x, y, z]
                    if block == AIR:
                        continue
                    
                    colors = BLOCK_COLORS.get(block)
                    if not colors:
                        continue
                    
                    # Check each face
                    for face_idx, (dx, dy, dz) in enumerate(FACE_DIRS):
                        nx, ny, nz = x + dx, y + dy, z + dz
                        neighbor = self.get_block(nx, ny, nz)
                        if neighbor != AIR:
                            continue
                        
                        # Get color for face
                        if dy == 1:
                            color = colors[0]
                        elif dy == -1:
                            color = colors[2]
                        else:
                            color = colors[1]
                        
                        # Shade
                        shade = 1.0
                        if dx == -1 or dz == -1: shade = 0.82
                        elif dx == 1 or dz == 1: shade = 0.68
                        elif dy == -1: shade = 0.50
                        
                        glColor3f(color[0]*shade, color[1]*shade, color[2]*shade)
                        for vx, vy, vz in FACE_VERTS[face_idx]:
                            glVertex3f(x + vx, y + vy, z + vz)
        
        glEnd()
        glEndList()
        self.mesh_dirty = False
    
    def draw(self):
        if self.mesh_dirty:
            self.build_mesh()
        if self.display_list:
            glCallList(self.display_list)
    
    def draw_grid(self):
        """Draw reference grid on ground."""
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(*GRID_COLOR)
        glLineWidth(1)
        glBegin(GL_LINES)
        for i in range(BUILDER_SIZE + 1):
            glVertex3f(i, 2.01, 0)
            glVertex3f(i, 2.01, BUILDER_SIZE)
            glVertex3f(0, 2.01, i)
            glVertex3f(BUILDER_SIZE, 2.01, i)
        glEnd()
        # Origin marker
        glColor4f(1, 0, 0, 0.5)
        glLineWidth(3)
        glBegin(GL_LINES)
        glVertex3f(0, 2.01, 0); glVertex3f(5, 2.01, 0)
        glColor4f(0, 1, 0, 0.5)
        glVertex3f(0, 2.01, 0); glVertex3f(0, 5, 0)
        glColor4f(0, 0, 1, 0.5)
        glVertex3f(0, 2.01, 0); glVertex3f(0, 2.01, 5)
        glEnd()
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)
    
    def export_structure(self, name="structure"):
        """Export placed blocks as JSON."""
        blocks = []
        for x in range(BUILDER_SIZE):
            for y in range(BUILDER_HEIGHT):
                for z in range(BUILDER_SIZE):
                    block = self.blocks[x, y, z]
                    if block not in (AIR, BEDROCK, DIRT, GRASS):  # Skip base
                        blocks.append({"x": x, "y": y - 2, "z": z, "type": int(block)})
        
        if not blocks:
            return None
        
        # Find bounding box
        xs = [b["x"] for b in blocks]
        ys = [b["y"] for b in blocks]
        zs = [b["z"] for b in blocks]
        
        structure = {
            "name": name,
            "blocks": blocks,
            "bounds": {
                "min_x": min(xs), "max_x": max(xs),
                "min_y": min(ys), "max_y": max(ys),
                "min_z": min(zs), "max_z": max(zs),
            },
            "size": {
                "width": max(xs) - min(xs) + 1,
                "height": max(ys) - min(ys) + 1,
                "depth": max(zs) - min(zs) + 1,
            },
            "block_count": len(blocks),
        }
        
        return structure
    
    def import_structure(self, structure):
        """Import a structure from JSON."""
        if not structure or "blocks" not in structure:
            return False
        
        # Clear existing blocks (except base)
        for x in range(BUILDER_SIZE):
            for y in range(3, BUILDER_HEIGHT):
                for z in range(BUILDER_SIZE):
                    self.blocks[x, y, z] = AIR
        
        # Place blocks
        for b in structure["blocks"]:
            x, y, z = b["x"], b["y"] + 2, b["z"]  # Offset up for base
            block_type = b["type"]
            if 0 <= x < BUILDER_SIZE and 0 <= y < BUILDER_HEIGHT and 0 <= z < BUILDER_SIZE:
                self.blocks[x, y, z] = block_type
        
        self.mesh_dirty = True
        return True
    
    def cleanup(self):
        if self.display_list:
            glDeleteLists(self.display_list, 1)


class BuilderPlayer:
    """Simple player for builder mode."""
    
    def __init__(self):
        self.pos = np.array([BUILDER_SIZE / 2.0, 8.0, BUILDER_SIZE / 2.0])
        self.velocity = np.array([0.0, 0.0, 0.0])
        self.yaw = 45.0
        self.pitch = -20.0
        self.on_ground = False
        self.flying = True
        self.selected_block = STONE
        self.hotbar = [STONE, COBBLESTONE, WOOD, PLANKS, GLASS, BRICK, SAND, DIRT, GRASS]
        self.selected_slot = 0
        self.show_grid = True
    
    def get_forward(self):
        ry = math.radians(self.yaw)
        rp = math.radians(self.pitch)
        return np.array([-math.sin(ry)*math.cos(rp), -math.sin(rp), -math.cos(ry)*math.cos(rp)])
    
    def get_eye_pos(self):
        return self.pos + np.array([0, PLAYER_HEIGHT, 0])


class StructureBuilder:
    """The main structure builder application."""
    
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.running = False
        self.world = BuilderWorld()
        self.player = BuilderPlayer()
        self.keys = {}
        self.mouse_captured = False
        self.clock = None
        self.last_break = 0
        self.last_place = 0
        self.message = ""
        self.message_timer = 0
        
        # Create structures directory
        self.structures_dir = os.path.join(os.path.dirname(__file__), "structures_json")
        os.makedirs(self.structures_dir, exist_ok=True)
    
    def _show_message(self, text, duration=3.0):
        self.message = text
        self.message_timer = duration
    
    def _center_mouse(self):
        pygame.mouse.set_pos(self.screen_w // 2, self.screen_h // 2)
    
    def _init_gl(self):
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        glDisable(GL_CULL_FACE)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glShadeModel(GL_SMOOTH)
        glClearColor(0.5, 0.7, 1.0, 1.0)
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.4, 0.4, 0.45, 1.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.9, 0.9, 0.85, 1.0))
        glLightfv(GL_LIGHT0, GL_POSITION, (0.5, 1.0, 0.3, 0.0))
        glEnable(GL_FOG)
        glFogi(GL_FOG_MODE, GL_LINEAR)
        glFogfv(GL_FOG_COLOR, (0.5, 0.7, 1.0, 1.0))
        glFogf(GL_FOG_START, 40)
        glFogf(GL_FOG_END, 80)
    
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
            
            elif event.type == KEYDOWN:
                self.keys[event.key] = True
                
                if event.key == K_ESCAPE:
                    if self.mouse_captured:
                        self.mouse_captured = False
                        pygame.mouse.set_visible(True)
                        pygame.event.set_grab(False)
                    else:
                        self.running = False
                
                elif event.key == K_f:
                    self.player.flying = not self.player.flying
                
                elif K_1 <= event.key <= K_9:
                    self.player.selected_slot = event.key - K_1
                    self.player.selected_block = self.player.hotbar[self.player.selected_slot]
                
                elif event.key == K_F5:
                    self.player.show_grid = not self.player.show_grid
                
                elif event.key == K_s and (pygame.key.get_mods() & KMOD_CTRL):
                    self._save_structure()
                
                elif event.key == K_l and (pygame.key.get_mods() & KMOD_CTRL):
                    self._load_structure_dialog()
            
            elif event.type == KEYUP:
                self.keys[event.key] = False
            
            elif event.type == MOUSEBUTTONDOWN:
                if not self.mouse_captured:
                    self.mouse_captured = True
                    pygame.mouse.set_visible(False)
                    pygame.event.set_grab(True)
                    self._center_mouse()
                    return
                
                if event.button == 1:
                    self._break_block()
                elif event.button == 3:
                    self._place_block()
                elif event.button == 4:
                    self.player.selected_slot = (self.player.selected_slot - 1) % 9
                    self.player.selected_block = self.player.hotbar[self.player.selected_slot]
                elif event.button == 5:
                    self.player.selected_slot = (self.player.selected_slot + 1) % 9
                    self.player.selected_block = self.player.hotbar[self.player.selected_slot]
            
            elif event.type == MOUSEMOTION and self.mouse_captured:
                dx, dy = event.rel
                self.player.yaw -= dx * 0.15
                self.player.pitch += dy * 0.15
                self.player.pitch = max(-89, min(89, self.player.pitch))
                self._center_mouse()
    
    def _break_block(self):
        now = time.time()
        if now - self.last_break < 0.15:
            return
        
        eye = self.player.get_eye_pos()
        direction = self.player.get_forward()
        hit = self._raycast(eye, direction)
        if hit:
            x, y, z = hit
            self.world.set_block(x, y, z, AIR)
            self.last_break = now
    
    def _place_block(self):
        now = time.time()
        if now - self.last_place < 0.15:
            return
        
        eye = self.player.get_eye_pos()
        direction = self.player.get_forward()
        hit, place_pos = self._raycast_place(eye, direction)
        if hit and place_pos:
            px, py, pz = place_pos
            if py > 1:  # Don't place on bedrock
                self.world.set_block(px, py, pz, self.player.selected_block)
                self.last_place = now
    
    def _raycast(self, origin, direction, max_dist=8.0):
        """Simple raycast for block breaking."""
        ox, oy, oz = origin
        dx, dy, dz = direction
        if abs(dx) < 1e-10 and abs(dy) < 1e-10 and abs(dz) < 1e-10:
            return None
        
        x, y, z = int(math.floor(ox)), int(math.floor(oy)), int(math.floor(oz))
        step_x = 1 if dx > 0 else -1
        step_y = 1 if dy > 0 else -1
        step_z = 1 if dz > 0 else -1
        
        t_max_x = ((x + (1 if dx > 0 else 0)) - ox) / dx if dx != 0 else float('inf')
        t_max_y = ((y + (1 if dy > 0 else 0)) - oy) / dy if dy != 0 else float('inf')
        t_max_z = ((z + (1 if dz > 0 else 0)) - oz) / dz if dz != 0 else float('inf')
        
        t_delta_x = abs(1.0 / dx) if dx != 0 else float('inf')
        t_delta_y = abs(1.0 / dy) if dy != 0 else float('inf')
        t_delta_z = abs(1.0 / dz) if dz != 0 else float('inf')
        
        dist = 0.0
        for _ in range(100):
            if dist >= max_dist:
                break
            block = self.world.get_block(x, y, z)
            if block != AIR:
                return (x, y, z)
            if t_max_x < t_max_y:
                if t_max_x < t_max_z:
                    x += step_x; dist = t_max_x; t_max_x += t_delta_x
                else:
                    z += step_z; dist = t_max_z; t_max_z += t_delta_z
            else:
                if t_max_y < t_max_z:
                    y += step_y; dist = t_max_y; t_max_y += t_delta_y
                else:
                    z += step_z; dist = t_max_z; t_max_z += t_delta_z
        return None
    
    def _raycast_place(self, origin, direction, max_dist=8.0):
        """Raycast that returns both hit and placement position."""
        ox, oy, oz = origin
        dx, dy, dz = direction
        if abs(dx) < 1e-10 and abs(dy) < 1e-10 and abs(dz) < 1e-10:
            return None, None
        
        x, y, z = int(math.floor(ox)), int(math.floor(oy)), int(math.floor(oz))
        step_x = 1 if dx > 0 else -1
        step_y = 1 if dy > 0 else -1
        step_z = 1 if dz > 0 else -1
        
        t_max_x = ((x + (1 if dx > 0 else 0)) - ox) / dx if dx != 0 else float('inf')
        t_max_y = ((y + (1 if dy > 0 else 0)) - oy) / dy if dy != 0 else float('inf')
        t_max_z = ((z + (1 if dz > 0 else 0)) - oz) / dz if dz != 0 else float('inf')
        
        t_delta_x = abs(1.0 / dx) if dx != 0 else float('inf')
        t_delta_y = abs(1.0 / dy) if dy != 0 else float('inf')
        t_delta_z = abs(1.0 / dz) if dz != 0 else float('inf')
        
        last_x, last_y, last_z = x, y, z
        dist = 0.0
        for _ in range(100):
            if dist >= max_dist:
                break
            block = self.world.get_block(x, y, z)
            if block != AIR:
                return (x, y, z), (last_x, last_y, last_z)
            last_x, last_y, last_z = x, y, z
            if t_max_x < t_max_y:
                if t_max_x < t_max_z:
                    x += step_x; dist = t_max_x; t_max_x += t_delta_x
                else:
                    z += step_z; dist = t_max_z; t_max_z += t_delta_z
            else:
                if t_max_y < t_max_z:
                    y += step_y; dist = t_max_y; t_max_y += t_delta_y
                else:
                    z += step_z; dist = t_max_z; t_max_z += t_delta_z
        return None, None
    
    def _save_structure(self):
        """Save current build as JSON."""
        structure = self.world.export_structure("custom_structure")
        if not structure:
            self._show_message("Nothing to save! Place some blocks first.")
            return
        
        filename = f"structure_{int(time.time())}.json"
        filepath = os.path.join(self.structures_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(structure, f, indent=2)
        
        self._show_message(f"Saved: {filename} ({structure['block_count']} blocks)")
        print(f"Structure saved to: {filepath}")
        print(f"Size: {structure['size']}")
        print(f"Blocks: {structure['block_count']}")
    
    def _load_structure_dialog(self):
        """Load a structure from JSON file."""
        if not os.path.exists(self.structures_dir):
            self._show_message("No structures folder found!")
            return
        
        files = [f for f in os.listdir(self.structures_dir) if f.endswith('.json')]
        if not files:
            self._show_message("No structures found! Build something and save first.")
            return
        
        # Load the most recent file
        files.sort(reverse=True)
        filepath = os.path.join(self.structures_dir, files[0])
        
        try:
            with open(filepath, 'r') as f:
                structure = json.load(f)
            
            if self.world.import_structure(structure):
                self._show_message(f"Loaded: {files[0]} ({structure.get('block_count', 0)} blocks)")
            else:
                self._show_message("Failed to load structure!")
        except Exception as e:
            self._show_message(f"Error: {str(e)}")
    
    def _update(self, dt):
        # Player movement
        forward = self.player.get_forward()
        forward[1] = 0
        n = np.linalg.norm(forward)
        if n > 0: forward /= n
        
        right = np.array([-math.cos(math.radians(self.player.yaw)), 0, math.sin(math.radians(self.player.yaw))])
        
        move = np.array([0.0, 0.0, 0.0])
        speed = FLY_SPEED if self.player.flying else WALK_SPEED
        
        if self.keys.get(K_w): move += forward
        if self.keys.get(K_s): move -= forward
        if self.keys.get(K_a): move += right
        if self.keys.get(K_d): move -= right
        
        if np.linalg.norm(move) > 0:
            move = move / np.linalg.norm(move) * speed
        
        self.player.velocity[0] = move[0]
        self.player.velocity[2] = move[2]
        
        if self.player.flying:
            if self.keys.get(K_SPACE): self.player.velocity[1] = speed
            elif self.keys.get(K_LSHIFT): self.player.velocity[1] = -speed
            else: self.player.velocity[1] = 0
        else:
            if self.keys.get(K_SPACE) and self.player.on_ground:
                self.player.velocity[1] = JUMP_SPEED
                self.player.on_ground = False
            self.player.velocity[1] += GRAVITY * dt
        
        # Simple collision
        new_pos = self.player.pos + self.player.velocity * dt
        # Clamp to world bounds
        new_pos[0] = max(0, min(BUILDER_SIZE, new_pos[0]))
        new_pos[2] = max(0, min(BUILDER_SIZE, new_pos[2]))
        # Ground collision
        bx, bz = int(math.floor(new_pos[0])), int(math.floor(new_pos[2]))
        ground_y = 3.0
        for y in range(BUILDER_HEIGHT - 1, -1, -1):
            if self.world.get_block(bx, y, bz) != AIR:
                ground_y = y + 1
                break
        if new_pos[1] < ground_y:
            new_pos[1] = ground_y
            self.player.velocity[1] = 0
            self.player.on_ground = True
        
        self.player.pos = new_pos
        
        # Message timer
        if self.message_timer > 0:
            self.message_timer -= dt
    
    def _render(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Camera
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(70, self.screen_w / self.screen_h, 0.1, 200.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        eye = self.player.get_eye_pos()
        look = eye + self.player.get_forward()
        gluLookAt(eye[0], eye[1], eye[2], look[0], look[1], look[2], 0, 1, 0)
        
        # World
        self.world.draw()
        
        # Grid
        if self.player.show_grid:
            self.world.draw_grid()
        
        # Target block highlight
        self._draw_target()
        
        # HUD
        self._draw_hud()
    
    def _draw_target(self):
        eye = self.player.get_eye_pos()
        hit = self._raycast(eye, self.player.get_forward())
        if not hit:
            return
        
        x, y, z = hit
        glDisable(GL_LIGHTING)
        glDisable(GL_FOG)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glLineWidth(2)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glColor4f(0, 0, 0, 0.5)
        for fi in range(6):
            glBegin(GL_QUADS)
            for vx, vy, vz in FACE_VERTS[fi]:
                glVertex3f(x + vx, y + vy, z + vz)
            glEnd()
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glDisable(GL_BLEND)
        glEnable(GL_FOG)
        glEnable(GL_LIGHTING)
    
    def _draw_hud(self):
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glDisable(GL_FOG)
        
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.screen_w, 0, self.screen_h, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        # Crosshair
        cx, cy = self.screen_w // 2, self.screen_h // 2
        glColor3f(1, 1, 1)
        glLineWidth(2)
        glBegin(GL_LINES)
        glVertex2f(cx - 10, cy); glVertex2f(cx + 10, cy)
        glVertex2f(cx, cy - 10); glVertex2f(cx, cy + 10)
        glEnd()
        
        # Hotbar
        bar_w = 9 * 44
        sx = (self.screen_w - bar_w) // 2
        sy = 10
        for i in range(9):
            bx = sx + i * 45
            if i == self.player.selected_slot:
                glColor3f(1, 1, 1)
                glLineWidth(3)
            else:
                glColor3f(0.35, 0.35, 0.35)
                glLineWidth(1)
            glBegin(GL_LINE_LOOP)
            glVertex2f(bx, sy); glVertex2f(bx + 40, sy)
            glVertex2f(bx + 40, sy + 40); glVertex2f(bx, sy + 40)
            glEnd()
            block = self.player.hotbar[i]
            if block in BLOCK_COLORS:
                c = BLOCK_COLORS[block][1]
                glColor3f(c[0], c[1], c[2])
                glBegin(GL_QUADS)
                glVertex2f(bx + 3, sy + 3); glVertex2f(bx + 37, sy + 3)
                glVertex2f(bx + 37, sy + 37); glVertex2f(bx + 3, sy + 37)
                glEnd()
        
        # Info text
        text_renderer.draw_text(10, self.screen_h - 25, 
                               f"Builder Mode | Pos: {self.player.pos[0]:.0f},{self.player.pos[1]:.0f},{self.player.pos[2]:.0f}",
                               "small", (1, 1, 1))
        text_renderer.draw_text(10, self.screen_h - 45,
                               "Ctrl+S: Save | Ctrl+L: Load | F5: Grid | F: Fly",
                               "small", (0.7, 0.7, 0.7))
        
        # Selected block name
        block_name = BLOCK_NAMES.get(self.player.selected_block, "")
        text_renderer.draw_text(sx, sy + 45, block_name, "medium", (1, 1, 1))
        
        # Message
        if self.message_timer > 0:
            alpha = min(1.0, self.message_timer)
            text_renderer.draw_text_centered(self.screen_w // 2, self.screen_h - 80, 
                                            self.message, "medium", (1, 1, 0.5))
        
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_FOG)
    
    def run(self):
        """Run the structure builder."""
        pygame.init()
        pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)
        pygame.display.gl_set_attribute(pygame.GL_DOUBLEBUFFER, 1)
        screen = pygame.display.set_mode((self.screen_w, self.screen_h), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Pythmc - Structure Builder")
        
        text_renderer.init()
        self._init_gl()
        self.clock = pygame.time.Clock()
        self.running = True
        
        print("=" * 50)
        print("  Pythmc - Structure Builder")
        print("=" * 50)
        print("  Build structures and export as JSON!")
        print("  Ctrl+S - Save structure")
        print("  Ctrl+L - Load last structure")
        print("=" * 50)
        
        dt = 0
        while self.running:
            self._handle_events()
            if self.running:
                self._update(dt)
                self._render()
                pygame.display.flip()
                dt = self.clock.tick(60) / 1000.0
        
        self.world.cleanup()
        pygame.quit()
        return "menu"


if __name__ == "__main__":
    builder = StructureBuilder(1280, 720)
    builder.run()

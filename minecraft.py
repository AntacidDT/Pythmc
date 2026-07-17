#!/usr/bin/env python3
"""
MC by Mimo - Minecraft Clone from scratch
Controls:
  WASD - Move | Space - Jump | Shift - Descend (fly) | Ctrl - Sprint
  Mouse Look | Left Click - Break Block | Right Click - Place Block
  1-9 - Select Hotbar Slot | F - Toggle Fly | T - Creative/Survival
  G - Freeze Time | F11 - Fullscreen | Esc - Release Mouse | R - Respawn
"""

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
from noise import pnoise2
import math
import time
import random

# ─── Constants ───────────────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 1280, 720
FPS = 60
CHUNK_SIZE = 16
CHUNK_HEIGHT = 64
RENDER_DISTANCE = 4
GRAVITY = -25.0
JUMP_SPEED = 9.0
PLAYER_HEIGHT = 1.62
PLAYER_WIDTH = 0.3
WALK_SPEED = 4.3
SPRINT_SPEED = 6.5
SWIM_SPEED = 3.0
FLY_SPEED = 12.0
BREAK_COOLDOWN = 0.2
PLACE_COOLDOWN = 0.2
MAX_REACH = 6.0
WATER_DRAG = 0.6

# ─── Block Types ─────────────────────────────────────────────────────────────
AIR = 0
GRASS = 1
DIRT = 2
STONE = 3
WOOD = 4
LEAVES = 5
SAND = 6
WATER = 7
COBBLESTONE = 8
PLANKS = 9
BEDROCK = 10
COAL_ORE = 11
IRON_ORE = 12
GLASS = 13
BRICK = 14
SNOW = 15
CACTUS = 16
TORCH = 17
GRAVEL = 18
GOLD_ORE = 19

BLOCK_NAMES = {
    AIR: "Air", GRASS: "Grass", DIRT: "Dirt", STONE: "Stone",
    WOOD: "Wood", LEAVES: "Leaves", SAND: "Sand", WATER: "Water",
    COBBLESTONE: "Cobble", PLANKS: "Planks", BEDROCK: "Bedrock",
    COAL_ORE: "Coal", IRON_ORE: "Iron", GLASS: "Glass", BRICK: "Brick",
    SNOW: "Snow", CACTUS: "Cactus", TORCH: "Torch", GRAVEL: "Gravel", GOLD_ORE: "Gold"
}

BLOCK_COLORS = {
    GRASS:       ((0.30, 0.78, 0.20), (0.55, 0.35, 0.15), (0.40, 0.26, 0.13)),
    DIRT:        ((0.55, 0.35, 0.15), (0.55, 0.35, 0.15), (0.55, 0.35, 0.15)),
    STONE:       ((0.55, 0.55, 0.55), (0.50, 0.50, 0.50), (0.45, 0.45, 0.45)),
    WOOD:        ((0.55, 0.42, 0.22), (0.40, 0.28, 0.12), (0.55, 0.42, 0.22)),
    LEAVES:      ((0.18, 0.58, 0.12), (0.15, 0.52, 0.10), (0.12, 0.48, 0.08)),
    SAND:        ((0.88, 0.82, 0.58), (0.82, 0.78, 0.52), (0.78, 0.72, 0.48)),
    WATER:       ((0.22, 0.45, 0.85), (0.18, 0.38, 0.78), (0.15, 0.32, 0.70)),
    COBBLESTONE: ((0.48, 0.48, 0.48), (0.42, 0.42, 0.42), (0.38, 0.38, 0.38)),
    PLANKS:      ((0.72, 0.58, 0.32), (0.68, 0.52, 0.28), (0.65, 0.48, 0.25)),
    BEDROCK:     ((0.28, 0.28, 0.28), (0.22, 0.22, 0.22), (0.18, 0.18, 0.18)),
    COAL_ORE:    ((0.48, 0.48, 0.48), (0.42, 0.42, 0.42), (0.38, 0.38, 0.38)),
    IRON_ORE:    ((0.55, 0.52, 0.48), (0.58, 0.55, 0.50), (0.52, 0.48, 0.42)),
    GLASS:       ((0.82, 0.92, 0.98), (0.80, 0.90, 0.95), (0.78, 0.88, 0.92)),
    BRICK:       ((0.68, 0.32, 0.28), (0.62, 0.30, 0.25), (0.58, 0.28, 0.22)),
    SNOW:        ((0.95, 0.97, 1.00), (0.90, 0.92, 0.95), (0.85, 0.88, 0.92)),
    CACTUS:      ((0.22, 0.62, 0.18), (0.18, 0.55, 0.15), (0.15, 0.48, 0.12)),
    TORCH:       ((0.95, 0.80, 0.30), (0.90, 0.72, 0.25), (0.85, 0.65, 0.20)),
    GRAVEL:      ((0.52, 0.50, 0.48), (0.48, 0.46, 0.44), (0.44, 0.42, 0.40)),
    GOLD_ORE:    ((0.55, 0.52, 0.48), (0.60, 0.55, 0.42), (0.52, 0.48, 0.42)),
}

TRANSPARENT = {AIR, WATER, GLASS, LEAVES, TORCH}
SOLID_BLOCKS = set(range(1, 20)) - {WATER, TORCH}
FACE_DIRS = [(0,1,0),(0,-1,0),(1,0,0),(-1,0,0),(0,0,1),(0,0,-1)]

# Face vertices - CCW winding when viewed from outside the block
# Each face: 4 vertices forming a quad
FACE_VERTS = [
    # +Y (top): viewed from above, CCW
    [(0,1,0),(1,1,0),(1,1,1),(0,1,1)],
    # -Y (bottom): viewed from below, CCW
    [(0,0,1),(1,0,1),(1,0,0),(0,0,0)],
    # +X (right): viewed from +X side, CCW
    [(1,0,0),(1,1,0),(1,1,1),(1,0,1)],
    # -X (left): viewed from -X side, CCW
    [(0,0,1),(0,1,1),(0,1,0),(0,0,0)],
    # +Z (front): viewed from +Z side, CCW
    [(0,0,1),(0,1,1),(1,1,1),(1,0,1)],
    # -Z (back): viewed from -Z side, CCW
    [(1,0,0),(1,1,0),(0,1,0),(0,0,0)],
]


# ─── Particle System ─────────────────────────────────────────────────────────
class Particle:
    __slots__ = ('pos','vel','color','life','max_life')
    def __init__(self, pos, vel, color, life=1.0):
        self.pos = np.array(pos, dtype=np.float64)
        self.vel = np.array(vel, dtype=np.float64)
        self.color = color
        self.life = life
        self.max_life = life

class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit(self, pos, block_type, count=12):
        colors = BLOCK_COLORS.get(block_type)
        if not colors: return
        for _ in range(count):
            vel = [random.uniform(-3,3), random.uniform(1,6), random.uniform(-3,3)]
            c = colors[1]
            shade = random.uniform(0.7, 1.0)
            color = (c[0]*shade, c[1]*shade, c[2]*shade)
            p = Particle(
                [pos[0]+random.uniform(0,1), pos[1]+random.uniform(0,1), pos[2]+random.uniform(0,1)],
                vel, color, random.uniform(0.3, 0.8)
            )
            self.particles.append(p)

    def update(self, dt):
        alive = []
        for p in self.particles:
            p.vel[1] -= 12 * dt
            p.pos += p.vel * dt
            p.life -= dt
            if p.life > 0:
                alive.append(p)
        self.particles = alive

    def draw(self):
        if not self.particles: return
        glDisable(GL_LIGHTING)
        glDisable(GL_FOG)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glPointSize(4)
        glBegin(GL_POINTS)
        for p in self.particles:
            alpha = p.life / p.max_life
            glColor4f(p.color[0], p.color[1], p.color[2], alpha)
            glVertex3f(p.pos[0], p.pos[1], p.pos[2])
        glEnd()
        glDisable(GL_BLEND)
        glEnable(GL_FOG)
        glEnable(GL_LIGHTING)


# ─── Chunk ───────────────────────────────────────────────────────────────────
class Chunk:
    def __init__(self, cx, cz, world):
        self.cx = cx
        self.cz = cz
        self.world = world
        self.blocks = np.zeros((CHUNK_SIZE, CHUNK_HEIGHT, CHUNK_SIZE), dtype=np.uint8)
        self.mesh_dirty = True
        self.display_list = None
        self.transparent_display_list = None

    def generate_terrain(self, seed):
        world_x = self.cx * CHUNK_SIZE
        world_z = self.cz * CHUNK_SIZE
        for x in range(CHUNK_SIZE):
            for z in range(CHUNK_SIZE):
                wx = world_x + x
                wz = world_z + z
                base_height = pnoise2(wx * 0.005, wz * 0.005, octaves=6, base=seed) * 25
                detail = pnoise2(wx * 0.02, wz * 0.02, octaves=4, base=seed + 100) * 6
                height = int(base_height + detail + 30)
                height = max(1, min(CHUNK_HEIGHT - 2, height))
                temp = pnoise2(wx * 0.003, wz * 0.003, octaves=3, base=seed + 200)
                humidity = pnoise2(wx * 0.004, wz * 0.004, octaves=3, base=seed + 300)
                for y in range(height + 1):
                    if y == 0:
                        self.blocks[x, y, z] = BEDROCK
                    elif y < height - 4:
                        self.blocks[x, y, z] = STONE
                        if y < height - 6 and random.random() < 0.025:
                            self.blocks[x, y, z] = COAL_ORE
                        if y < height - 8 and random.random() < 0.015:
                            self.blocks[x, y, z] = IRON_ORE
                        if y < height - 12 and random.random() < 0.008:
                            self.blocks[x, y, z] = GOLD_ORE
                        if random.random() < 0.02:
                            self.blocks[x, y, z] = GRAVEL
                    elif y < height:
                        if temp > 0.3 and height < 22:
                            self.blocks[x, y, z] = SAND
                        else:
                            self.blocks[x, y, z] = DIRT
                    elif y == height:
                        if height < 19:
                            self.blocks[x, y, z] = SAND
                        elif temp < -0.4 and height > 35:
                            self.blocks[x, y, z] = SNOW
                        elif temp > 0.3 and humidity < -0.2 and height > 22:
                            if random.random() < 0.15:
                                self.blocks[x, y, z] = CACTUS
                            else:
                                self.blocks[x, y, z] = SAND
                        else:
                            self.blocks[x, y, z] = GRASS
                for y in range(height + 1, 19):
                    self.blocks[x, y, z] = WATER
        self._generate_trees(seed)

    def _generate_trees(self, seed):
        world_x = self.cx * CHUNK_SIZE
        world_z = self.cz * CHUNK_SIZE
        for x in range(2, CHUNK_SIZE - 2):
            for z in range(2, CHUNK_SIZE - 2):
                wx = world_x + x
                wz = world_z + z
                rng = random.Random(seed * 997 + wx * 7 + wz * 13)
                height = self._get_height(x, z)
                if height > 22 and self.blocks[x, height, z] == GRASS and rng.random() < 0.02:
                    self._place_tree(x, height + 1, z, rng)

    def _place_tree(self, x, y, z, rng):
        trunk_h = rng.randint(4, 6)
        for dy in range(trunk_h):
            if y + dy < CHUNK_HEIGHT:
                self.blocks[x, y + dy, z] = WOOD
        for dy in range(trunk_h - 2, trunk_h + 1):
            for dx in range(-2, 3):
                for dz in range(-2, 3):
                    nx, nz = x + dx, z + dz
                    if 0 <= nx < CHUNK_SIZE and 0 <= nz < CHUNK_SIZE and y + dy < CHUNK_HEIGHT:
                        if abs(dx) == 2 and abs(dz) == 2 and rng.random() < 0.35:
                            continue
                        if self.blocks[nx, y + dy, nz] == AIR:
                            self.blocks[nx, y + dy, nz] = LEAVES

    def _get_height(self, x, z):
        for y in range(CHUNK_HEIGHT - 1, -1, -1):
            if self.blocks[x, y, z] not in (AIR, WATER):
                return y
        return 0

    def get_block(self, x, y, z):
        if 0 <= x < CHUNK_SIZE and 0 <= y < CHUNK_HEIGHT and 0 <= z < CHUNK_SIZE:
            return self.blocks[x, y, z]
        return AIR

    def set_block(self, x, y, z, block_type):
        if 0 <= x < CHUNK_SIZE and 0 <= y < CHUNK_HEIGHT and 0 <= z < CHUNK_SIZE:
            self.blocks[x, y, z] = block_type
            self.mesh_dirty = True
            self._mark_neighbors_dirty(x, z)

    def _mark_neighbors_dirty(self, x, z):
        if x == 0: self.world.mark_chunk_dirty(self.cx - 1, self.cz)
        if x == CHUNK_SIZE - 1: self.world.mark_chunk_dirty(self.cx + 1, self.cz)
        if z == 0: self.world.mark_chunk_dirty(self.cx, self.cz - 1)
        if z == CHUNK_SIZE - 1: self.world.mark_chunk_dirty(self.cx, self.cz + 1)

    def build_mesh(self):
        opaque_verts = []
        transparent_verts = []
        for x in range(CHUNK_SIZE):
            for y in range(CHUNK_HEIGHT):
                for z in range(CHUNK_SIZE):
                    block = self.blocks[x, y, z]
                    if block == AIR:
                        continue
                    is_transparent = block in TRANSPARENT
                    for face_idx in range(6):
                        dx, dy, dz = FACE_DIRS[face_idx]
                        nx_pos, ny_pos, nz_pos = x + dx, y + dy, z + dz
                        neighbor = self.get_block(nx_pos, ny_pos, nz_pos)
                        if is_transparent:
                            if neighbor == block:
                                continue
                            show_face = neighbor == AIR or (neighbor in TRANSPARENT and neighbor != block)
                        else:
                            show_face = neighbor in TRANSPARENT
                        if not show_face:
                            continue
                        colors = BLOCK_COLORS.get(block)
                        if not colors:
                            continue
                        if dy == 1:
                            color = colors[0]
                        elif dy == -1:
                            color = colors[2]
                        else:
                            color = colors[1]
                        shade = 1.0
                        if dx == -1 or dz == -1: shade = 0.82
                        elif dx == 1 or dz == 1: shade = 0.68
                        elif dy == -1: shade = 0.50
                        c = (color[0]*shade, color[1]*shade, color[2]*shade)
                        wx = self.cx * CHUNK_SIZE + x
                        wz = self.cz * CHUNK_SIZE + z
                        for vx, vy, vz in FACE_VERTS[face_idx]:
                            vert = (wx + vx, y + vy, wz + vz, c[0], c[1], c[2])
                            if is_transparent:
                                transparent_verts.append(vert)
                            else:
                                opaque_verts.append(vert)
        self._build_display_list(opaque_verts, transparent_verts)
        self.mesh_dirty = False

    def _build_display_list(self, opaque_verts, transparent_verts):
        if self.display_list is None:
            self.display_list = glGenLists(1)
        glNewList(self.display_list, GL_COMPILE)
        if opaque_verts:
            glBegin(GL_QUADS)
            for v in opaque_verts:
                glColor3f(v[3], v[4], v[5])
                glVertex3f(v[0], v[1], v[2])
            glEnd()
        glEndList()

        if self.transparent_display_list is None:
            self.transparent_display_list = glGenLists(1)
        glNewList(self.transparent_display_list, GL_COMPILE)
        if transparent_verts:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glBegin(GL_QUADS)
            for v in transparent_verts:
                glColor4f(v[3], v[4], v[5], 0.55)
                glVertex3f(v[0], v[1], v[2])
            glEnd()
            glDisable(GL_BLEND)
        glEndList()

    def draw_opaque(self):
        if self.display_list is not None:
            glCallList(self.display_list)

    def draw_transparent(self):
        if self.transparent_display_list is not None:
            glCallList(self.transparent_display_list)

    def cleanup(self):
        if self.display_list is not None:
            glDeleteLists(self.display_list, 1)
            self.display_list = None
        if self.transparent_display_list is not None:
            glDeleteLists(self.transparent_display_list, 1)
            self.transparent_display_list = None


# ─── World ───────────────────────────────────────────────────────────────────
class World:
    def __init__(self, seed=None):
        self.seed = seed if seed is not None else random.randint(0, 999999)
        self.chunks = {}
        self.dirty_chunks = set()

    def get_chunk_key(self, cx, cz):
        return (cx, cz)

    def get_chunk(self, cx, cz):
        key = self.get_chunk_key(cx, cz)
        if key not in self.chunks:
            chunk = Chunk(cx, cz, self)
            chunk.generate_terrain(self.seed)
            chunk.build_mesh()
            self.chunks[key] = chunk
        return self.chunks[key]

    def mark_chunk_dirty(self, cx, cz):
        key = self.get_chunk_key(cx, cz)
        if key in self.chunks:
            self.dirty_chunks.add(key)

    def world_to_chunk(self, wx, wz):
        return (wx // CHUNK_SIZE) if wx >= 0 else (wx - CHUNK_SIZE + 1) // CHUNK_SIZE, \
               (wz // CHUNK_SIZE) if wz >= 0 else (wz - CHUNK_SIZE + 1) // CHUNK_SIZE

    def world_to_local(self, wx, wz):
        return wx % CHUNK_SIZE, wz % CHUNK_SIZE

    def get_block(self, x, y, z):
        if y < 0 or y >= CHUNK_HEIGHT:
            return AIR
        cx, cz = self.world_to_chunk(x, z)
        lx, lz = self.world_to_local(x, z)
        key = self.get_chunk_key(cx, cz)
        if key in self.chunks:
            return self.chunks[key].get_block(lx, y, lz)
        return AIR

    def set_block(self, x, y, z, block_type):
        if y < 0 or y >= CHUNK_HEIGHT:
            return
        cx, cz = self.world_to_chunk(x, z)
        lx, lz = self.world_to_local(x, z)
        chunk = self.get_chunk(cx, cz)
        chunk.set_block(lx, y, lz, block_type)

    def update(self, player_cx, player_cz):
        for key in list(self.dirty_chunks):
            if key in self.chunks:
                self.chunks[key].build_mesh()
        self.dirty_chunks.clear()
        to_remove = []
        for key in self.chunks:
            dx = abs(key[0] - player_cx)
            dz = abs(key[1] - player_cz)
            if dx > RENDER_DISTANCE + 2 or dz > RENDER_DISTANCE + 2:
                to_remove.append(key)
        for key in to_remove:
            self.chunks[key].cleanup()
            del self.chunks[key]

    def draw(self, player_cx, player_cz):
        opaque, transparent = [], []
        for dx in range(-RENDER_DISTANCE, RENDER_DISTANCE + 1):
            for dz in range(-RENDER_DISTANCE, RENDER_DISTANCE + 1):
                chunk = self.get_chunk(player_cx + dx, player_cz + dz)
                opaque.append(chunk)
                transparent.append(chunk)
        for c in opaque: c.draw_opaque()
        for c in transparent: c.draw_transparent()

    def get_height(self, x, z):
        for y in range(CHUNK_HEIGHT - 1, -1, -1):
            if self.get_block(x, y, z) not in (AIR, WATER):
                return y
        return 0


# ─── Raycasting ──────────────────────────────────────────────────────────────
def raycast(world, origin, direction, max_dist=MAX_REACH):
    ox, oy, oz = origin
    dx, dy, dz = direction
    if abs(dx) < 1e-10 and abs(dy) < 1e-10 and abs(dz) < 1e-10:
        return None, None, None
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
    for _ in range(200):
        if dist >= max_dist: break
        block = world.get_block(x, y, z)
        if block not in (AIR, WATER):
            return (x, y, z), (last_x, last_y, last_z), block
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
    return None, None, None


# ─── Cloud Renderer ──────────────────────────────────────────────────────────
class CloudRenderer:
    def __init__(self, seed):
        self.cloud_map = {}
        self.seed = seed

    def get_cloud(self, cx, cz):
        key = (cx, cz)
        if key not in self.cloud_map:
            rng = random.Random(self.seed + cx * 31 + cz * 37)
            self.cloud_map[key] = rng.random() < 0.35
        return self.cloud_map[key]

    def draw(self, player_pos, time_val):
        glDisable(GL_LIGHTING)
        glDisable(GL_FOG)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        cloud_y = 55.0
        px = int(math.floor(player_pos[0] / 12))
        pz = int(math.floor(player_pos[2] / 12))
        offset_x = (time_val * 2.0) % 12.0
        glColor4f(1.0, 1.0, 1.0, 0.65)
        glBegin(GL_QUADS)
        for dx in range(-15, 16):
            for dz in range(-15, 16):
                if self.get_cloud(px + dx, pz + dz):
                    bx = (px + dx) * 12 - offset_x
                    bz = (pz + dz) * 12
                    glVertex3f(bx, cloud_y, bz)
                    glVertex3f(bx + 10, cloud_y, bz)
                    glVertex3f(bx + 10, cloud_y, bz + 10)
                    glVertex3f(bx, cloud_y, bz + 10)
        glEnd()
        glDisable(GL_BLEND)
        glEnable(GL_FOG)
        glEnable(GL_LIGHTING)


# ─── Player ──────────────────────────────────────────────────────────────────
class Player:
    def __init__(self, world):
        self.world = world
        self._spawn()

    def _spawn(self):
        spawn_x, spawn_z = 8, 8
        pcx, pcz = self.world.world_to_chunk(spawn_x, spawn_z)
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                self.world.get_chunk(pcx + dx, pcz + dz)
        spawn_y = self.world.get_height(spawn_x, spawn_z) + 2
        if spawn_y < 5:
            spawn_y = 50
        self.pos = np.array([spawn_x + 0.5, float(spawn_y), spawn_z + 0.5], dtype=np.float64)
        self.velocity = np.array([0.0, 0.0, 0.0], dtype=np.float64)
        self.yaw = 0.0
        self.pitch = 0.0
        self.on_ground = False
        self.flying = False
        self.creative = True
        self.health = 20.0
        self.max_health = 20.0
        self.hunger = 20.0
        self.hotbar = [GRASS, DIRT, STONE, WOOD, PLANKS, COBBLESTONE, SAND, GLASS, BRICK]
        self.selected_slot = 0
        self.fall_distance = 0.0
        self.inventory_open = False
        self.sprinting = False
        self.in_water = False
        self.dead = False
        self.respawn_timer = 0.0

    def get_forward(self):
        ry = math.radians(self.yaw)
        rp = math.radians(self.pitch)
        return np.array([-math.sin(ry)*math.cos(rp), -math.sin(rp), -math.cos(ry)*math.cos(rp)])

    def get_right(self):
        ry = math.radians(self.yaw)
        return np.array([-math.cos(ry), 0, math.sin(ry)])

    def get_eye_pos(self):
        return self.pos + np.array([0, PLAYER_HEIGHT, 0])

    def _check_in_water(self):
        eye = self.get_eye_pos()
        bx, by, bz = int(math.floor(eye[0])), int(math.floor(eye[1])), int(math.floor(eye[2]))
        return self.world.get_block(bx, by, bz) == WATER

    def update(self, dt, keys):
        if self.dead:
            self.respawn_timer -= dt
            if self.respawn_timer <= 0:
                self.dead = False
                self._spawn()
            return

        if self.inventory_open:
            return

        self.in_water = self._check_in_water()
        self.sprinting = keys.get(K_LCTRL, False) and not self.in_water

        forward = self.get_forward()
        right = self.get_right()
        forward[1] = 0
        n = np.linalg.norm(forward)
        if n > 0: forward /= n
        right[1] = 0
        n = np.linalg.norm(right)
        if n > 0: right /= n

        move = np.array([0.0, 0.0, 0.0])
        if self.flying:
            speed = FLY_SPEED
        elif self.in_water:
            speed = SWIM_SPEED
        elif self.sprinting:
            speed = SPRINT_SPEED
        else:
            speed = WALK_SPEED

        if keys.get(K_w): move += forward
        if keys.get(K_s): move -= forward
        if keys.get(K_a): move += right
        if keys.get(K_d): move -= right
        if np.linalg.norm(move) > 0:
            move = move / np.linalg.norm(move) * speed

        self.velocity[0] = move[0]
        self.velocity[2] = move[2]

        if self.flying:
            if keys.get(K_SPACE): self.velocity[1] = speed
            elif keys.get(K_LSHIFT): self.velocity[1] = -speed
            else: self.velocity[1] = 0
        elif self.in_water:
            if keys.get(K_SPACE):
                self.velocity[1] = 3.5
            self.velocity[1] += 1.5 * dt
            self.velocity[1] *= WATER_DRAG
            self.velocity[0] *= WATER_DRAG
            self.velocity[2] *= WATER_DRAG
        else:
            if keys.get(K_SPACE) and self.on_ground:
                self.velocity[1] = JUMP_SPEED
                self.on_ground = False
            self.velocity[1] += GRAVITY * dt
            self.velocity[1] = max(self.velocity[1], -50.0)

        new_pos = self.pos + self.velocity * dt
        new_pos = self._check_collision(new_pos)

        if new_pos[1] < self.pos[1] and not self.flying and not self.in_water:
            self.fall_distance += self.pos[1] - new_pos[1]
        elif self.on_ground or self.in_water:
            if self.fall_distance > 3.0 and not self.creative:
                damage = self.fall_distance - 3.0
                self.health -= damage
                self.health = max(0, self.health)
                if self.health <= 0:
                    self.die()
            self.fall_distance = 0.0

        self.pos = new_pos

        if self.pos[1] < -10:
            self.health = 0
            self.die()

        if not self.creative:
            self.hunger -= dt * 0.01
            self.hunger = max(0, self.hunger)
            if self.hunger > 18 and self.health < self.max_health:
                self.health = min(self.max_health, self.health + dt * 0.5)

    def die(self):
        if not self.dead:
            self.dead = True
            self.respawn_timer = 3.0
            self.velocity = np.array([0, 0, 0])

    def _check_collision(self, new_pos):
        hw = PLAYER_WIDTH / 2
        result = new_pos.copy()
        for axis in range(3):
            test_pos = self.pos.copy()
            test_pos[axis] = new_pos[axis]
            collision = False
            for dx in [-hw, hw]:
                for dz in [-hw, hw]:
                    for dy in [0.05, PLAYER_HEIGHT * 0.5, PLAYER_HEIGHT - 0.05]:
                        cx = test_pos[0] + dx
                        cy = test_pos[1] + dy
                        cz = test_pos[2] + dz
                        bx, by, bz = int(math.floor(cx)), int(math.floor(cy)), int(math.floor(cz))
                        block = self.world.get_block(bx, by, bz)
                        if block in SOLID_BLOCKS:
                            collision = True
                            break
                    if collision: break
                if collision: break
            if collision:
                result[axis] = self.pos[axis]
                if axis == 1:
                    if self.velocity[1] < 0: self.on_ground = True
                    self.velocity[axis] = 0
            else:
                if axis == 1: self.on_ground = False
        return result

    def _pos_occupied(self, x, y, z):
        hw = PLAYER_WIDTH / 2
        for dx in [-hw, hw]:
            for dz in [-hw, hw]:
                for dy in [0.05, PLAYER_HEIGHT * 0.5, PLAYER_HEIGHT - 0.05]:
                    px, py, pz = self.pos[0]+dx, self.pos[1]+dy, self.pos[2]+dz
                    if int(math.floor(px))==x and int(math.floor(py))==y and int(math.floor(pz))==z:
                        return True
        return False


# ─── Main Game ───────────────────────────────────────────────────────────────
class Game:
    def __init__(self):
        pygame.init()
        pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)
        pygame.display.gl_set_attribute(pygame.GL_DOUBLEBUFFER, 1)
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("MC by Mimo")
        self.clock = pygame.time.Clock()
        self.running = True
        self.keys = {}
        self.mouse_captured = False
        self.last_break = 0
        self.last_place = 0
        self.day_time = 0.25
        self.day_speed = 0.005
        self.world_time = 0.0
        self._init_gl()
        self.world = World(seed=42)
        self.player = Player(self.world)
        self.particles = ParticleSystem()
        self.clouds = CloudRenderer(self.world.seed)
        self._center_mouse()
        self.fps_counter = 0
        self.fps_display = 0
        self.fps_timer = 0

    def _init_gl(self):
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        # Disable backface culling to avoid winding issues
        glDisable(GL_CULL_FACE)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glShadeModel(GL_SMOOTH)
        glClearColor(0.5, 0.7, 1.0, 1.0)
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.3, 0.3, 0.35, 1.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 0.95, 0.85, 1.0))
        glLightfv(GL_LIGHT0, GL_POSITION, (0.5, 1.0, 0.3, 0.0))
        glEnable(GL_FOG)
        glFogi(GL_FOG_MODE, GL_LINEAR)
        glFogfv(GL_FOG_COLOR, (0.5, 0.7, 1.0, 1.0))
        glFogf(GL_FOG_START, CHUNK_SIZE * (RENDER_DISTANCE - 1))
        glFogf(GL_FOG_END, CHUNK_SIZE * RENDER_DISTANCE)

    def _center_mouse(self):
        pygame.mouse.set_pos(SCREEN_W // 2, SCREEN_H // 2)

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
                elif K_1 <= event.key <= K_9:
                    self.player.selected_slot = event.key - K_1
                elif event.key == K_f:
                    if self.player.creative:
                        self.player.flying = not self.player.flying
                elif event.key == K_t:
                    self.player.creative = not self.player.creative
                    if self.player.creative:
                        self.player.health = self.player.max_health
                        self.player.hunger = 20.0
                    else:
                        self.player.flying = False
                elif event.key == K_g:
                    self.day_speed = 0.0 if self.day_speed > 0 else 0.005
                elif event.key == K_r:
                    if self.player.dead:
                        self.player.dead = False
                        self.player._spawn()
                elif event.key == K_F11:
                    pygame.display.toggle_fullscreen()
            elif event.type == KEYUP:
                self.keys[event.key] = False
            elif event.type == MOUSEBUTTONDOWN:
                if not self.mouse_captured:
                    self.mouse_captured = True
                    pygame.mouse.set_visible(False)
                    pygame.event.set_grab(True)
                    self._center_mouse()
                    return
                if event.button == 1: self._break_block()
                elif event.button == 3: self._place_block()
                elif event.button == 4: self.player.selected_slot = (self.player.selected_slot - 1) % 9
                elif event.button == 5: self.player.selected_slot = (self.player.selected_slot + 1) % 9
            elif event.type == MOUSEMOTION and self.mouse_captured:
                dx, dy = event.rel
                # Inverted: negate dx so moving mouse right looks right
                self.player.yaw -= dx * 0.15
                self.player.pitch -= dy * 0.15
                self.player.pitch = max(-89, min(89, self.player.pitch))
                self._center_mouse()

    def _break_block(self):
        now = time.time()
        if now - self.last_break < BREAK_COOLDOWN: return
        eye = self.player.get_eye_pos()
        hit, _, _ = raycast(self.world, eye, self.player.get_forward())
        if not hit: return
        x, y, z = hit
        block = self.world.get_block(x, y, z)
        if block == BEDROCK and not self.player.creative:
            return
        if block != AIR:
            self.world.set_block(x, y, z, AIR)
            self.particles.emit((x, y, z), block, 15)
            self.last_break = now
            # Force immediate mesh rebuild for the affected chunk
            cx, cz = self.world.world_to_chunk(x, z)
            lx, lz = self.world.world_to_local(x, z)
            key = self.world.get_chunk_key(cx, cz)
            if key in self.world.chunks:
                self.world.chunks[key].build_mesh()
                self.world.dirty_chunks.discard(key)

    def _place_block(self):
        now = time.time()
        if now - self.last_place < PLACE_COOLDOWN: return
        eye = self.player.get_eye_pos()
        hit, place_pos, _ = raycast(self.world, eye, self.player.get_forward())
        if not hit or not place_pos: return
        px, py, pz = place_pos
        if py < 0 or py >= CHUNK_HEIGHT: return
        block_type = self.player.hotbar[self.player.selected_slot]
        if block_type == AIR: return
        if self.player._pos_occupied(px, py, pz): return
        existing = self.world.get_block(px, py, pz)
        if existing not in (AIR, WATER): return
        self.world.set_block(px, py, pz, block_type)
        self.last_place = now
        # Force immediate mesh rebuild
        cx, cz = self.world.world_to_chunk(px, pz)
        key = self.world.get_chunk_key(cx, cz)
        if key in self.world.chunks:
            self.world.chunks[key].build_mesh()
            self.world.dirty_chunks.discard(key)

    def _update(self, dt):
        self.player.update(dt, self.keys)
        self.particles.update(dt)
        self.world_time += dt
        self.fps_timer += dt
        self.fps_counter += 1
        if self.fps_timer >= 1.0:
            self.fps_display = self.fps_counter
            self.fps_counter = 0
            self.fps_timer = 0
        pcx, pcz = self.world.world_to_chunk(int(self.player.pos[0]), int(self.player.pos[2]))
        self.world.update(pcx, pcz)
        self.day_time = (self.day_time + self.day_speed * dt) % 1.0
        self._update_sky()

    def _update_sky(self):
        sun_angle = self.day_time * 2 * math.pi
        brightness = max(0.0, math.sin(sun_angle))
        r = 0.05 + 0.45 * brightness
        g = 0.05 + 0.65 * brightness
        b = 0.15 + 0.85 * brightness
        glClearColor(r, g, b, 1.0)
        glFogfv(GL_FOG_COLOR, (r, g, b, 1.0))
        ambient = 0.15 + 0.25 * brightness
        diffuse = 0.3 + 0.7 * brightness
        glLightfv(GL_LIGHT0, GL_AMBIENT, (ambient, ambient, ambient + 0.05, 1.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (diffuse, diffuse * 0.95, diffuse * 0.85, 1.0))
        glLightfv(GL_LIGHT0, GL_POSITION, (math.cos(sun_angle), math.sin(sun_angle), 0.5, 0.0))

    def _draw_target_block(self):
        eye = self.player.get_eye_pos()
        hit, _, _ = raycast(self.world, eye, self.player.get_forward())
        if not hit: return
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
        glColor4f(1, 1, 1, 0.08)
        for fi in range(6):
            glBegin(GL_QUADS)
            for vx, vy, vz in FACE_VERTS[fi]:
                glVertex3f(x + vx, y + vy, z + vz)
            glEnd()
        glDisable(GL_BLEND)
        glEnable(GL_FOG)
        glEnable(GL_LIGHTING)

    def _draw_hud(self):
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glDisable(GL_FOG)
        glDisable(GL_BLEND)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, SCREEN_W, 0, SCREEN_H, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        cx, cy = SCREEN_W // 2, SCREEN_H // 2
        glColor3f(1, 1, 1)
        glLineWidth(2)
        glBegin(GL_LINES)
        glVertex2f(cx - 12, cy); glVertex2f(cx + 12, cy)
        glVertex2f(cx, cy - 12); glVertex2f(cx, cy + 12)
        glEnd()
        bar_w = 9 * 44
        sx = (SCREEN_W - bar_w) // 2
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
            if block != AIR and block in BLOCK_COLORS:
                c = BLOCK_COLORS[block][1]
                glColor3f(c[0], c[1], c[2])
                glBegin(GL_QUADS)
                glVertex2f(bx + 3, sy + 3); glVertex2f(bx + 37, sy + 3)
                glVertex2f(bx + 37, sy + 37); glVertex2f(bx + 3, sy + 37)
                glEnd()
        if not self.player.creative:
            hx = sx
            for i in range(10):
                if self.player.health >= (i + 1) * 2:
                    glColor3f(0.85, 0.1, 0.1)
                elif self.player.health >= i * 2 + 1:
                    glColor3f(0.85, 0.35, 0.3)
                else:
                    glColor3f(0.25, 0.25, 0.25)
                glBegin(GL_QUADS)
                glVertex2f(hx + i * 18, sy + 50); glVertex2f(hx + i * 18 + 14, sy + 50)
                glVertex2f(hx + i * 18 + 14, sy + 64); glVertex2f(hx + i * 18, sy + 64)
                glEnd()
            for i in range(10):
                if self.player.hunger >= (i + 1) * 2:
                    glColor3f(0.75, 0.55, 0.15)
                elif self.player.hunger >= i * 2 + 1:
                    glColor3f(0.65, 0.5, 0.2)
                else:
                    glColor3f(0.25, 0.25, 0.25)
                glBegin(GL_QUADS)
                glVertex2f(hx + i * 18 + 200, sy + 50); glVertex2f(hx + i * 18 + 214, sy + 50)
                glVertex2f(hx + i * 18 + 214, sy + 64); glVertex2f(hx + i * 18 + 200, sy + 64)
                glEnd()
        if self.player.dead:
            self._draw_death_screen()
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_FOG)

    def _draw_death_screen(self):
        # Darken background
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(0.5, 0.0, 0.0, 0.4)
        glBegin(GL_QUADS)
        glVertex2f(0, 0); glVertex2f(SCREEN_W, 0)
        glVertex2f(SCREEN_W, SCREEN_H); glVertex2f(0, SCREEN_H)
        glEnd()
        glDisable(GL_BLEND)
        # Draw "YOU DIED" as a simple rectangle-based text
        cx, cy = SCREEN_W // 2, SCREEN_H // 2
        # Red block letters for "YOU DIED"
        glColor3f(0.9, 0.1, 0.1)
        glLineWidth(3)
        # Y
        self._draw_block_letter(cx - 180, cy + 10, 'Y')
        # O
        self._draw_block_letter(cx - 140, cy + 10, 'O')
        # U
        self._draw_block_letter(cx - 100, cy + 10, 'U')
        # space
        # D
        self._draw_block_letter(cx - 30, cy + 10, 'D')
        # I
        self._draw_block_letter(cx + 10, cy + 10, 'I')
        # E
        self._draw_block_letter(cx + 40, cy + 10, 'E')
        # D
        self._draw_block_letter(cx + 80, cy + 10, 'D')
        # Respawn text
        glColor3f(0.8, 0.8, 0.8)
        glLineWidth(1)
        timer = max(0, self.player.respawn_timer)
        # Simple countdown bar
        bar_w = 200
        bar_x = cx - bar_w // 2
        bar_y = cy - 40
        glColor3f(0.3, 0.3, 0.3)
        glBegin(GL_QUADS)
        glVertex2f(bar_x, bar_y); glVertex2f(bar_x + bar_w, bar_y)
        glVertex2f(bar_x + bar_w, bar_y + 10); glVertex2f(bar_x, bar_y + 10)
        glEnd()
        progress = 1.0 - (timer / 3.0)
        glColor3f(0.2, 0.8, 0.2)
        glBegin(GL_QUADS)
        glVertex2f(bar_x, bar_y); glVertex2f(bar_x + bar_w * progress, bar_y)
        glVertex2f(bar_x + bar_w * progress, bar_y + 10); glVertex2f(bar_x, bar_y + 10)
        glEnd()

    def _draw_block_letter(self, x, y, ch):
        """Draw a simple blocky letter using line segments."""
        segments = {
            'Y': [(0,20,10,10),(20,20,10,10),(10,10,10,0)],
            'O': [(0,0,0,20),(0,20,20,20),(20,20,20,0),(20,0,0,0)],
            'U': [(0,20,0,0),(0,0,20,0),(20,0,20,20)],
            'D': [(0,0,0,20),(0,20,14,20),(14,20,20,14),(20,14,20,6),(20,6,14,0),(14,0,0,0)],
            'I': [(0,20,20,20),(10,20,10,0),(0,0,20,0)],
            'E': [(20,20,0,20),(0,20,0,0),(0,0,20,0),(0,10,14,10)],
        }
        segs = segments.get(ch, [])
        glBegin(GL_LINES)
        for s in segs:
            glVertex2f(x + s[0], y + s[1])
            glVertex2f(x + s[2], y + s[3])
        glEnd()

    def _render(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(70, SCREEN_W / SCREEN_H, 0.1, 1000.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        eye = self.player.get_eye_pos()
        look = eye + self.player.get_forward()
        gluLookAt(eye[0], eye[1], eye[2], look[0], look[1], look[2], 0, 1, 0)
        pcx, pcz = self.world.world_to_chunk(int(self.player.pos[0]), int(self.player.pos[2]))
        self.world.draw(pcx, pcz)
        self.clouds.draw(self.player.pos, self.world_time)
        self.particles.draw()
        self._draw_target_block()
        self._draw_hud()

    def run(self):
        print("=" * 48)
        print("  MC by Mimo - Minecraft Clone")
        print("=" * 48)
        print("  WASD - Move | Space - Jump | Ctrl - Sprint")
        print("  F - Fly (Creative) | T - Creative/Survival")
        print("  Mouse - Look | LClick - Break | RClick - Place")
        print("  1-9 - Hotbar | R - Respawn | G - Freeze Time")
        print("  Esc - Release Mouse | F11 - Fullscreen")
        print("=" * 48)
        dt = 0
        while self.running:
            self._handle_events()
            self._update(dt)
            self._render()
            pygame.display.flip()
            dt = self.clock.tick(FPS) / 1000.0
            mode = "Creative" if self.player.creative else "Survival"
            fly = "[Fly]" if self.player.flying else ""
            sprint = "[Sprint]" if self.player.sprinting else ""
            water = "[Swim]" if self.player.in_water else ""
            dead = "[DEAD]" if self.player.dead else ""
            px, py, pz = self.player.pos
            caption = f"MC by Mimo | {mode} {fly}{sprint}{water}{dead} | {self.fps_display} FPS | {px:.1f},{py:.1f},{pz:.1f}"
            pygame.display.set_caption(caption)
        pygame.quit()


if __name__ == "__main__":
    Game().run()

"""Pythmc - World and Chunk System with Threading Optimizations

Features:
- Threaded chunk generation (no lag when crossing borders)
- Proper chunk unloading (memory management)
- Cross-chunk face culling (no hidden walls at borders)
- V2.3: GPU-accelerated terrain and cave generation via CUDA/CuPy
"""

import numpy as np
from noise import pnoise2, pnoise3
import random
import math
import threading
import queue
from OpenGL.GL import *
from constants import *
from textures import texture_manager

# Blocks that get per-block color variation
TINTABLE = {GRASS, LEAVES, SAND, SNOW, CACTUS, PLANKS, WOOD}

def _block_tint(wx, y, wz, block):
    h = (wx * 374761393 + y * 668265263 + wz * 1274126177) & 0xFFFFFFFF
    h = ((h >> 13) ^ h) * 1274126177
    h = (h >> 16) ^ h
    r = (h & 0xFF) / 255.0
    g = ((h >> 8) & 0xFF) / 255.0
    b = ((h >> 16) & 0xFF) / 255.0
    if block == GRASS:
        return (0.85 + 0.15 * r, 0.9 + 0.2 * g, 0.8 + 0.2 * b)
    elif block == LEAVES:
        return (0.8 + 0.2 * r, 0.85 + 0.3 * g, 0.75 + 0.2 * b)
    elif block == SAND:
        return (0.9 + 0.1 * r, 0.88 + 0.12 * g, 0.75 + 0.15 * b)
    elif block == SNOW:
        return (0.92 + 0.08 * r, 0.93 + 0.07 * g, 0.95 + 0.05 * b)
    elif block == CACTUS:
        return (0.85 + 0.15 * r, 0.92 + 0.15 * g, 0.8 + 0.15 * b)
    return (1.0, 1.0, 1.0)


class Chunk:
    def __init__(self, cx, cz, world):
        self.cx = cx
        self.cz = cz
        self.world = world
        self.blocks = np.zeros((CHUNK_SIZE, CHUNK_HEIGHT, CHUNK_SIZE), dtype=np.uint8)
        self.mesh_dirty = True
        self.display_list = None
        self.transparent_display_list = None
        self.generated = False
        self.mesh_built = False

    def generate_terrain(self, seed):
        """Generate terrain data (can be called from thread).
        Uses GPU acceleration via CUDA when available."""
        from cuda_manager import gpu_generate_chunk_terrain
        gpu_generate_chunk_terrain(self, seed)
        self._generate_cave_entrances(seed)
        self._generate_trees(seed)
        self.generated = True

    def _generate_caves(self, seed):
        """Generate cave systems. Uses GPU acceleration when available."""
        from cuda_manager import gpu_generate_caves
        gpu_generate_caves(self, seed)

    def _generate_cave_entrances(self, seed):
        world_x = self.cx * CHUNK_SIZE
        world_z = self.cz * CHUNK_SIZE
        rng = random.Random(seed + self.cx * 777 + self.cz * 333)
        
        for _ in range(2):
            if rng.random() > 0.15:
                continue
            x = rng.randint(2, CHUNK_SIZE - 3)
            z = rng.randint(2, CHUNK_SIZE - 3)
            surface_y = 0
            for y in range(CHUNK_HEIGHT - 1, 0, -1):
                if self.blocks[x, y, z] not in (AIR, WATER):
                    surface_y = y
                    break
            if surface_y < 20 or surface_y > 45:
                continue
            entrance_depth = rng.randint(8, 15)
            for dy in range(entrance_depth):
                y = surface_y - dy
                if y < 1:
                    break
                radius = max(1, 3 - dy // 4)
                for dx in range(-radius, radius + 1):
                    for dz in range(-radius, radius + 1):
                        if dx*dx + dz*dz <= radius*radius:
                            bx, bz = x + dx, z + dz
                            if 0 <= bx < CHUNK_SIZE and 0 <= bz < CHUNK_SIZE:
                                if y > 0:
                                    self.blocks[bx, y, bz] = AIR

    def _generate_trees(self, seed):
        world_x = self.cx * CHUNK_SIZE
        world_z = self.cz * CHUNK_SIZE
        center_wx = world_x + CHUNK_SIZE // 2
        center_wz = world_z + CHUNK_SIZE // 2
        biome_noise1 = pnoise2(center_wx * 0.002, center_wz * 0.002, octaves=2, base=seed + 500)
        biome_noise2 = pnoise2(center_wx * 0.003, center_wz * 0.003, octaves=2, base=seed + 600)
        biome_noise3 = pnoise2(center_wx * 0.0015, center_wz * 0.0015, octaves=2, base=seed + 700)
        
        if biome_noise3 < -0.25:
            biome = "ocean"
        elif biome_noise1 > 0.15 and biome_noise2 < 0.0:
            biome = "desert"
        elif biome_noise1 < -0.2:
            biome = "snow"
        elif biome_noise2 > 0.15:
            biome = "forest"
        elif biome_noise1 > 0.05 and biome_noise2 > 0.05:
            biome = "jungle"
        else:
            biome = "plains"
        
        if biome == "ocean": tree_chance = 0.0
        elif biome == "desert": tree_chance = 0.003
        elif biome == "forest": tree_chance = 0.05
        elif biome == "jungle": tree_chance = 0.06
        elif biome == "snow": tree_chance = 0.015
        else: tree_chance = 0.025
        
        for x in range(2, CHUNK_SIZE - 2):
            for z in range(2, CHUNK_SIZE - 2):
                wx = world_x + x
                wz = world_z + z
                rng = random.Random(seed * 997 + wx * 7 + wz * 13)
                height = self._get_height(x, z)
                if height > 20 and self.blocks[x, height, z] == GRASS and rng.random() < tree_chance:
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

    def build_mesh(self, world):
        """Build display list with cross-chunk face culling."""
        if not self.generated:
            return
        
        opaque_verts = []
        transparent_verts = []
        face_names = ['top', 'bottom', 'px', 'nx', 'pz', 'nz']
        
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
                        
                        # Cross-chunk face culling
                        if 0 <= nx_pos < CHUNK_SIZE and 0 <= nz_pos < CHUNK_SIZE:
                            neighbor = self.get_block(nx_pos, ny_pos, nz_pos)
                        else:
                            # Check neighboring chunk
                            world_x = self.cx * CHUNK_SIZE + nx_pos
                            world_z = self.cz * CHUNK_SIZE + nz_pos
                            neighbor = world.get_block(world_x, ny_pos, world_z)
                        
                        if is_transparent:
                            if neighbor == block:
                                continue
                            show_face = neighbor == AIR or (neighbor in TRANSPARENT and neighbor != block)
                        else:
                            show_face = neighbor in TRANSPARENT
                        
                        if not show_face:
                            continue
                        
                        face_name = face_names[face_idx]
                        uv = texture_manager.get_face_uv(block, face_name)
                        
                        shade = 1.0
                        if dy == 1: shade = 1.0
                        elif dy == -1: shade = 0.5
                        elif dx == -1 or dz == -1: shade = 0.7
                        elif dx == 1 or dz == 1: shade = 0.85
                        
                        wx = self.cx * CHUNK_SIZE + x
                        wz = self.cz * CHUNK_SIZE + z
                        
                        tint = _block_tint(wx, y, wz, block) if block in TINTABLE else (1.0, 1.0, 1.0)
                        
                        for i, (vx, vy, vz) in enumerate(FACE_VERTS[face_idx]):
                            if face_idx == 0:
                                u = uv[0] + (uv[2] - uv[0]) * vx
                                v = uv[1] + (uv[3] - uv[1]) * vz
                            elif face_idx == 1:
                                u = uv[0] + (uv[2] - uv[0]) * vx
                                v = uv[1] + (uv[3] - uv[1]) * vz
                            elif face_idx == 2 or face_idx == 3:
                                u = uv[0] + (uv[2] - uv[0]) * vz
                                v = uv[1] + (uv[3] - uv[1]) * vy
                            else:
                                u = uv[0] + (uv[2] - uv[0]) * vx
                                v = uv[1] + (uv[3] - uv[1]) * vy
                            
                            vert = (wx + vx, y + vy, wz + vz, u, v,
                                    shade * tint[0], shade * tint[1], shade * tint[2])
                            if is_transparent:
                                transparent_verts.append(vert)
                            else:
                                opaque_verts.append(vert)
        
        self._build_display_list(opaque_verts, transparent_verts)
        self.mesh_dirty = False
        self.mesh_built = True

    def _build_display_list(self, opaque_verts, transparent_verts):
        if self.display_list is None:
            self.display_list = glGenLists(1)
        glNewList(self.display_list, GL_COMPILE)
        if opaque_verts:
            texture_manager.bind()
            glBegin(GL_QUADS)
            for v in opaque_verts:
                glColor3f(v[5], v[6], v[7])
                glTexCoord2f(v[3], v[4])
                glVertex3f(v[0], v[1], v[2])
            glEnd()
            texture_manager.unbind()
        glEndList()

        if self.transparent_display_list is None:
            self.transparent_display_list = glGenLists(1)
        glNewList(self.transparent_display_list, GL_COMPILE)
        if transparent_verts:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            texture_manager.bind()
            glBegin(GL_QUADS)
            for v in transparent_verts:
                glColor4f(v[5], v[6], v[7], 0.6)
                glTexCoord2f(v[3], v[4])
                glVertex3f(v[0], v[1], v[2])
            glEnd()
            texture_manager.unbind()
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


class ChunkGenerator(threading.Thread):
    """Background thread for generating chunk data."""
    
    def __init__(self, world):
        super().__init__(daemon=True)
        self.world = world
        self.task_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.running = True
        self.start()
    
    def request_chunk(self, cx, cz):
        """Request chunk generation in background."""
        key = (cx, cz)
        self.task_queue.put((cx, cz))
    
    def run(self):
        """Background thread loop."""
        while self.running:
            try:
                cx, cz = self.task_queue.get(timeout=0.1)
                chunk = Chunk(cx, cz, self.world)
                chunk.generate_terrain(self.world.seed)
                self.result_queue.put((cx, cz, chunk))
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Chunk gen error: {e}")
    
    def get_completed_chunks(self):
        """Get all completed chunks from the result queue."""
        chunks = []
        while True:
            try:
                chunks.append(self.result_queue.get_nowait())
            except queue.Empty:
                break
        return chunks


class World:
    def __init__(self, seed=None):
        self.seed = seed if seed is not None else random.randint(0, 999999)
        self.chunks = {}
        self.dirty_chunks = set()
        self.chunk_gen = ChunkGenerator(self)
        self.pending_chunks = set()  # Chunks being generated
    
    def get_chunk_key(self, cx, cz):
        return (cx, cz)
    
    def get_chunk(self, cx, cz):
        """Get chunk, generating if needed (blocking)."""
        key = self.get_chunk_key(cx, cz)
        if key not in self.chunks:
            chunk = Chunk(cx, cz, self)
            chunk.generate_terrain(self.seed)
            chunk.build_mesh(self)
            self.chunks[key] = chunk
        return self.chunks[key]
    
    def request_chunk_async(self, cx, cz):
        """Request chunk generation in background thread."""
        key = self.get_chunk_key(cx, cz)
        if key not in self.chunks and key not in self.pending_chunks:
            self.pending_chunks.add(key)
            self.chunk_gen.request_chunk(cx, cz)
    
    def mark_chunk_dirty(self, cx, cz):
        key = self.get_chunk_key(cx, cz)
        if key in self.chunks:
            self.dirty_chunks.add(key)
    
    def world_to_chunk(self, wx, wz):
        return math.floor(wx / CHUNK_SIZE), math.floor(wz / CHUNK_SIZE)
    
    def world_to_local(self, wx, wz):
        return wx % CHUNK_SIZE, wz % CHUNK_SIZE
    
    def get_block(self, x, y, z):
        """Get block at world coordinates (generates chunk if needed)."""
        if y < 0 or y >= CHUNK_HEIGHT:
            return AIR
        cx, cz = self.world_to_chunk(x, z)
        lx, lz = self.world_to_local(x, z)
        key = self.get_chunk_key(cx, cz)
        if key in self.chunks:
            return self.chunks[key].get_block(lx, y, lz)
        return STONE if y > 0 else BEDROCK
    
    def set_block(self, x, y, z, block_type):
        if y < 0 or y >= CHUNK_HEIGHT:
            return
        cx, cz = self.world_to_chunk(x, z)
        lx, lz = self.world_to_local(x, z)
        key = self.get_chunk_key(cx, cz)
        if key in self.chunks:
            self.chunks[key].set_block(lx, y, lz, block_type)
    
    def update(self, player_cx, player_cz):
        """Update world: collect generated chunks, build meshes, unload far chunks."""
        # Collect completed chunks from background thread
        for cx, cz, chunk in self.chunk_gen.get_completed_chunks():
            key = (cx, cz)
            self.chunks[key] = chunk
            self.pending_chunks.discard(key)
            self.dirty_chunks.add(key)
            # Dirty neighbor chunks for border face culling
            for ddx, ddz in [(1,0),(-1,0),(0,1),(0,-1)]:
                nkey = (cx+ddx, cz+ddz)
                if nkey in self.chunks:
                    self.dirty_chunks.add(nkey)
        
        # Request chunks around player (async) - generate ahead
        gen_dist = RENDER_DISTANCE + 2
        for dx in range(-gen_dist, gen_dist + 1):
            for dz in range(-gen_dist, gen_dist + 1):
                cx, cz = player_cx + dx, player_cz + dz
                key = (cx, cz)
                if key not in self.chunks and key not in self.pending_chunks:
                    # Prioritize closer chunks
                    dist = abs(dx) + abs(dz)
                    if dist <= RENDER_DISTANCE + 1:
                        self.request_chunk_async(cx, cz)
        
        # Build meshes for dirty chunks (time-budgeted, ~5ms per frame)
        import time as _time
        start = _time.monotonic()
        built = 0
        for key in list(self.dirty_chunks):
            if key in self.chunks and self.chunks[key].generated:
                chunk = self.chunks[key]
                if chunk.mesh_dirty or not chunk.mesh_built:
                    chunk.build_mesh(self)
                    built += 1
                    if _time.monotonic() - start > 0.005:
                        break
        self.dirty_chunks -= {k for k in self.dirty_chunks if k in self.chunks and self.chunks[k].mesh_built}
        
        # Unload far chunks (Step 2)
        to_remove = []
        for key in self.chunks:
            dx = abs(key[0] - player_cx)
            dz = abs(key[1] - player_cz)
            if dx > RENDER_DISTANCE + 3 or dz > RENDER_DISTANCE + 3:
                to_remove.append(key)
        for key in to_remove:
            self.chunks[key].cleanup()
            del self.chunks[key]
    
    def draw(self, player_cx, player_cz):
        """Draw only chunks within render distance."""
        opaque, transparent = [], []
        for dx in range(-RENDER_DISTANCE, RENDER_DISTANCE + 1):
            for dz in range(-RENDER_DISTANCE, RENDER_DISTANCE + 1):
                key = (player_cx + dx, player_cz + dz)
                if key in self.chunks and self.chunks[key].mesh_built:
                    chunk = self.chunks[key]
                    opaque.append(chunk)
                    transparent.append(chunk)
        for c in opaque:
            c.draw_opaque()
        for c in transparent:
            c.draw_transparent()
    
    def get_height(self, x, z):
        for y in range(CHUNK_HEIGHT - 1, -1, -1):
            if self.get_block(x, y, z) not in (AIR, WATER):
                return y
        return 0


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
        if block not in (AIR, WATER, LAVA):
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

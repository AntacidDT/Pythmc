"""Pythmc - World Structures"""

import random
from constants import *


class Structure:
    """Base class for world structures."""
    
    def __init__(self, x, y, z, seed=0):
        self.x = x
        self.y = y
        self.z = z
        self.seed = seed
        self.rng = random.Random(seed)
    
    def place(self, chunk):
        """Place this structure directly in a chunk (chunk-local coords)."""
        raise NotImplementedError


class SmallHouse(Structure):
    """A small wooden house."""
    
    def place(self, chunk):
        ox, oy, oz = self.x, self.y, self.z
        # Convert to local coords
        lx = ox % 16
        lz = oz % 16
        
        def sb(dx, dy, dz, block):
            bx, by, bz = lx + dx, oy + dy, lz + dz
            if 0 <= bx < 16 and 0 <= by < 64 and 0 <= bz < 16:
                chunk.blocks[bx, by, bz] = block
        
        def gb(dx, dy, dz):
            bx, by, bz = lx + dx, oy + dy, lz + dz
            if 0 <= bx < 16 and 0 <= by < 64 and 0 <= bz < 16:
                return chunk.blocks[bx, by, bz]
            return AIR
        
        # Floor (5x5)
        for dx in range(5):
            for dz in range(5):
                sb(dx, 0, dz, PLANKS)
        
        # Walls
        for dy in range(1, 4):
            for dx in range(5):
                sb(dx, dy, 0, WOOD)
                sb(dx, dy, 4, WOOD)
            for dz in range(5):
                sb(0, dy, dz, WOOD)
                sb(4, dy, dz, WOOD)
        
        # Door opening
        sb(2, 1, 0, AIR)
        sb(2, 2, 0, AIR)
        
        # Windows
        sb(1, 2, 0, GLASS)
        sb(3, 2, 0, GLASS)
        sb(0, 2, 2, GLASS)
        sb(4, 2, 2, GLASS)
        
        # Roof
        for dy in range(2):
            for dx in range(-dy, 5 + dy):
                for dz in range(-dy, 5 + dy):
                    if 0 <= lx+dx < 16 and 0 <= lz+dz < 16:
                        if (0 <= dx < 5 or dx == -dy or dx == 4 + dy):
                            if (0 <= dz < 5 or dz == -dy or dz == 4 + dy):
                                if gb(dx, 4 + dy, dz) == AIR:
                                    sb(dx, 4 + dy, dz, PLANKS)
        
        # Torch inside
        sb(2, 2, 2, TORCH)


class StoneTower(Structure):
    """A stone tower."""
    
    def place(self, chunk):
        ox, oy, oz = self.x, self.y, self.z
        lx = ox % 16
        lz = oz % 16
        
        def sb(dx, dy, dz, block):
            bx, by, bz = lx + dx, oy + dy, lz + dz
            if 0 <= bx < 16 and 0 <= by < 64 and 0 <= bz < 16:
                chunk.blocks[bx, by, bz] = block
        
        # Base (3x3)
        for dx in range(3):
            for dz in range(3):
                sb(dx, 0, dz, COBBLESTONE)
        
        # Walls (8 high)
        for dy in range(1, 9):
            for dx in range(3):
                sb(dx, dy, 0, COBBLESTONE)
                sb(dx, dy, 2, COBBLESTONE)
            for dz in range(3):
                sb(0, dy, dz, COBBLESTONE)
                sb(2, dy, dz, COBBLESTONE)
        
        # Windows
        for dy in [3, 6]:
            sb(1, dy, 0, GLASS)
            sb(1, dy, 2, GLASS)
            sb(0, dy, 1, GLASS)
            sb(2, dy, 1, GLASS)
        
        # Battlements
        for dx in range(3):
            for dz in range(3):
                if (dx + dz) % 2 == 0:
                    sb(dx, 9, dz, COBBLESTONE)
        
        # Torch
        sb(1, 2, 1, TORCH)


class Ruins(Structure):
    """Crumbling stone ruins."""
    
    def place(self, chunk):
        lx = self.x % 16
        lz = self.z % 16
        
        def sb(dx, dy, dz, block):
            bx, by, bz = lx + dx, self.y + dy, lz + dz
            if 0 <= bx < 16 and 0 <= by < 64 and 0 <= bz < 16:
                chunk.blocks[bx, by, bz] = block
        
        height = self.rng.randint(2, 4)
        for dy in range(height):
            if self.rng.random() > 0.3:
                sb(0, dy, 0, COBBLESTONE)
            if self.rng.random() > 0.3:
                sb(2, dy, 0, COBBLESTONE)
            if self.rng.random() > 0.3:
                sb(0, dy, 2, COBBLESTONE)
            if self.rng.random() > 0.3:
                sb(2, dy, 2, COBBLESTONE)
        
        for dx in range(3):
            for dz in range(3):
                if self.rng.random() > 0.4:
                    sb(dx, 0, dz, COBBLESTONE)


class Well(Structure):
    """A stone well."""
    
    def place(self, chunk):
        lx = self.x % 16
        lz = self.z % 16
        
        def sb(dx, dy, dz, block):
            bx, by, bz = lx + dx, self.y + dy, lz + dz
            if 0 <= bx < 16 and 0 <= by < 64 and 0 <= bz < 16:
                chunk.blocks[bx, by, bz] = block
        
        for dx in range(3):
            for dz in range(3):
                sb(dx, 0, dz, COBBLESTONE)
        
        for dy in range(1, 3):
            for dx in range(3):
                sb(dx, dy, 0, COBBLESTONE)
                sb(dx, dy, 2, COBBLESTONE)
            for dz in range(3):
                sb(0, dy, dz, COBBLESTONE)
                sb(2, dy, dz, COBBLESTONE)
        
        sb(1, 1, 1, WATER)


class Garden(Structure):
    """A small garden."""
    
    def place(self, chunk):
        lx = self.x % 16
        lz = self.z % 16
        
        def sb(dx, dy, dz, block):
            bx, by, bz = lx + dx, self.y + dy, lz + dz
            if 0 <= bx < 16 and 0 <= by < 64 and 0 <= bz < 16:
                chunk.blocks[bx, by, bz] = block
        
        for dx in range(4):
            for dz in range(4):
                sb(dx, 0, dz, DIRT)
        
        for dx in range(4):
            sb(dx, 1, 0, PLANKS)
            sb(dx, 1, 3, PLANKS)
        for dz in range(4):
            sb(0, 1, dz, PLANKS)
            sb(3, 1, dz, PLANKS)
        
        for dx in range(1, 3):
            for dz in range(1, 3):
                sb(dx, 1, dz, GRASS)


# Structure spawning configuration
STRUCTURE_TYPES = [
    (SmallHouse, 0.003),    # 0.3% chance per chunk
    (StoneTower, 0.001),    # 0.1% chance per chunk
    (Ruins, 0.005),         # 0.5% chance per chunk
    (Well, 0.002),          # 0.2% chance per chunk
    (Garden, 0.003),        # 0.3% chance per chunk
    ("Factory", 0.008),     # 0.8% chance per chunk (factories are rare but valuable)
]


def try_place_structures(chunk, seed):
    """Try to place structures in a chunk."""
    world_x = chunk.cx * CHUNK_SIZE
    world_z = chunk.cz * CHUNK_SIZE
    
    # Use chunk coordinates for deterministic placement
    rng = random.Random(seed + chunk.cx * 997 + chunk.cz * 1337)
    
    for structure_class, chance in STRUCTURE_TYPES:
        for _ in range(2):
            if rng.random() < chance:
                local_x = rng.randint(1, CHUNK_SIZE - 6)
                local_z = rng.randint(1, CHUNK_SIZE - 6)
                
                world_block_x = world_x + local_x
                world_block_z = world_z + local_z
                
                # Find ground level in this chunk
                ground_y = None
                for y in range(CHUNK_HEIGHT - 1, 0, -1):
                    block = chunk.blocks[local_x, y, local_z]
                    if block in (GRASS, DIRT, STONE, SAND, SNOW):
                        ground_y = y + 1
                        break
                
                if ground_y and ground_y > 20 and ground_y < CHUNK_HEIGHT - 10:
                    if structure_class == "Factory":
                        # Factory uses different generation
                        from factory import Factory
                        factory = Factory(world_block_x, ground_y, world_block_z,
                                         seed + int(world_block_x * 100 + world_block_z))
                        factory.generate(chunk.world)
                    else:
                        structure = structure_class(world_block_x, ground_y, world_block_z,
                                                   seed + int(world_block_x * 100 + world_block_z))
                        structure.place(chunk)

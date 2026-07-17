"""Pythmc - Factory Structure Generator

Generates abandoned electronics factories with:
- Assembly lines
- Component storage shelves
- Circuit boards on tables
- Working lights (sometimes)
- Valuable loot
"""

import random
from constants import *


class Factory:
    """Generates an electronics factory structure."""
    
    def __init__(self, x, y, z, seed):
        self.x = x
        self.y = y
        self.z = z
        self.seed = seed
        self.rng = random.Random(seed)

    def generate(self, world):
        """Generate the factory in the world."""
        # Factory dimensions
        width = self.rng.randint(12, 18)
        depth = self.rng.randint(12, 18)
        height = 6

        x0, y0, z0 = self.x, self.y, self.z

        # Foundation
        for dx in range(width):
            for dz in range(depth):
                world.set_block(x0 + dx, y0, z0 + dz, STONE)

        # Walls
        for dy in range(1, height + 1):
            for dx in range(width):
                world.set_block(x0 + dx, y0 + dy, z0, BRICK)
                world.set_block(x0 + dx, y0 + dy, z0 + depth - 1, BRICK)
            for dz in range(depth):
                world.set_block(x0, y0 + dy, z0 + dz, BRICK)
                world.set_block(x0 + width - 1, y0 + dy, z0 + dz, BRICK)

        # Floor
        for dx in range(1, width - 1):
            for dz in range(1, depth - 1):
                world.set_block(x0 + dx, y0 + 1, z0 + dz, STONE)

        # Roof
        for dx in range(width):
            for dz in range(depth):
                world.set_block(x0 + dx, y0 + height, z0 + dz, STONE)

        # Door opening
        door_x = width // 2
        world.set_block(x0 + door_x, y0 + 2, z0, AIR)
        world.set_block(x0 + door_x, y0 + 3, z0, AIR)
        world.set_block(x0 + door_x + 1, y0 + 2, z0, AIR)
        world.set_block(x0 + door_x + 1, y0 + 3, z0, AIR)

        # Windows
        for dx in [3, width - 4]:
            for dy in [3, 4]:
                world.set_block(x0 + dx, y0 + dy, z0, GLASS)
                world.set_block(x0 + dx, y0 + dy, z0 + depth - 1, GLASS)

        # Interior - Assembly tables
        self._generate_assembly_tables(world, x0, y0, z0, width, depth)

        # Interior - Storage shelves
        self._generate_storage(world, x0, y0, z0, width, depth)

        # Interior - Workbenches with circuit boards
        self._generate_workbenches(world, x0, y0, z0, width, depth)

        # Lighting (torches)
        self._generate_lighting(world, x0, y0, z0, width, depth, height)

        # Loot chests (using special blocks as markers)
        self._generate_loot(world, x0, y0, z0, width, depth)

    def _generate_assembly_tables(self, world, x0, y0, z0, width, depth):
        """Generate assembly line tables."""
        # Long tables along the center
        table_z = depth // 2
        for dx in range(2, width - 2):
            if self.rng.random() < 0.7:
                world.set_block(x0 + dx, y0 + 2, z0 + table_z, PLANKS)
                # Random components on table
                if self.rng.random() < 0.3:
                    world.set_block(x0 + dx, y0 + 3, z0 + table_z, CIRCUIT_BOARD)
                elif self.rng.random() < 0.2:
                    world.set_block(x0 + dx, y0 + 3, z0 + table_z, RESISTOR_BLOCK)
                elif self.rng.random() < 0.2:
                    world.set_block(x0 + dx, y0 + 3, z0 + table_z, CAPACITOR_BLOCK)

    def _generate_storage(self, world, x0, y0, z0, width, depth):
        """Generate storage shelves with components."""
        # Shelves along walls
        for dz in range(2, depth - 2, 3):
            # Left wall shelf
            if self.rng.random() < 0.6:
                world.set_block(x0 + 1, y0 + 2, z0 + dz, PLANKS)
                world.set_block(x0 + 1, y0 + 3, z0 + dz, PLANKS)
                # Items on shelf
                if self.rng.random() < 0.5:
                    world.set_block(x0 + 1, y0 + 4, z0 + dz, CIRCUIT_BOARD)
                if self.rng.random() < 0.3:
                    world.set_block(x0 + 1, y0 + 4, z0 + dz + 1, RESISTOR_BLOCK)

            # Right wall shelf
            if self.rng.random() < 0.6:
                world.set_block(x0 + width - 2, y0 + 2, z0 + dz, PLANKS)
                world.set_block(x0 + width - 2, y0 + 3, z0 + dz, PLANKS)
                if self.rng.random() < 0.5:
                    world.set_block(x0 + width - 2, y0 + 4, z0 + dz, CAPACITOR_BLOCK)

    def _generate_workbenches(self, world, x0, y0, z0, width, depth):
        """Generate workbenches with electronics."""
        # Corner workstations
        corners = [
            (2, 2), (2, depth - 3),
            (width - 3, 2), (width - 3, depth - 3)
        ]

        for cx, cz in corners:
            # Desk
            for dx in range(2):
                for dz in range(2):
                    world.set_block(x0 + cx + dx, y0 + 2, z0 + cz + dz, PLANKS)

            # Chair (stairs placeholder)
            world.set_block(x0 + cx + 1, y0 + 2, z0 + cz + 2, COBBLESTONE)

            # Electronics on desk
            if self.rng.random() < 0.7:
                world.set_block(x0 + cx, y0 + 3, z0 + cz, CIRCUIT_BOARD)
            if self.rng.random() < 0.5:
                world.set_block(x0 + cx + 1, y0 + 3, z0 + cz, NE555_BLOCK)
            if self.rng.random() < 0.4:
                world.set_block(x0 + cx, y0 + 3, z0 + cz + 1, TRANSISTOR_NPN)

    def _generate_lighting(self, world, x0, y0, z0, width, depth, height):
        """Generate factory lighting."""
        # Torches on walls
        for dz in range(2, depth - 2, 4):
            if self.rng.random() < 0.7:
                world.set_block(x0 + 1, y0 + height - 1, z0 + dz, TORCH)
                world.set_block(x0 + width - 2, y0 + height - 1, z0 + dz, TORCH)

        # Ceiling lights (using glowstone-like blocks)
        for dx in range(3, width - 3, 4):
            for dz in range(3, depth - 3, 4):
                if self.rng.random() < 0.5:
                    world.set_block(x0 + dx, y0 + height - 1, z0 + dz, GLASS)

    def _generate_loot(self, world, x0, y0, z0, width, depth):
        """Generate loot containers."""
        # Hidden storage room
        if width > 14 and depth > 14:
            # Create a small back room
            room_x = x0 + width - 5
            room_z = z0 + depth - 5
            for dy in range(2, 5):
                for dx in range(4):
                    for dz in range(4):
                        if dx == 0 or dx == 3 or dz == 0 or dz == 3:
                            world.set_block(room_x + dx, y0 + dy, room_z + dz, BRICK)
                        else:
                            world.set_block(room_x + dx, y0 + dy, room_z + dz, AIR)

            # Door to room
            world.set_block(room_x, y0 + 2, room_z + 1, AIR)
            world.set_block(room_x, y0 + 3, room_z + 1, AIR)

            # Valuable loot inside
            world.set_block(room_x + 1, y0 + 2, room_z + 1, CIRCUIT_BOARD)
            world.set_block(room_x + 2, y0 + 2, room_z + 1, NE555_BLOCK)
            world.set_block(room_x + 1, y0 + 2, room_z + 2, TRANSISTOR_NPN)
            world.set_block(room_x + 2, y0 + 2, room_z + 2, LOGIC_AND)

        # Random component drops on floor
        for _ in range(self.rng.randint(3, 8)):
            dx = self.rng.randint(2, width - 3)
            dz = self.rng.randint(2, depth - 3)
            comp_type = self.rng.choice([
                RESISTOR_BLOCK, CAPACITOR_BLOCK, TRANSISTOR_NPN,
                CIRCUIT_BOARD, NE555_BLOCK, LOGIC_GATE
            ])
            world.set_block(x0 + dx, y0 + 2, z0 + dz, comp_type)


def try_generate_factory(world, chunk, seed):
    """Try to generate a factory in a chunk."""
    rng = random.Random(seed + chunk.cx * 555 + chunk.cz * 777)
    
    # Only generate in plains biome, rarely
    if rng.random() > 0.02:  # 2% chance per chunk
        return
    
    # Find suitable location (flat area)
    world_x = chunk.cx * CHUNK_SIZE
    world_z = chunk.cz * CHUNK_SIZE
    
    # Check for flat area
    for attempt in range(3):
        local_x = rng.randint(1, CHUNK_SIZE - 12)
        local_z = rng.randint(1, CHUNK_SIZE - 12)
        
        # Check if area is relatively flat
        heights = []
        for dx in range(10):
            for dz in range(10):
                h = chunk._get_height(local_x + dx, local_z + dz)
                heights.append(h)
        
        if not heights:
            continue
            
        min_h = min(heights)
        max_h = max(heights)
        
        if max_h - min_h <= 3 and min_h > 20:  # Flat enough and above water
            factory = Factory(
                world_x + local_x,
                min_h + 1,
                world_z + local_z,
                seed + chunk.cx * 1000 + chunk.cz
            )
            factory.generate(world)
            return

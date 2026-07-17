"""Pythmc - Procedural Low-Poly Texture System"""

import numpy as np
from OpenGL.GL import *
import random

# Texture size (16x16 for that classic Minecraft look)
TEX_SIZE = 16


class TextureManager:
    def __init__(self):
        self.textures = {}  # block_type -> texture_id
        self.atlas = None
        self.atlas_id = None
        self.block_uvs = {}  # block_type -> (u0, v0, u1, v1)
        
    def init(self):
        """Generate all block textures."""
        from constants import (GRASS, DIRT, STONE, WOOD, LEAVES, SAND, WATER,
                               COBBLESTONE, PLANKS, BEDROCK, COAL_ORE, IRON_ORE,
                               GLASS, BRICK, SNOW, CACTUS, TORCH, GRAVEL, GOLD_ORE,
                               DIAMOND_ORE, CRAFTING_TABLE_BLOCK, FURNACE_BLOCK)
        
        # Define texture generators for each block type
        texture_defs = {
            GRASS: (self._tex_grass_top, self._tex_grass_side, self._tex_dirt),
            DIRT: (self._tex_dirt, self._tex_dirt, self._tex_dirt),
            STONE: (self._tex_stone, self._tex_stone, self._tex_stone),
            WOOD: (self._tex_wood_top, self._tex_wood_side, self._tex_wood_top),
            LEAVES: (self._tex_leaves, self._tex_leaves, self._tex_leaves),
            SAND: (self._tex_sand, self._tex_sand, self._tex_sand),
            WATER: (self._tex_water, self._tex_water, self._tex_water),
            COBBLESTONE: (self._tex_cobble, self._tex_cobble, self._tex_cobble),
            PLANKS: (self._tex_planks, self._tex_planks, self._tex_planks),
            BEDROCK: (self._tex_bedrock, self._tex_bedrock, self._tex_bedrock),
            COAL_ORE: (self._tex_stone, self._tex_ore_coal, self._tex_stone),
            IRON_ORE: (self._tex_stone, self._tex_ore_iron, self._tex_stone),
            GOLD_ORE: (self._tex_stone, self._tex_ore_gold, self._tex_stone),
            DIAMOND_ORE: (self._tex_stone, self._tex_ore_diamond, self._tex_stone),
            GLASS: (self._tex_glass, self._tex_glass, self._tex_glass),
            BRICK: (self._tex_brick, self._tex_brick, self._tex_brick),
            SNOW: (self._tex_snow, self._tex_snow_side, self._tex_dirt),
            CACTUS: (self._tex_cactus_top, self._tex_cactus_side, self._tex_cactus_top),
            TORCH: (self._tex_torch, self._tex_torch, self._tex_torch),
            GRAVEL: (self._tex_gravel, self._tex_gravel, self._tex_gravel),
            CRAFTING_TABLE_BLOCK: (self._tex_craft_top, self._tex_craft_side, self._tex_planks),
            FURNACE_BLOCK: (self._tex_furnace_top, self._tex_furnace_side, self._tex_stone),
        }
        
        # Generate textures for each block
        for block_type, (top_fn, side_fn, bottom_fn) in texture_defs.items():
            top = top_fn()
            side = side_fn()
            bottom = bottom_fn()
            self.textures[block_type] = (top, side, bottom)
        
        # Create texture atlas
        self._build_atlas()
    
    def _noise(self, base_color, variation=15, seed=0):
        """Generate a noisy 16x16 texture."""
        rng = random.Random(seed)
        img = np.zeros((TEX_SIZE, TEX_SIZE, 4), dtype=np.uint8)
        for y in range(TEX_SIZE):
            for x in range(TEX_SIZE):
                r = max(0, min(255, base_color[0] + rng.randint(-variation, variation)))
                g = max(0, min(255, base_color[1] + rng.randint(-variation, variation)))
                b = max(0, min(255, base_color[2] + rng.randint(-variation, variation)))
                img[y, x] = [r, g, b, 255]
        return img
    
    def _tex_grass_top(self):
        return self._noise((76, 153, 0), 20, seed=1)
    
    def _tex_grass_side(self):
        """Grass side - dirt with grass strip on top."""
        img = self._noise((134, 96, 67), 12, seed=2)
        # Green strip at bottom of texture (appears at top in OpenGL due to flip)
        for x in range(TEX_SIZE):
            for y in range(13, 16):
                img[y, x] = [76 + random.randint(-10, 10), 
                            153 + random.randint(-10, 10), 
                            0 + random.randint(0, 10), 255]
        return img
    
    def _tex_dirt(self):
        return self._noise((134, 96, 67), 15, seed=3)
    
    def _tex_stone(self):
        img = self._noise((128, 128, 128), 18, seed=4)
        # Add some darker patches
        for _ in range(8):
            x, y = random.randint(0, 14), random.randint(0, 14)
            for dy in range(2):
                for dx in range(2):
                    if 0 <= x+dx < 16 and 0 <= y+dy < 16:
                        img[y+dy, x+dx] = [max(0, c - 30) for c in img[y+dy, x+dx][:3]] + [255]
        return img
    
    def _tex_wood_top(self):
        """Wood top - rings."""
        img = np.zeros((TEX_SIZE, TEX_SIZE, 4), dtype=np.uint8)
        cx, cy = 8, 8
        for y in range(TEX_SIZE):
            for x in range(TEX_SIZE):
                dist = ((x - cx)**2 + (y - cy)**2) ** 0.5
                ring = int(dist * 2) % 3
                if ring == 0:
                    img[y, x] = [101, 67, 33, 255]
                else:
                    img[y, x] = [139, 90, 43, 255]
        return img
    
    def _tex_wood_side(self):
        """Wood side - bark pattern."""
        img = self._noise((101, 67, 33), 12, seed=5)
        # Vertical lines
        for x in range(0, TEX_SIZE, 3):
            for y in range(TEX_SIZE):
                img[y, x] = [max(0, c - 15) for c in img[y, x][:3]] + [255]
        return img
    
    def _tex_leaves(self):
        """Leaves - scattered green pixels."""
        img = np.zeros((TEX_SIZE, TEX_SIZE, 4), dtype=np.uint8)
        rng = random.Random(6)
        for y in range(TEX_SIZE):
            for x in range(TEX_SIZE):
                if rng.random() > 0.15:
                    g = rng.randint(100, 180)
                    img[y, x] = [rng.randint(20, 60), g, rng.randint(0, 30), 255]
                else:
                    img[y, x] = [0, 0, 0, 0]  # Transparent
        return img
    
    def _tex_sand(self):
        return self._noise((214, 207, 142), 15, seed=7)
    
    def _tex_water(self):
        img = self._noise((50, 100, 200), 15, seed=8)
        # Make semi-transparent
        img[:, :, 3] = 180
        return img
    
    def _tex_cobble(self):
        """Cobblestone - irregular gray patches."""
        img = self._noise((120, 120, 120), 20, seed=9)
        # Add "cobble" pattern
        for _ in range(12):
            x, y = random.randint(0, 12), random.randint(0, 12)
            w, h = random.randint(2, 4), random.randint(2, 4)
            shade = random.randint(-30, 30)
            for dy in range(h):
                for dx in range(w):
                    if 0 <= x+dx < 16 and 0 <= y+dy < 16:
                        for c in range(3):
                            val = int(img[y+dy, x+dx, c]) + shade
                            img[y+dy, x+dx, c] = max(0, min(255, val))
        return img
    
    def _tex_planks(self):
        """Wood planks - horizontal lines."""
        img = self._noise((180, 140, 80), 12, seed=10)
        # Plank separators
        for y in range(0, TEX_SIZE, 4):
            for x in range(TEX_SIZE):
                img[y, x] = [max(0, c - 30) for c in img[y, x][:3]] + [255]
        return img
    
    def _tex_bedrock(self):
        return self._noise((60, 60, 60), 15, seed=11)
    
    def _tex_ore_coal(self):
        """Stone with coal spots."""
        img = self._tex_stone()
        spots = [(3, 4), (4, 4), (3, 5), (4, 5), (10, 8), (11, 8), (10, 9)]
        for x, y in spots:
            if 0 <= x < 16 and 0 <= y < 16:
                img[y, x] = [20, 20, 20, 255]
        return img
    
    def _tex_ore_iron(self):
        """Stone with iron spots."""
        img = self._tex_stone()
        spots = [(5, 3), (6, 3), (5, 4), (6, 4), (11, 10), (12, 10)]
        for x, y in spots:
            if 0 <= x < 16 and 0 <= y < 16:
                img[y, x] = [200, 180, 160, 255]
        return img
    
    def _tex_ore_gold(self):
        """Stone with gold spots."""
        img = self._tex_stone()
        spots = [(4, 5), (5, 5), (4, 6), (5, 6), (10, 11), (11, 11)]
        for x, y in spots:
            if 0 <= x < 16 and 0 <= y < 16:
                img[y, x] = [255, 215, 0, 255]
        return img

    def _tex_ore_diamond(self):
        """Stone with diamond spots."""
        img = self._tex_stone()
        spots = [(3, 3), (4, 3), (3, 4), (4, 4), (11, 9), (12, 9), (11, 10), (12, 10), (7, 12)]
        for x, y in spots:
            if 0 <= x < 16 and 0 <= y < 16:
                img[y, x] = [70, 200, 210, 255]
        return img
    
    def _tex_glass(self):
        """Glass - mostly transparent with slight tint."""
        img = np.zeros((TEX_SIZE, TEX_SIZE, 4), dtype=np.uint8)
        img[:, :] = [200, 220, 240, 60]
        # Border
        for i in range(TEX_SIZE):
            img[0, i] = [180, 200, 220, 150]
            img[15, i] = [180, 200, 220, 150]
            img[i, 0] = [180, 200, 220, 150]
            img[i, 15] = [180, 200, 220, 150]
        return img
    
    def _tex_brick(self):
        """Brick pattern."""
        img = np.zeros((TEX_SIZE, TEX_SIZE, 4), dtype=np.uint8)
        # Mortar background
        img[:, :] = [180, 175, 165, 255]
        # Bricks
        brick_color = [(170, 60, 50), (160, 55, 45), (180, 65, 55)]
        for row in range(4):
            y_start = row * 4
            offset = 4 if row % 2 else 0
            for col in range(2):
                x_start = (col * 8 + offset) % 16
                c = brick_color[(row + col) % 3]
                for dy in range(1, 4):
                    for dx in range(1, 7):
                        bx, by = (x_start + dx) % 16, y_start + dy
                        if 0 <= by < 16:
                            img[by, bx] = [c[0] + random.randint(-5, 5), 
                                          c[1] + random.randint(-5, 5), 
                                          c[2] + random.randint(-5, 5), 255]
        return img
    
    def _tex_snow(self):
        return self._noise((240, 245, 255), 8, seed=15)
    
    def _tex_snow_side(self):
        """Snow side - dirt with snow on top."""
        img = self._noise((134, 96, 67), 12, seed=16)
        for x in range(TEX_SIZE):
            for y in range(13, 16):
                img[y, x] = [240 + random.randint(-5, 5), 
                            245 + random.randint(-5, 5), 
                            255, 255]
        return img
    
    def _tex_cactus_top(self):
        return self._noise((50, 130, 40), 15, seed=17)
    
    def _tex_cactus_side(self):
        img = self._noise((50, 130, 40), 12, seed=18)
        # Spines
        for y in range(0, TEX_SIZE, 3):
            img[y, 8] = [70, 150, 50, 255]
        return img
    
    def _tex_torch(self):
        img = np.zeros((TEX_SIZE, TEX_SIZE, 4), dtype=np.uint8)
        # Stick
        for y in range(4, 16):
            img[y, 7] = [139, 90, 43, 255]
            img[y, 8] = [139, 90, 43, 255]
        # Flame
        for y in range(0, 5):
            for x in range(6, 10):
                if random.random() > 0.2:
                    img[y, x] = [255, random.randint(150, 220), 0, 255]
        return img
    
    def _tex_gravel(self):
        return self._noise((130, 125, 120), 20, seed=20)
    
    def _tex_craft_top(self):
        """Crafting table top - grid pattern."""
        img = self._noise((180, 140, 80), 10, seed=21)
        # Grid lines
        for i in range(0, TEX_SIZE, 4):
            for x in range(TEX_SIZE):
                img[i, x] = [100, 70, 30, 255]
                img[x, i] = [100, 70, 30, 255]
        return img
    
    def _tex_craft_side(self):
        """Crafting table side - tools."""
        img = self._noise((180, 140, 80), 10, seed=22)
        # Simple saw pattern
        for y in range(4, 12):
            img[y, 3] = [150, 150, 150, 255]
            img[y, 4] = [150, 150, 150, 255]
        return img
    
    def _tex_furnace_top(self):
        return self._noise((120, 120, 120), 15, seed=23)
    
    def _tex_furnace_side(self):
        """Furnace side - with opening."""
        img = self._noise((120, 120, 120), 15, seed=24)
        # Dark opening
        for y in range(6, 12):
            for x in range(5, 11):
                img[y, x] = [30, 30, 30, 255]
        return img
    
    def _build_atlas(self):
        """Build a texture atlas from all block textures."""
        # Count total textures needed (6 per block: 4 sides, top, bottom)
        num_blocks = len(self.textures)
        if num_blocks == 0:
            return
            
        # Atlas: 16 textures per row, each 16x16
        textures_per_row = 16
        total_faces = num_blocks * 6
        num_rows = (total_faces + textures_per_row - 1) // textures_per_row
        
        atlas_w = textures_per_row * TEX_SIZE
        atlas_h = max(num_rows, 1) * TEX_SIZE
        
        self.atlas = np.zeros((atlas_h, atlas_w, 4), dtype=np.uint8)
        
        idx = 0
        for block_type, (top, side, bottom) in self.textures.items():
            # Face order matches FACE_DIRS: +Y, -Y, +X, -X, +Z, -Z
            for face_img in [top, bottom, side, side, side, side]:
                col = idx % textures_per_row
                row = idx // textures_per_row
                x0 = col * TEX_SIZE
                y0 = row * TEX_SIZE
                self.atlas[y0:y0+TEX_SIZE, x0:x0+TEX_SIZE] = face_img
                
                # Store UV coordinates
                u0 = x0 / atlas_w
                v0 = y0 / atlas_h
                u1 = (x0 + TEX_SIZE) / atlas_w
                v1 = (y0 + TEX_SIZE) / atlas_h
                
                if block_type not in self.block_uvs:
                    self.block_uvs[block_type] = {}
                face_names = ['top', 'bottom', 'px', 'nx', 'pz', 'nz']
                self.block_uvs[block_type][face_names[idx % 6]] = (u0, v0, u1, v1)
                
                idx += 1
        
        # Upload to OpenGL
        self.atlas_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.atlas_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, atlas_w, atlas_h, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE, self.atlas)
    
    def bind(self):
        """Bind the texture atlas."""
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.atlas_id)
    
    def unbind(self):
        """Unbind textures."""
        glDisable(GL_TEXTURE_2D)
    
    def get_face_uv(self, block_type, face):
        """Get UV coordinates for a block face."""
        if block_type in self.block_uvs:
            return self.block_uvs[block_type].get(face, (0, 0, 1, 1))
        return (0, 0, 1, 1)


# Global texture manager
texture_manager = TextureManager()

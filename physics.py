"""Pythmc - Physics System V2.3 - Better Physics + CUDA

Features:
- FallingBlock entities (explosion debris with force vectors)
- Sphere-based explosions (radius check, hardness-based destruction)
- Fluid simulation (water/lava fill holes like real Minecraft)
- Wind system (pushes water, affects particles)
- Rain-ground interaction (puddles from heavy rain)
- Block gravity (sand/gravel fall when unsupported)
- V2.3: GPU-accelerated fluid simulation and particle updates via CUDA
- Hyper-optimized (time-budgeted, spatial queries, dirty chunk batching)
"""

import math
import random
import time
import numpy as np
from collections import deque
from constants import *


class FallingBlock:
    """A block entity that flies away with physics during explosions,
    then either lands and becomes a block or vanishes."""

    __slots__ = (
        'block_type', 'pos', 'velocity', 'rotation', 'spin',
        'life', 'on_ground', 'damage', 'alpha'
    )

    def __init__(self, block_type, pos, velocity=None, damage=0.0):
        self.block_type = block_type
        self.pos = np.array(pos, dtype=np.float64)
        if velocity is not None:
            self.velocity = np.array(velocity, dtype=np.float64)
        else:
            self.velocity = np.array([
                random.uniform(-2, 2),
                random.uniform(4, 10),
                random.uniform(-2, 2)
            ], dtype=np.float64)
        self.rotation = random.uniform(0, 360.0)
        self.spin = np.array([
            random.uniform(-400, 400),
            random.uniform(-400, 400),
            random.uniform(-400, 400)
        ], dtype=np.float64)
        self.life = EXPLOSION_DEBRIS_LIFETIME
        self.on_ground = False
        self.damage = damage
        self.alpha = 1.0

    def update(self, dt, world):
        """Update falling block physics. Returns False when dead."""
        self.life -= dt
        if self.life <= 0:
            return False

        self.velocity[1] += GRAVITY * dt
        self.velocity[1] = max(self.velocity[1], -50)

        new_pos = self.pos + self.velocity * dt

        bx = int(math.floor(new_pos[0]))
        by = int(math.floor(new_pos[1]))
        bz = int(math.floor(new_pos[2]))

        block_below = world.get_block(bx, by - 1, bz)
        if block_below in SOLID_BLOCKS or block_below in FLUID_BLOCKS:
            if new_pos[1] < by + 1.0:
                new_pos[1] = by + 1.0
                self.velocity[1] = 0
                self.velocity[0] *= 0.3
                self.velocity[2] *= 0.3
                self.on_ground = True

        block_at = world.get_block(bx, by, bz)
        if block_at in SOLID_BLOCKS and not self.on_ground:
            new_pos[1] = by + 1.1
            self.velocity[1] = abs(self.velocity[1]) * 0.3

        self.pos = new_pos
        self.rotation += self.spin[0] * dt
        self.spin *= 0.98

        if self.life < 0.5:
            self.alpha = self.life / 0.5

        if self.pos[1] < -20:
            return False

        if self.on_ground and abs(self.velocity[1]) < 0.1:
            self.life -= dt * 3

        return True

    def place_if_valid(self, world):
        """Try to place the block in the world. Returns True if placed."""
        bx = int(math.floor(self.pos[0]))
        by = int(math.floor(self.pos[1]))
        bz = int(math.floor(self.pos[2]))
        if 0 <= by < CHUNK_HEIGHT:
            current = world.get_block(bx, by, bz)
            if current == AIR:
                world.set_block(bx, by, bz, self.block_type)
                return True
        return False


class Explosion:
    """Sphere-based explosion that destroys blocks and launches FallingBlocks."""

    def __init__(self, cx, cy, cz, radius=4.0, power=1.0):
        self.cx = cx
        self.cy = cy
        self.cz = cz
        self.radius = radius
        self.power = power
        self.affected_chunks = set()

    def execute(self, world, entity_manager=None):
        """Execute the explosion: destroy blocks, spawn debris, damage entities."""
        r = self.radius
        ir = int(math.ceil(r))
        center = np.array([self.cx + 0.5, self.cy + 0.5, self.cz + 0.5],
                          dtype=np.float64)

        for dx in range(-ir, ir + 1):
            for dy in range(-ir, ir + 1):
                for dz in range(-ir, ir + 1):
                    bx = self.cx + dx
                    by = self.cy + dy
                    bz = self.cz + dz

                    dist = math.sqrt(dx * dx + dy * dy + dz * dz)
                    if dist > r:
                        continue

                    block = world.get_block(bx, by, bz)
                    if block == AIR or block in FLUID_BLOCKS:
                        continue
                    if block in EXPLOSION_RESISTANT:
                        hardness = BLOCK_HARDNESS.get(block, 3.0)
                        if hardness > self.power * (r - dist) * 2:
                            continue

                    strength = (1.0 - dist / r) * self.power
                    hardness = BLOCK_HARDNESS.get(block, 3.0)
                    if hardness > 0 and strength < hardness / 4.0:
                        continue

                    world.set_block(bx, by, bz, AIR)

                    cx, cz = world.world_to_chunk(bx, bz)
                    self.affected_chunks.add((cx, cz))

                    if block != BEDROCK and random.random() < min(1.0, strength * 0.8):
                        outward = np.array([
                            bx + 0.5 - center[0],
                            0.5,
                            bz + 0.5 - center[2]
                        ], dtype=np.float64)
                        norm = np.linalg.norm(outward)
                        if norm > 0.01:
                            outward /= norm
                        else:
                            outward = np.array([0, 1, 0], dtype=np.float64)

                        force = strength * 15.0
                        vel = outward * force + np.array([0, force * 1.2, 0],
                                                        dtype=np.float64)
                        vel += np.array([
                            random.uniform(-1, 1),
                            random.uniform(-1, 1),
                            random.uniform(-1, 1)
                        ], dtype=np.float64)

                        fb = FallingBlock(block, [bx, by + 0.5, bz], vel,
                                         damage=strength * 5.0)
                        entity_manager.falling_blocks.append(fb)

        for cx, cz in self.affected_chunks:
            key = (cx, cz)
            if key in world.chunks:
                world.dirty_chunks.add(key)
            for ddx, ddz in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nkey = (cx + ddx, cz + ddz)
                if nkey in world.chunks:
                    world.dirty_chunks.add(nkey)

        if entity_manager is not None:
            self._damage_entities(entity_manager)

        return len(self.affected_chunks)

    def _damage_entities(self, entity_manager):
        """Apply knockback and damage to entities in explosion radius."""
        center = np.array([self.cx + 0.5, self.cy + 0.5, self.cz + 0.5],
                          dtype=np.float64)
        for entity in entity_manager.entities:
            if entity.dead:
                continue
            diff = entity.pos - center
            dist = np.linalg.norm(diff)
            if dist < self.radius * 2:
                strength = max(0.0, 1.0 - dist / (self.radius * 2))
                entity.take_damage(int(strength * self.power * 20))
                if dist > 0.1:
                    knock = diff / dist * strength * 15
                    knock[1] = max(knock[1], strength * 10)
                    entity.velocity += knock


class FluidSim:
    """Water and lava simulation. BFS-based spreading that fills holes
    like real Minecraft. Time-budgeted for performance."""

    def __init__(self):
        self.water_sources = set()
        self.lava_sources = set()
        self.fluid_tick_timer = 0.0
        self.lava_tick_timer = 0.0
        self.pending_updates = deque()
        self.max_updates_per_tick = 256
        self.dirty_chunks = set()
        self.rain_timer = 0.0

    def add_source(self, x, y, z, block_type):
        """Register a fluid source block."""
        if block_type == WATER:
            self.water_sources.add((x, y, z))
        elif block_type == LAVA:
            self.lava_sources.add((x, y, z))

    def remove_source(self, x, y, z, block_type):
        """Remove a fluid source block."""
        if block_type == WATER:
            self.water_sources.discard((x, y, z))
        elif block_type == LAVA:
            self.lava_sources.discard((x, y, z))

    def update(self, dt, world, wind=None, rain_intensity=0.0, player_pos=None):
        """Time-budgeted fluid simulation update."""
        self.fluid_tick_timer += dt
        self.lava_tick_timer += dt
        self.rain_timer += dt

        if self.fluid_tick_timer >= FLUID_TICK_RATE:
            self.fluid_tick_timer -= FLUID_TICK_RATE
            self._tick_fluid(WATER, world, wind, dt)

        if self.lava_tick_timer >= LAVA_TICK_RATE:
            self.lava_tick_timer -= LAVA_TICK_RATE
            self._tick_fluid(LAVA, world, wind, dt)

        if self.rain_timer >= 2.0 and rain_intensity > 0.5 and player_pos is not None:
            self.rain_timer = 0.0
            self._rain_puddle(world, rain_intensity, player_pos)

        if self.dirty_chunks:
            chunks_copy = self.dirty_chunks.copy()
            self.dirty_chunks.clear()
            return chunks_copy
        return set()

    def _tick_fluid(self, fluid_type, world, wind, dt):
        """Spread a single fluid type. GPU-accelerated BFS when available."""
        from cuda_manager import gpu_fluid_spread_step
        sources = self.water_sources if fluid_type == WATER else self.lava_sources
        spread_max = WATER_SPREAD_MAX if fluid_type == WATER else LAVA_SPREAD_MAX

        sources, dirty = gpu_fluid_spread_step(
            sources, fluid_type, world, spread_max, wind)
        self.dirty_chunks.update(dirty)

    def _rain_puddle(self, world, rain_intensity, player_pos):
        """Place water on exposed surfaces during heavy rain."""
        px, py, pz = int(player_pos[0]), int(player_pos[1]), int(player_pos[2])
        radius = int(rain_intensity * 12)
        placed = 0
        max_places = int(rain_intensity * 4)

        for _ in range(radius * radius * 2):
            if placed >= max_places:
                break
            rx = px + random.randint(-radius, radius)
            rz = pz + random.randint(-radius, radius)

            for y in range(min(CHUNK_HEIGHT - 1, py + 15), max(0, py - 10), -1):
                block = world.get_block(rx, y, rz)
                if block != AIR and block not in FLUID_BLOCKS:
                    if y + 1 < CHUNK_HEIGHT:
                        above = world.get_block(rx, y + 1, rz)
                        if above == AIR:
                            if random.random() < RAIN_PUDDLE_CHANCE * rain_intensity:
                                world.set_block(rx, y + 1, rz, WATER)
                                self.water_sources.add((rx, y + 1, rz))
                                cx, cz = world.world_to_chunk(rx, rz)
                                self.dirty_chunks.add((cx, cz))
                                placed += 1
                    break

    def scan_existing_fluids(self, world, player_cx, player_cz):
        """Scan loaded chunks to find existing water/lava sources."""
        for dx in range(-RENDER_DISTANCE, RENDER_DISTANCE + 1):
            for dz in range(-RENDER_DISTANCE, RENDER_DISTANCE + 1):
                key = (player_cx + dx, player_cz + dz)
                if key not in world.chunks:
                    continue
                chunk = world.chunks[key]
                wx_base = chunk.cx * CHUNK_SIZE
                wz_base = chunk.cz * CHUNK_SIZE
                for x in range(CHUNK_SIZE):
                    for z in range(CHUNK_SIZE):
                        for y in range(CHUNK_HEIGHT):
                            b = chunk.get_block(x, y, z)
                            if b == WATER:
                                self.water_sources.add(
                                    (wx_base + x, y, wz_base + z))
                            elif b == LAVA:
                                self.lava_sources.add(
                                    (wx_base + x, y, wz_base + z))


class WindSystem:
    """Global wind that pushes water and affects particles."""

    def __init__(self):
        self.direction = np.array([1.0, 0.0, 0.0], dtype=np.float64)
        self.speed = 0.0
        self.target_speed = 0.0
        self.target_direction = self.direction.copy()
        self.change_timer = 0.0
        self.change_interval = random.uniform(10, 30)
        self.gust_timer = 0.0
        self.gust_strength = 0.0

    def update(self, dt):
        """Update wind direction and speed."""
        self.change_timer -= dt
        if self.change_timer <= 0:
            self.change_timer = random.uniform(10, 30)
            angle = random.uniform(0, math.pi * 2)
            self.target_direction = np.array([
                math.cos(angle), 0.0, math.sin(angle)
            ], dtype=np.float64)
            self.target_speed = random.uniform(0.5, MAX_WIND_SPEED)

        self.speed += (self.target_speed - self.speed) * dt * WIND_CHANGE_RATE
        dot = np.dot(self.direction, self.target_direction)
        if dot < 0.99:
            axis = np.cross(self.direction, self.target_direction)
            norm = np.linalg.norm(axis)
            if norm > 0.001:
                axis /= norm
                angle = math.acos(max(-1, min(1, dot)))
                rot_angle = min(angle, dt * 0.5)
                cos_a = math.cos(rot_angle)
                sin_a = math.sin(rot_angle)
                self.direction = self.direction * cos_a + np.cross(axis, self.direction) * sin_a + axis * np.dot(axis, self.direction) * (1 - cos_a)
                n = np.linalg.norm(self.direction)
                if n > 0.001:
                    self.direction /= n

        self.gust_timer -= dt
        if self.gust_timer <= 0:
            self.gust_timer = random.uniform(3, 8)
            self.gust_strength = random.uniform(0, self.speed * 0.5)

        self.gust_strength *= 0.95

    def get_force(self):
        """Get current wind force vector."""
        gust = self.gust_strength * self.direction
        return self.direction * self.speed + gust

    def get_horizontal_push(self):
        """Get 2D horizontal push for fluid/water."""
        return self.direction * self.speed

    def apply_to_particle(self, vel, dt):
        """Apply wind force to a particle velocity."""
        push = self.get_force() * dt * 0.3
        vel[0] += push[0]
        vel[2] += push[2]


class BlockGravity:
    """Makes sand/gravel fall when the block beneath is removed.
    Only updates blocks near the player for performance."""

    def __init__(self):
        self.gravity_queue = deque()
        self.processed = set()
        self.timer = 0.0
        self.scan_radius = 16

    def check_area(self, world, player_pos, dt):
        """Periodically scan for unsupported gravity blocks near player."""
        self.timer -= dt
        if self.timer > 0:
            return
        self.timer = 0.2

        px = int(player_pos[0])
        py = int(player_pos[1])
        pz = int(player_pos[2])
        r = self.scan_radius

        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                x = px + dx
                z = pz + dz
                for y in range(py + r, max(0, py - r), -1):
                    block = world.get_block(x, y, z)
                    if block in GRAVITY_BLOCKS:
                        below = world.get_block(x, y - 1, z)
                        if below == AIR or below in FLUID_BLOCKS:
                            key = (x, y, z)
                            if key not in self.processed:
                                self.gravity_queue.append((x, y, z, block))
                                self.processed.add(key)

    def update(self, dt, world, time_budget_ms=2.0):
        """Process gravity blocks with time budget."""
        start = time.monotonic()
        updated = 0

        while self.gravity_queue:
            if (time.monotonic() - start) * 1000 > time_budget_ms:
                break

            x, y, z, block = self.gravity_queue.popleft()
            self.processed.discard((x, y, z))

            current = world.get_block(x, y, z)
            if block is not None and current != block:
                continue
            if current not in GRAVITY_BLOCKS:
                continue
            block = current

            drop_y = y - 1
            while drop_y >= 0:
                below = world.get_block(x, drop_y, z)
                if below != AIR and below not in FLUID_BLOCKS:
                    break
                drop_y -= 1
            drop_y += 1

            if drop_y < y:
                world.set_block(x, y, z, AIR)
                world.set_block(x, drop_y, z, block)
                updated += 1

                cx, cz = world.world_to_chunk(x, z)
                world.dirty_chunks.add((cx, cz))
                for ddx, ddz in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    nkey = (cx + ddx, cz + ddz)
                    if nkey in world.chunks:
                        world.dirty_chunks.add(nkey)

                if drop_y > 0:
                    check_block = world.get_block(x, drop_y - 1, z)
                    if check_block in GRAVITY_BLOCKS:
                        self.gravity_queue.append(
                            (x, drop_y - 1, z, check_block))

        return updated


class PhysicsManager:
    """Master physics controller that coordinates all sub-systems."""

    def __init__(self):
        self.falling_blocks = []
        self.fluid_sim = FluidSim()
        self.wind = WindSystem()
        self.block_gravity = BlockGravity()
        self.explosion_timer = 0.0
        self.initialized = False

    def init(self, world, player_cx, player_cz):
        """Initial scan for existing fluids."""
        if not self.initialized:
            self.fluid_sim.scan_existing_fluids(world, player_cx, player_cz)
            self.initialized = True

    def create_explosion(self, world, cx, cy, cz, radius=4.0, power=1.0, entity_manager=None):
        """Trigger an explosion at the given block coordinates."""
        explosion = Explosion(cx, cy, cz, radius, power)
        chunks_modified = explosion.execute(world, entity_manager)
        return chunks_modified

    def update(self, dt, world, player_pos, day_time, rain_intensity=0.0):
        """Update all physics sub-systems with time budgeting."""
        self.wind.update(dt)

        dirty_chunks = set()

        falling_dead = []
        for i, fb in enumerate(self.falling_blocks):
            if not fb.update(dt, world):
                if fb.life <= 0 and fb.on_ground:
                    fb.place_if_valid(world)
                falling_dead.append(i)
        for i in reversed(falling_dead):
            self.falling_blocks.pop(i)

        fluid_dirty = self.fluid_sim.update(
            dt, world, self.wind, rain_intensity, player_pos)
        dirty_chunks.update(fluid_dirty)

        self.block_gravity.check_area(world, player_pos, dt)
        self.block_gravity.update(dt, world)

        return dirty_chunks

    def trigger_tnt(self, x, y, z, world, entity_manager=None):
        """Trigger a TNT explosion."""
        explosion = Explosion(x, y, z, radius=4.0, power=2.0)
        chunks = explosion.execute(world, entity_manager)
        for cx, cz in chunks:
            world.dirty_chunks.add((cx, cz))
            for ddx, ddz in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nkey = (cx + ddx, cz + ddz)
                if nkey in world.chunks:
                    world.dirty_chunks.add(nkey)
        return chunks

    def on_block_removed(self, x, y, z, block_type):
        """Called when a block is removed. Handles fluid/gravity updates."""
        if block_type == WATER:
            self.fluid_sim.remove_source(x, y, z, WATER)
        elif block_type == LAVA:
            self.fluid_sim.remove_source(x, y, z, LAVA)

        for dy in range(1, 4):
            key = (x, y + dy, z)
            if key not in self.block_gravity.processed:
                check = None
                self.block_gravity.gravity_queue.append(
                    (x, y + dy, z, check))

    def on_block_placed(self, x, y, z, block_type):
        """Called when a block is placed. Handles fluid/gravity triggers."""
        if block_type == WATER:
            self.fluid_sim.add_source(x, y, z, WATER)
            self.fluid_sim.water_sources.add((x, y, z))
        elif block_type == LAVA:
            self.fluid_sim.add_source(x, y, z, LAVA)
            self.fluid_sim.lava_sources.add((x, y, z))
        elif block_type == TNT:
            pass
        elif block_type in GRAVITY_BLOCKS:
            pass
        else:
            for dy in range(1, 4):
                check_y = y + dy
                if check_y < CHUNK_HEIGHT:
                    block_above = None
                    self.block_gravity.gravity_queue.append(
                        (x, check_y, z, None))

"""Pythmc - Natural Disasters System V2.3

15 disasters with biome rules, chain events, and visual effects.

Disasters:
 1. Earthquake    - Cracks terrain, collapses caves, fissures
 2. Tornado       - Spinning funnel picks up blocks + entities
 3. Tsunami        - Massive water wall floods coast
 4. Sandstorm     - Desert: reduces vision, moves sand
 5. Blizzard      - Snow: places snow, freezes water, damages
 6. Volcanic Eruption - Mountains: lava flows + ash
 7. Wildfire      - Forest: spreads through flammable blocks
 8. Whirlpool     - Ocean: spinning water vortex
 9. Meteor Strike  - Sky impact: explosion + crater
10. Sinkhole      - Ground collapses into deep pit
11. Avalanche     - Snow: blocks tumble down mountain
12. Mudslide      - Jungle: dirt flows downhill
13. Ice Storm     - Snow: places ice, damages vegetation
14. Flash Flood   - Plains/Forest: sudden water surge
15. Lightning Barrage - Multiple rapid strikes

Chain Events:
  Earthquake -> Tsunami (near water)
  Earthquake -> Sinkhole (plains)
  Earthquake -> Avalanche (snow mountains)
  Lightning  -> Wildfire (forest)
  Meteor     -> Wildfire (forest)
  Heavy Rain -> Flash Flood (low ground)
"""

import math
import random
import numpy as np
from noise import pnoise2
from constants import *


def get_biome(wx, wz, seed):
    """Determine biome at world coordinates using same noise as terrain gen."""
    biome_noise1 = pnoise2(wx * 0.002, wz * 0.002, octaves=2, base=seed + 500)
    biome_noise2 = pnoise2(wx * 0.003, wz * 0.003, octaves=2, base=seed + 600)
    biome_noise3 = pnoise2(wx * 0.0015, wz * 0.0015, octaves=2, base=seed + 700)

    if biome_noise3 < -0.25:
        return "ocean"
    elif biome_noise1 > 0.15 and biome_noise2 < 0.0:
        return "desert"
    elif biome_noise1 < -0.2:
        return "snow"
    elif biome_noise2 > 0.15:
        return "forest"
    elif biome_noise1 > 0.05 and biome_noise2 > 0.05:
        return "jungle"
    return "plains"


# ─── Base Disaster ───────────────────────────────────────────────────────────

class Disaster:
    """Base class for all natural disasters."""
    name = "disaster"
    biome_specific = []
    min_duration = 5.0
    max_duration = 30.0
    probability = 0.01
    can_chain = False
    screen_shake = 0.0

    def __init__(self, world, player_pos, seed):
        self.world = world
        self.seed = seed
        self.pos = np.array(player_pos, dtype=np.float64)
        self.timer = random.uniform(self.min_duration, self.max_duration)
        self.active = True
        self.started = False
        self.ended = False
        self.intensity = 0.0
        self.rng = random.Random(seed + int(self.pos[0]) + int(self.pos[2]))
        self.affected_chunks = set()
        self.damage_timer = 0.0

    def start(self):
        self.started = True
        return self

    def update(self, dt, player_pos):
        if not self.active:
            return
        self.timer -= dt
        if self.timer <= 0:
            self.active = False
            self.ended = True
        self.pos = np.array(player_pos, dtype=np.float64)

    def end(self):
        self.active = False
        self.ended = True

    def get_screen_shake(self):
        return self.screen_shake * self.intensity

    def get_chain_events(self):
        return []

    def apply_chunk_dirtying(self):
        for cx, cz in self.affected_chunks:
            key = (cx, cz)
            if key in self.world.chunks:
                self.world.dirty_chunks.add(key)
            for ddx, ddz in [(1,0),(-1,0),(0,1),(0,-1)]:
                nkey = (cx+ddx, cz+ddz)
                if nkey in self.world.chunks:
                    self.world.dirty_chunks.add(nkey)
        self.affected_chunks.clear()


# ─── 1. Earthquake ──────────────────────────────────────────────────────────

class Earthquake(Disaster):
    name = "Earthquake"
    probability = 0.005
    min_duration = 8.0
    max_duration = 15.0
    screen_shake = 12.0
    can_chain = True

    def start(self):
        super().start()
        self.rumble_phase = 0.0
        self.crack_timer = 0.0
        return self

    def update(self, dt, player_pos):
        super().update(dt, player_pos)
        self.intensity = min(1.0, self.timer / 3.0)
        self.rumble_phase += dt * 15
        self.crack_timer -= dt

        if self.crack_timer <= 0:
            self.crack_timer = 0.3
            self._crack_terrain()

    def _crack_terrain(self):
        px, pz = int(self.pos[0]), int(self.pos[2])
        radius = 20
        for _ in range(5):
            dx = self.rng.randint(-radius, radius)
            dz = self.rng.randint(-radius, radius)
            x, z = px + dx, pz + dz
            for y in range(int(self.pos[1]) + 10, 0, -1):
                b = self.world.get_block(x, y, z)
                if b != AIR and b not in FLUID_BLOCKS:
                    if self.rng.random() < 0.3:
                        hardness = BLOCK_HARDNESS.get(b, 3.0)
                        if hardness < 4.0:
                            self.world.set_block(x, y, z, AIR)
                            cx, cz = self.world.world_to_chunk(x, z)
                            self.affected_chunks.add((cx, cz))
                    break

        fissure_x = px + self.rng.randint(-15, 15)
        fissure_z = pz + self.rng.randint(-15, 15)
        for step in range(10):
            fx = fissure_x + self.rng.randint(-2, 2)
            fz = fissure_z + step
            for y in range(int(self.pos[1]) + 5, max(0, int(self.pos[1]) - 5), -1):
                b = self.world.get_block(fx, y, fz)
                if b not in (AIR, WATER, LAVA, BEDROCK):
                    self.world.set_block(fx, y, fz, AIR)
                    cx, cz = self.world.world_to_chunk(fx, fz)
                    self.affected_chunks.add((cx, cz))
                    break

        self.apply_chunk_dirtying()

    def get_chain_events(self):
        if self.timer < 2.0:
            biome = get_biome(int(self.pos[0]), int(self.pos[2]), self.seed)
            chains = []
            if biome in ("ocean",) or self._near_water():
                if self.rng.random() < 0.35:
                    chains.append(("tsunami", [float(self.pos[0]), float(self.pos[1]), float(self.pos[2])]))
            if biome == "plains":
                if self.rng.random() < 0.2:
                    chains.append(("sinkhole", [float(self.pos[0]), float(self.pos[1]), float(self.pos[2])]))
            if biome == "snow":
                if self.rng.random() < 0.25:
                    chains.append(("avalanche", [float(self.pos[0]), float(self.pos[1]), float(self.pos[2])]))
            if biome in ("mountain", "desert", "snow"):
                if self.rng.random() < 0.1:
                    chains.append(("volcanic", [float(self.pos[0]), float(self.pos[1]), float(self.pos[2])]))
            return chains
        return []

    def _near_water(self):
        px, pz = int(self.pos[0]), int(self.pos[2])
        for dx in range(-10, 11, 2):
            for dz in range(-10, 11, 2):
                for y in range(30, 0, -1):
                    b = self.world.get_block(px+dx, y, pz+dz)
                    if b == WATER:
                        return True
                    if b not in (AIR, WATER):
                        break
        return False


# ─── 2. Tornado ─────────────────────────────────────────────────────────────

class Tornado(Disaster):
    name = "Tornado"
    probability = 0.004
    min_duration = 15.0
    max_duration = 30.0
    screen_shake = 6.0

    def start(self):
        super().start()
        angle = self.rng.uniform(0, math.pi * 2)
        self.move_dir = np.array([math.cos(angle), 0, math.sin(angle)], dtype=np.float64)
        self.move_speed = self.rng.uniform(3.0, 6.0)
        self.center = np.array([
            self.pos[0] + self.rng.randint(-20, 20),
            0,
            self.pos[2] + self.rng.randint(-20, 20)
        ], dtype=np.float64)
        self.radius = 4.0
        self.suck_timer = 0.0
        self.flying_blocks = []
        return self

    def update(self, dt, player_pos):
        super().update(dt, player_pos)
        self.intensity = min(1.0, self.timer / 5.0) * min(1.0, (self.max_duration - self.timer) / 3.0)
        self.center += self.move_dir * self.move_speed * dt
        self.suck_timer -= dt

        if self.suck_timer <= 0:
            self.suck_timer = 0.15
            self._suck_blocks()

        alive = []
        for fb in self.flying_blocks:
            fb[0] += fb[1] * dt
            fb[1][1] += 2.0 * dt
            fb[2] -= dt
            if fb[2] > 0:
                alive.append(fb)
        self.flying_blocks = alive

        dist_to_tornado = math.sqrt(
            (self.pos[0] - self.center[0])**2 +
            (self.pos[2] - self.center[2])**2
        )
        if dist_to_tornado < self.radius:
            self.screen_shake = 4.0
        else:
            self.screen_shake = 0.0

    def _suck_blocks(self):
        cx, cy, cz = int(self.center[0]), 1, int(self.center[2])
        for _ in range(3):
            dx = self.rng.randint(-int(self.radius), int(self.radius))
            dz = self.rng.randint(-int(self.radius), int(self.radius))
            bx, bz = cx + dx, cz + dz
            for y in range(CHUNK_HEIGHT - 1, 0, -1):
                b = self.world.get_block(bx, y, bz)
                if b not in (AIR, WATER, LAVA, BEDROCK):
                    hardness = BLOCK_HARDNESS.get(b, 3.0)
                    if hardness < 3.0:
                        self.world.set_block(bx, y, bz, AIR)
                        vel = [
                            self.move_dir[0] * 2 + self.rng.uniform(-1, 1),
                            self.rng.uniform(3, 8),
                            self.move_dir[2] * 2 + self.rng.uniform(-1, 1)
                        ]
                        self.flying_blocks.append([
                            [bx + 0.5, y + 0.5, bz + 0.5],
                            vel,
                            self.rng.uniform(2, 5),
                            b
                        ])
                        cx2, cz2 = self.world.world_to_chunk(bx, bz)
                        self.affected_chunks.add((cx2, cz2))
                    break
        self.apply_chunk_dirtying()


# ─── 3. Tsunami ─────────────────────────────────────────────────────────────

class Tsunami(Disaster):
    name = "Tsunami"
    probability = 0.003
    min_duration = 10.0
    max_duration = 20.0
    screen_shake = 4.0

    def start(self):
        super().start()
        angle = self.rng.uniform(0, math.pi * 2)
        self.direction = np.array([math.cos(angle), 0, math.sin(angle)], dtype=np.float64)
        self.wave_pos = np.array(self.pos, dtype=np.float64) - self.direction * 30
        self.wave_speed = 8.0
        self.wave_width = 15
        self.wave_height = 8
        self.flooded = []
        self.phase = 0
        self.place_timer = 0.0
        return self

    def update(self, dt, player_pos):
        super().update(dt, player_pos)
        self.intensity = min(1.0, self.timer / 3.0)
        self.wave_pos += self.direction * self.wave_speed * dt
        self.phase += dt * 2

        self.place_timer -= dt

        if self.place_timer <= 0:
            self.place_timer = 0.1
            px, pz = int(self.wave_pos[0]), int(self.wave_pos[2])
            placed = 0
            for dx in range(-self.wave_width, self.wave_width + 1):
                bx = px + dx
                bz = pz + self.rng.randint(-2, 2)
                for y in range(self.wave_height, 0, -1):
                    b = self.world.get_block(bx, y, bz)
                    if b == AIR:
                        self.world.set_block(bx, y, bz, WATER)
                        self.flooded.append((bx, y, bz))
                        cx, cz = self.world.world_to_chunk(bx, bz)
                        self.affected_chunks.add((cx, cz))
                        placed += 1
                        break
                    elif b in SOLID_BLOCKS:
                        break
                if placed >= 15:
                    break

            self.apply_chunk_dirtying()

        if self.timer < self.max_duration * 0.3:
            if self.place_timer <= 0:
                self.place_timer = 0.1
                for bx, by, bz in self.flooded[-50:]:
                    self.world.set_block(bx, by, bz, AIR)
                    cx, cz = self.world.world_to_chunk(bx, bz)
                    self.affected_chunks.add((cx, cz))
                self.apply_chunk_dirtying()


# ─── 4. Sandstorm ───────────────────────────────────────────────────────────

class Sandstorm(Disaster):
    name = "Sandstorm"
    probability = 0.008
    min_duration = 20.0
    max_duration = 45.0
    screen_shake = 1.5

    def start(self):
        super().start()
        self.move_timer = 0.0
        self.damage_timer = 0.0
        return self

    def update(self, dt, player_pos):
        super().update(dt, player_pos)
        self.intensity = min(1.0, self.timer / 5.0)
        self.move_timer -= dt
        self.damage_timer -= dt

        if self.damage_timer <= 0:
            self.damage_timer = 2.0
            dist = 0
            if hasattr(self, '_player_ref'):
                dist = np.linalg.norm(self.pos - self._player_ref)

        if self.move_timer <= 0:
            self.move_timer = 0.5
            px, pz = int(self.pos[0]), int(self.pos[2])
            for _ in range(3):
                dx = self.rng.randint(-8, 8)
                dz = self.rng.randint(-8, 8)
                bx, bz = px + dx, pz + dz
                for y in range(30, 0, -1):
                    b = self.world.get_block(bx, y, bz)
                    if b == SAND:
                        if self.rng.random() < 0.1:
                            self.world.set_block(bx, y, bz, AIR)
                            ny = y + self.rng.randint(1, 4)
                            nz = bz + self.rng.randint(-3, 3)
                            nx = bx + self.rng.randint(-3, 3)
                            if self.world.get_block(nx, ny, nz) == AIR:
                                self.world.set_block(nx, ny, nz, SAND)
                                cx, cz = self.world.world_to_chunk(nx, nz)
                                self.affected_chunks.add((cx, cz))
                        break
                    elif b not in (AIR, WATER):
                        break
            self.apply_chunk_dirtying()


# ─── 5. Blizzard ────────────────────────────────────────────────────────────

class Blizzard(Disaster):
    name = "Blizzard"
    probability = 0.006
    min_duration = 25.0
    max_duration = 50.0
    screen_shake = 2.0

    def start(self):
        super().start()
        self.place_timer = 0.0
        return self

    def update(self, dt, player_pos):
        super().update(dt, player_pos)
        self.intensity = min(1.0, self.timer / 5.0)
        self.place_timer -= dt

        if self.place_timer <= 0:
            self.place_timer = 0.2
            px, pz = int(self.pos[0]), int(self.pos[2])
            for _ in range(4):
                dx = self.rng.randint(-12, 12)
                dz = self.rng.randint(-12, 12)
                bx, bz = px + dx, pz + dz
                for y in range(30, 0, -1):
                    b = self.world.get_block(bx, y, bz)
                    if b not in (AIR, WATER, LAVA):
                        above = self.world.get_block(bx, y + 1, bz)
                        if above == AIR and y + 1 < CHUNK_HEIGHT:
                            if self.rng.random() < 0.2:
                                self.world.set_block(bx, y + 1, bz, SNOW)
                                cx, cz = self.world.world_to_chunk(bx, bz)
                                self.affected_chunks.add((cx, cz))
                        if b == WATER:
                            if self.rng.random() < 0.05:
                                self.world.set_block(bx, y, bz, GLASS)
                                cx, cz = self.world.world_to_chunk(bx, bz)
                                self.affected_chunks.add((cx, cz))
                        break
            self.apply_chunk_dirtying()


# ─── 6. Volcanic Eruption ───────────────────────────────────────────────────

class VolcanicEruption(Disaster):
    name = "Volcanic Eruption"
    probability = 0.002
    min_duration = 15.0
    max_duration = 30.0
    screen_shake = 8.0
    can_chain = True

    def start(self):
        super().start()
        self.lava_timer = 0.0
        self.erupt_point = np.array([
            self.pos[0] + self.rng.randint(-10, 10),
            0,
            self.pos[2] + self.rng.randint(-10, 10)
        ], dtype=np.float64)
        for y in range(CHUNK_HEIGHT - 1, 0, -1):
            b = self.world.get_block(int(self.erupt_point[0]), y, int(self.erupt_point[2]))
            if b not in (AIR, WATER):
                self.erupt_point[1] = y + 1
                break
        return self

    def update(self, dt, player_pos):
        super().update(dt, player_pos)
        self.intensity = min(1.0, self.timer / 3.0)
        self.lava_timer -= dt

        if self.lava_timer <= 0:
            self.lava_timer = 0.4
            self._erupt()

    def _erupt(self):
        px, py, pz = int(self.erupt_point[0]), int(self.erupt_point[1]), int(self.erupt_point[2])
        for _ in range(3):
            dx = self.rng.randint(-2, 2)
            dz = self.rng.randint(-2, 2)
            for dy in range(0, 6):
                bx, by, bz = px + dx, py + dy, pz + dz
                b = self.world.get_block(bx, by, bz)
                if b in SOLID_BLOCKS:
                    self.world.set_block(bx, by, bz, AIR)
                if by < CHUNK_HEIGHT:
                    self.world.set_block(bx, by, bz, LAVA)
                cx, cz = self.world.world_to_chunk(bx, bz)
                self.affected_chunks.add((cx, cz))

        for _ in range(2):
            dx = self.rng.randint(-1, 1)
            dz = self.rng.randint(-1, 1)
            flow_x, flow_z = px + dx, pz + dz
            for dist in range(1, 8):
                fx = flow_x + int(self.rng.choice([-1, 0, 1])) * dist
                fz = flow_z + int(self.rng.choice([-1, 0, 1])) * dist
                for y in range(py, 0, -1):
                    b = self.world.get_block(fx, y, fz)
                    if b == AIR:
                        self.world.set_block(fx, y, fz, LAVA)
                        cx, cz = self.world.world_to_chunk(fx, fz)
                        self.affected_chunks.add((cx, cz))
                        break
                    elif b not in (WATER, LAVA):
                        break
        self.apply_chunk_dirtying()


# ─── 7. Wildfire ────────────────────────────────────────────────────────────

class Wildfire(Disaster):
    name = "Wildfire"
    probability = 0.004
    min_duration = 20.0
    max_duration = 40.0
    screen_shake = 1.0

    def start(self):
        super().start()
        self.burn_timer = 0.0
        self.fire_spread = []
        px, pz = int(self.pos[0]), int(self.pos[2])
        for _ in range(5):
            dx = self.rng.randint(-10, 10)
            dz = self.rng.randint(-10, 10)
            bx, bz = px + dx, pz + dz
            for y in range(30, 0, -1):
                b = self.world.get_block(bx, y, bz)
                if b in (WOOD, LEAVES, PLANKS):
                    self.fire_spread.append((bx, y, bz))
                    break
                elif b not in (AIR, WATER):
                    break
        return self

    def update(self, dt, player_pos):
        super().update(dt, player_pos)
        self.intensity = min(1.0, self.timer / 5.0)
        self.burn_timer -= dt

        if self.burn_timer <= 0:
            self.burn_timer = 0.5
            new_fires = []
            for bx, by, bz in self.fire_spread:
                b = self.world.get_block(bx, by, bz)
                if b in (WOOD, LEAVES, PLANKS):
                    if self.rng.random() < 0.3:
                        self.world.set_block(bx, by, bz, AIR)
                        cx, cz = self.world.world_to_chunk(bx, bz)
                        self.affected_chunks.add((cx, cz))

                for dx, dy, dz in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]:
                    nx, ny, nz = bx+dx, by+dy, bz+dz
                    if 0 <= ny < CHUNK_HEIGHT:
                        nb = self.world.get_block(nx, ny, nz)
                        if nb in (WOOD, LEAVES, PLANKS):
                            if self.rng.random() < 0.15:
                                new_fires.append((nx, ny, nz))
            if new_fires:
                self.fire_spread.extend(new_fires)
            if len(self.fire_spread) > 200:
                self.fire_spread = self.fire_spread[-200:]
            self.apply_chunk_dirtying()


# ─── 8. Whirlpool ───────────────────────────────────────────────────────────

class Whirlpool(Disaster):
    name = "Whirlpool"
    probability = 0.003
    min_duration = 12.0
    max_duration = 20.0
    screen_shake = 3.0

    def start(self):
        super().start()
        self.angle = 0.0
        self.center = np.array([
            self.pos[0] + self.rng.randint(-5, 5),
            0,
            self.pos[2] + self.rng.randint(-5, 5)
        ], dtype=np.float64)
        for y in range(30, 0, -1):
            b = self.world.get_block(int(self.center[0]), y, int(self.center[2]))
            if b == WATER:
                self.center[1] = y
                break
            elif b not in (AIR, WATER):
                self.center[1] = y
                break
        return self

    def update(self, dt, player_pos):
        super().update(dt, player_pos)
        self.intensity = min(1.0, self.timer / 3.0)
        self.angle += dt * 4

        cx, cy, cz = int(self.center[0]), int(self.center[1]), int(self.center[2])
        for r in range(1, 6):
            for a in range(8):
                angle = self.angle + a * math.pi / 4
                bx = cx + int(math.cos(angle) * r)
                bz = cz + int(math.sin(angle) * r)
                b = self.world.get_block(bx, cy, bz)
                if b == WATER:
                    if self.rng.random() < 0.1:
                        self.world.set_block(bx, cy, bz, AIR)
                        cx2, cz2 = self.world.world_to_chunk(bx, bz)
                        self.affected_chunks.add((cx2, cz2))
                elif b == AIR:
                    if self.rng.random() < 0.05:
                        self.world.set_block(bx, cy, bz, WATER)
                        cx2, cz2 = self.world.world_to_chunk(bx, bz)
                        self.affected_chunks.add((cx2, cz2))
        self.apply_chunk_dirtying()


# ─── 9. Meteor Strike ───────────────────────────────────────────────────────

class MeteorStrike(Disaster):
    name = "Meteor Strike"
    probability = 0.002
    min_duration = 5.0
    max_duration = 8.0
    screen_shake = 15.0
    can_chain = True

    def start(self):
        super().start()
        self.impact_x = self.pos[0] + self.rng.uniform(-20, 20)
        self.impact_z = self.pos[2] + self.rng.uniform(-20, 20)
        self.impacted = False
        self.impact_timer = 1.5
        self.meteor_y = 50.0
        self.crater_radius = self.rng.randint(4, 7)
        return self

    def update(self, dt, player_pos):
        super().update(dt, player_pos)
        self.intensity = 1.0
        self.impact_timer -= dt

        if not self.impacted and self.impact_timer <= 0:
            self.impacted = True
            self._explode()

    def _explode(self):
        ix, iz = int(self.impact_x), int(self.impact_z)
        for dy in range(CHUNK_HEIGHT - 1, 0, -1):
            b = self.world.get_block(ix, dy, iz)
            if b not in (AIR, WATER, LAVA):
                iy = dy + 1
                break
        else:
            iy = 20

        for dx in range(-self.crater_radius, self.crater_radius + 1):
            for dz in range(-self.crater_radius, self.crater_radius + 1):
                dist = math.sqrt(dx*dx + dz*dz)
                if dist > self.crater_radius:
                    continue
                for dy in range(0, int(dist + 3)):
                    bx, by, bz = ix + dx, iy + dy, iz + dz
                    if 0 <= by < CHUNK_HEIGHT:
                        b = self.world.get_block(bx, by, bz)
                        if b not in (BEDROCK, AIR):
                            self.world.set_block(bx, by, bz, AIR)
                            cx, cz = self.world.world_to_chunk(bx, bz)
                            self.affected_chunks.add((cx, cz))
                depth = int((self.crater_radius - dist) * 0.5)
                for dy in range(1, depth + 1):
                    bx, by, bz = ix + dx, iy - dy, iz + dz
                    if 0 <= by < CHUNK_HEIGHT:
                        self.world.set_block(bx, by, bz, AIR)
                        cx, cz = self.world.world_to_chunk(bx, bz)
                        self.affected_chunks.add((cx, cz))

        for _ in range(3):
            bx = ix + self.rng.randint(-2, 2)
            bz = iz + self.rng.randint(-2, 2)
            for y in range(iy, 0, -1):
                if self.world.get_block(bx, y, bz) in SOLID_BLOCKS:
                    self.world.set_block(bx, y + 1, bz, LAVA)
                    break

        self.apply_chunk_dirtying()

    def get_chain_events(self):
        if self.impacted:
            biome = get_biome(int(self.impact_x), int(self.impact_z), self.seed)
            if biome == "forest" and self.rng.random() < 0.6:
                return [("wildfire", {"x": self.impact_x, "y": 20.0, "z": self.impact_z})]
            if biome in ("mountain", "desert") and self.rng.random() < 0.2:
                return [("volcanic", {"x": self.impact_x, "y": 20.0, "z": self.impact_z})]
        return []


# ─── 10. Sinkhole ───────────────────────────────────────────────────────────

class Sinkhole(Disaster):
    name = "Sinkhole"
    probability = 0.003
    min_duration = 10.0
    max_duration = 18.0
    screen_shake = 5.0

    def start(self):
        super().start()
        self.cx = int(self.pos[0]) + self.rng.randint(-5, 5)
        self.cz = int(self.pos[2]) + self.rng.randint(-5, 5)
        self.sink_radius = 0.0
        self.max_radius = self.rng.uniform(5.0, 10.0)
        self.grow_rate = self.max_radius / (self.max_duration * 0.7)
        self.dig_timer = 0.0
        self.dig_positions = []
        self._rebuild_dig_queue()
        return self

    def _rebuild_dig_queue(self):
        self.dig_positions = []
        r = int(self.sink_radius) + 1
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                dist = math.sqrt(dx*dx + dz*dz)
                if dist <= self.sink_radius:
                    self.dig_positions.append((dx, dz, dist))
        self.rng.shuffle(self.dig_positions)

    def update(self, dt, player_pos):
        super().update(dt, player_pos)
        self.intensity = min(1.0, self.timer / 3.0)

        if self.sink_radius < self.max_radius:
            self.sink_radius += self.grow_rate * dt
            self._rebuild_dig_queue()

        self.dig_timer -= dt
        if self.dig_timer <= 0:
            self.dig_timer = 0.15
            placed = 0
            for dx, dz, dist in self.dig_positions:
                bx, bz = self.cx + dx, self.cz + dz
                for y in range(40, 0, -1):
                    b = self.world.get_block(bx, y, bz)
                    if b not in (AIR, WATER, LAVA, BEDROCK):
                        depth = int((self.sink_radius - dist) * 0.4)
                        for remove_y in range(y, max(0, y - depth) - 1, -1):
                            rb = self.world.get_block(bx, remove_y, bz)
                            if rb not in (BEDROCK,):
                                self.world.set_block(bx, remove_y, bz, AIR)
                                cx2, cz2 = self.world.world_to_chunk(bx, bz)
                                self.affected_chunks.add((cx2, cz2))
                                placed += 1
                        break
                if placed >= 15:
                    break
            self.apply_chunk_dirtying()


# ─── 11. Avalanche ──────────────────────────────────────────────────────────

class Avalanche(Disaster):
    name = "Avalanche"
    probability = 0.004
    min_duration = 8.0
    max_duration = 15.0
    screen_shake = 6.0

    def start(self):
        super().start()
        self.slide_blocks = []
        self.slide_timer = 0.0
        px, pz = int(self.pos[0]), int(self.pos[2])
        for y in range(40, 10, -1):
            for dx in range(-5, 6):
                b = self.world.get_block(px + dx, y, pz)
                if b in (SNOW, STONE, DIRT, COBBLESTONE):
                    self.slide_blocks.append((px + dx, y, pz, b))
                    break
        return self

    def update(self, dt, player_pos):
        super().update(dt, player_pos)
        self.intensity = min(1.0, self.timer / 3.0)
        self.slide_timer -= dt

        if self.slide_timer <= 0:
            self.slide_timer = 0.1
            new_slide = []
            for bx, by, bz, block in self.slide_blocks:
                b = self.world.get_block(bx, by, bz)
                if b == block:
                    self.world.set_block(bx, by, bz, AIR)
                    cx, cz = self.world.world_to_chunk(bx, bz)
                    self.affected_chunks.add((cx, cz))

                    nz = bz + self.rng.randint(1, 3)
                    for down_y in range(by, 0, -1):
                        below = self.world.get_block(bx, down_y - 1, nz)
                        if below in SOLID_BLOCKS:
                            if down_y < CHUNK_HEIGHT:
                                self.world.set_block(bx, down_y, nz, block)
                                cx2, cz2 = self.world.world_to_chunk(bx, nz)
                                self.affected_chunks.add((cx2, cz2))
                                if by + 1 < CHUNK_HEIGHT:
                                    above = self.world.get_block(bx, by + 1, bz)
                                    if above in (SNOW, STONE, DIRT, GRAVEL):
                                        new_slide.append((bx, by + 1, bz, above))
                            break
                        elif below == AIR:
                            continue
                        else:
                            break
            self.slide_blocks = new_slide
            self.apply_chunk_dirtying()


# ─── 12. Mudslide ───────────────────────────────────────────────────────────

class Mudslide(Disaster):
    name = "Mudslide"
    probability = 0.004
    min_duration = 10.0
    max_duration = 18.0
    screen_shake = 4.0

    def start(self):
        super().start()
        self.flow_blocks = []
        self.flow_timer = 0.0
        px, pz = int(self.pos[0]), int(self.pos[2])
        for y in range(35, 10, -1):
            for dx in range(-4, 5):
                b = self.world.get_block(px + dx, y, pz)
                if b in (DIRT, SAND, GRAVEL, CLAY):
                    self.flow_blocks.append((px + dx, y, pz, b))
                    break
        return self

    def update(self, dt, player_pos):
        super().update(dt, player_pos)
        self.intensity = min(1.0, self.timer / 3.0)
        self.flow_timer -= dt

        if self.flow_timer <= 0:
            self.flow_timer = 0.15
            new_flow = []
            for bx, by, bz, block in self.flow_blocks:
                b = self.world.get_block(bx, by, bz)
                if b == block:
                    self.world.set_block(bx, by, bz, AIR)
                    cx, cz = self.world.world_to_chunk(bx, bz)
                    self.affected_chunks.add((cx, cz))

                    dx = self.rng.choice([-1, 0, 1])
                    dz = self.rng.randint(1, 2)
                    nx, nz = bx + dx, bz + dz
                    for down_y in range(by, 0, -1):
                        below = self.world.get_block(nx, down_y - 1, nz)
                        if below in SOLID_BLOCKS:
                            if down_y < CHUNK_HEIGHT:
                                self.world.set_block(nx, down_y, nz, block)
                                cx2, cz2 = self.world.world_to_chunk(nx, nz)
                                self.affected_chunks.add((cx2, cz2))
                                if by + 1 < CHUNK_HEIGHT:
                                    above = self.world.get_block(bx, by + 1, bz)
                                    if above in (DIRT, SAND, GRAVEL, CLAY):
                                        new_flow.append((bx, by + 1, bz, above))
                            break
                        elif below in (AIR, WATER):
                            continue
                        else:
                            break
            self.flow_blocks = new_flow
            self.apply_chunk_dirtying()


# ─── 13. Ice Storm ──────────────────────────────────────────────────────────

class IceStorm(Disaster):
    name = "Ice Storm"
    probability = 0.004
    min_duration = 15.0
    max_duration = 30.0
    screen_shake = 1.0

    def start(self):
        super().start()
        self.freeze_timer = 0.0
        return self

    def update(self, dt, player_pos):
        super().update(dt, player_pos)
        self.intensity = min(1.0, self.timer / 4.0)
        self.freeze_timer -= dt

        if self.freeze_timer <= 0:
            self.freeze_timer = 0.3
            px, pz = int(self.pos[0]), int(self.pos[2])
            for _ in range(5):
                dx = self.rng.randint(-10, 10)
                dz = self.rng.randint(-10, 10)
                bx, bz = px + dx, pz + dz
                for y in range(30, 0, -1):
                    b = self.world.get_block(bx, y, bz)
                    if b == LEAVES:
                        if self.rng.random() < 0.15:
                            self.world.set_block(bx, y, bz, AIR)
                            cx, cz = self.world.world_to_chunk(bx, bz)
                            self.affected_chunks.add((cx, cz))
                    elif b not in (AIR, WATER, LAVA):
                        above = self.world.get_block(bx, y + 1, bz)
                        if above == AIR and y + 1 < CHUNK_HEIGHT:
                            if self.rng.random() < 0.08:
                                self.world.set_block(bx, y + 1, bz, GLASS)
                                cx, cz = self.world.world_to_chunk(bx, bz)
                                self.affected_chunks.add((cx, cz))
                        break
            self.apply_chunk_dirtying()


# ─── 14. Flash Flood ────────────────────────────────────────────────────────

class FlashFlood(Disaster):
    name = "Flash Flood"
    probability = 0.005
    min_duration = 8.0
    max_duration = 15.0
    screen_shake = 3.0

    def start(self):
        super().start()
        angle = self.rng.uniform(0, math.pi * 2)
        self.direction = np.array([math.cos(angle), 0, math.sin(angle)])
        self.wave_x = self.pos[0] - self.direction[0] * 20
        self.wave_z = self.pos[2] - self.direction[2] * 20
        self.wave_speed = 5.0
        self.wave_width = 10
        self.flooded = []
        self.receding = False
        self.place_timer = 0.0
        return self

    def update(self, dt, player_pos):
        super().update(dt, player_pos)
        self.intensity = min(1.0, self.timer / 2.0)

        self.place_timer -= dt

        if not self.receding:
            self.wave_x += self.direction[0] * self.wave_speed * dt
            self.wave_z += self.direction[2] * self.wave_speed * dt

            if self.place_timer <= 0:
                self.place_timer = 0.1
                wx, wz = int(self.wave_x), int(self.wave_z)
                placed = 0
                for dx in range(-self.wave_width, self.wave_width + 1):
                    bx = wx + dx
                    bz = wz + self.rng.randint(-2, 2)
                    for y in range(25, 0, -1):
                        b = self.world.get_block(bx, y, bz)
                        if b == AIR:
                            self.world.set_block(bx, y, bz, WATER)
                            self.flooded.append((bx, y, bz))
                            cx, cz = self.world.world_to_chunk(bx, bz)
                            self.affected_chunks.add((cx, cz))
                            placed += 1
                            break
                        elif b in SOLID_BLOCKS:
                            break
                    if placed >= 12:
                        break

        if self.timer < self.max_duration * 0.4:
            self.receding = True
            if self.place_timer <= 0:
                self.place_timer = 0.1
                for bx, by, bz in self.flooded[-30:]:
                    self.world.set_block(bx, by, bz, AIR)
                    cx, cz = self.world.world_to_chunk(bx, bz)
                    self.affected_chunks.add((cx, cz))

        self.apply_chunk_dirtying()


# ─── 15. Lightning Barrage ──────────────────────────────────────────────────

class LightningBarrage(Disaster):
    name = "Lightning Barrage"
    probability = 0.005
    min_duration = 5.0
    max_duration = 12.0
    screen_shake = 8.0
    can_chain = True

    def start(self):
        super().start()
        self.strike_timer = 0.0
        self.flash_timer = 0.0
        self.flash_intensity = 0.0
        self.strikes = []
        return self

    def update(self, dt, player_pos):
        super().update(dt, player_pos)
        self.intensity = min(1.0, self.timer / 3.0)
        self.strike_timer -= dt
        self.flash_timer -= dt

        if self.flash_timer > 0:
            self.flash_intensity = self.flash_timer / 0.3
        else:
            self.flash_intensity = 0.0

        if self.strike_timer <= 0:
            self.strike_timer = self.rng.uniform(0.3, 1.0)
            self._strike()

    def _strike(self):
        sx = int(self.pos[0]) + self.rng.randint(-15, 15)
        sz = int(self.pos[2]) + self.rng.randint(-15, 15)
        hit_y = None
        for y in range(CHUNK_HEIGHT - 1, 0, -1):
            b = self.world.get_block(sx, y, sz)
            if b not in (AIR, WATER, LAVA):
                hit_y = y
                break

        self.flash_timer = 0.3
        self.strikes.append([sx, hit_y if hit_y else 20, sz, 0.3])

        if hit_y:
            b = self.world.get_block(sx, hit_y, sz)
            if b == WOOD or b == LEAVES:
                self.world.set_block(sx, hit_y, sz, AIR)
                cx, cz = self.world.world_to_chunk(sx, sz)
                self.affected_chunks.add((cx, cz))
            if b in SOLID_BLOCKS:
                hardness = BLOCK_HARDNESS.get(b, 3.0)
                if hardness < 2.0:
                    self.world.set_block(sx, hit_y, sz, AIR)
                    cx, cz = self.world.world_to_chunk(sx, sz)
                    self.affected_chunks.add((cx, cz))

        self.apply_chunk_dirtying()

    def get_chain_events(self):
        if self.timer < 1.0:
            biome = get_biome(int(self.pos[0]), int(self.pos[2]), self.seed)
            if biome == "forest" and self.rng.random() < 0.4:
                return [("wildfire", dict(self.pos))]
        return []


# ─── Disaster Manager ───────────────────────────────────────────────────────

DISASTER_CLASSES = {
    "earthquake": Earthquake,
    "tornado": Tornado,
    "tsunami": Tsunami,
    "sandstorm": Sandstorm,
    "blizzard": Blizzard,
    "volcanic": VolcanicEruption,
    "wildfire": Wildfire,
    "whirlpool": Whirlpool,
    "meteor": MeteorStrike,
    "sinkhole": Sinkhole,
    "avalanche": Avalanche,
    "mudslide": Mudslide,
    "ice_storm": IceStorm,
    "flash_flood": FlashFlood,
    "lightning_barrage": LightningBarrage,
}

BIOME_DISASTERS = {
    "plains":   ["earthquake", "tornado", "sinkhole", "flash_flood", "lightning_barrage"],
    "forest":   ["earthquake", "tornado", "wildfire", "lightning_barrage", "mudslide", "flash_flood"],
    "desert":   ["earthquake", "sandstorm", "meteor", "sinkhole"],
    "snow":     ["earthquake", "blizzard", "avalanche", "ice_storm", "lightning_barrage"],
    "ocean":    ["earthquake", "tsunami", "whirlpool", "meteor"],
    "jungle":   ["earthquake", "mudslide", "wildfire", "lightning_barrage"],
}


class DisasterManager:
    """Manages natural disasters: triggers, chains, and active disaster tracking."""

    def __init__(self):
        self.active_disaster = None
        self.cooldown = 0.0
        self.min_cooldown = 60.0
        self.max_cooldown = 180.0
        self.screen_shake = 0.0
        self.chain_queue = []
        self.disaster_log = []

    def update(self, dt, world, player_pos, seed, rain_intensity=0.0):
        """Update disaster system. Returns screen shake amount."""
        self.screen_shake = 0.0

        if self.active_disaster:
            self.active_disaster.update(dt, player_pos)
            self.screen_shake = self.active_disaster.get_screen_shake()

            chains = self.active_disaster.get_chain_events()
            for chain_type, chain_pos in chains:
                self.chain_queue.append((chain_type, chain_pos))

            if not self.active_disaster.active:
                self.active_disaster = None
                self.cooldown = random.uniform(self.min_cooldown, self.max_cooldown)

        if self.chain_queue:
            chain_type, chain_pos = self.chain_queue.pop(0)
            self._trigger(chain_type, chain_pos, world, seed)

        if self.cooldown > 0:
            self.cooldown -= dt
        elif self.active_disaster is None:
            self._try_trigger(world, player_pos, seed, rain_intensity)

        return self.screen_shake

    def _try_trigger(self, world, player_pos, seed, rain_intensity):
        px, pz = int(player_pos[0]), int(player_pos[2])
        biome = get_biome(px, pz, seed)
        candidates = BIOME_DISASTERS.get(biome, ["earthquake", "tornado"])

        for dis_name in candidates:
            cls = DISASTER_CLASSES.get(dis_name)
            if cls is None:
                continue
            adjusted_prob = cls.probability
            if rain_intensity > 0.5 and dis_name in ("flash_flood", "lightning_barrage"):
                adjusted_prob *= 2.0
            if biome in cls.biome_specific or not cls.biome_specific:
                if random.random() < adjusted_prob:
                    self._trigger(dis_name, player_pos, world, seed)
                    return

    def _trigger(self, dis_name, pos, world, seed):
        cls = DISASTER_CLASSES.get(dis_name)
        if cls is None:
            return
        disaster = cls(world, pos, seed)
        disaster.start()
        self.active_disaster = disaster
        self.disaster_log.append(dis_name)

    def get_current_disaster_name(self):
        if self.active_disaster:
            return self.active_disaster.name
        return None

    def get_disaster_info(self):
        if self.active_disaster:
            return {
                "name": self.active_disaster.name,
                "intensity": self.active_disaster.intensity,
                "timer": self.active_disaster.timer,
            }
        return None

    def apply_chain_dirtying(self):
        """Apply chunk dirtying for any chain disasters that were triggered."""
        if self.active_disaster:
            self.active_disaster.apply_chunk_dirtying()

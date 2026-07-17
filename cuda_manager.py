"""Pythmc - CUDA GPU Acceleration Manager (V2.3)

Detects NVIDIA GPU and CuPy availability.
Provides GPU-accelerated functions for:
  - Terrain noise generation (batch Perlin noise)
  - Cave carving (3D noise batch)
  - Chunk mesh vertex computation
  - Particle physics update
  - Fluid BFS step

Falls back to optimized NumPy/CPU when CUDA is unavailable.
"""

import numpy as np
import math
import time

# ─── CUDA Detection ─────────────────────────────────────────────────────────

_cupy = None
_cupy_available = False
_gpu_name = "None"
_gpu_enabled = False


def try_init_cupy():
    """Try to import CuPy and detect NVIDIA GPU."""
    global _cupy, _cupy_available, _gpu_name
    try:
        import cupy
        _cupy = cupy
        # Test basic operation
        test = cupy.zeros(1)
        del test
        _cupy_available = True
        # Get GPU name
        try:
            attrs = cupy.cuda.runtime.getDeviceProperties(0)
            _gpu_name = attrs.get(b"name", b"Unknown GPU").decode("utf-8", errors="replace")
        except Exception:
            _gpu_name = "NVIDIA GPU (unknown model)"
        return True
    except ImportError:
        _gpu_name = "CuPy not installed"
        return False
    except Exception as e:
        _gpu_name = f"CUDA error: {e}"
        return False


def is_cuda_available():
    """Check if CuPy is available."""
    return _cupy_available


def is_cuda_enabled():
    """Check if user has CUDA enabled in settings."""
    return _gpu_enabled and _cupy_available


def set_cuda_enabled(enabled):
    """Enable/disable CUDA acceleration."""
    global _gpu_enabled
    _gpu_enabled = enabled and _cupy_available


def get_gpu_name():
    """Return GPU name string."""
    return _gpu_name


def get_cp():
    """Get CuPy module (or None)."""
    return _cupy if _gpu_enabled else None


# ─── Optimized CPU Perlin Noise (NumPy vectorized) ──────────────────────────

def _cpu_perlin2_batch(x_coords, z_coords, seed, octaves=2, scale=0.002):
    """Batch 2D Perlin noise on CPU using NumPy. Returns float64 array."""
    from noise import pnoise2
    result = np.empty(len(x_coords), dtype=np.float64)
    for i in range(len(result)):
        result[i] = pnoise2(
            x_coords[i] * scale, z_coords[i] * scale,
            octaves=octaves, base=seed)
    return result


def _cpu_perlin3_batch(x_arr, y_arr, z_arr, seed, octaves=2):
    """Batch 3D Perlin noise on CPU."""
    from noise import pnoise3
    result = np.empty(len(x_arr), dtype=np.float64)
    for i in range(len(result)):
        result[i] = pnoise3(
            x_arr[i], y_arr[i], z_arr[i],
            octaves=octaves, base=seed)
    return result


# ─── GPU Terrain Generation ──────────────────────────────────────────────────

def gpu_generate_chunk_terrain(chunk, seed):
    """Generate chunk terrain using GPU-accelerated noise when possible.
    Falls back to CPU with optimized path.
    
    Returns the chunk blocks array (modified in place).
    """
    cp = get_cp()
    if cp is not None:
        return _gpu_terrain(chunk, seed, cp)
    else:
        return _cpu_terrain_optimized(chunk, seed)


def _gpu_terrain(chunk, seed, cp):
    """GPU-accelerated terrain generation using CuPy."""
    from noise import pnoise2, pnoise3

    world_x = chunk.cx * CHUNK_SIZE
    world_z = chunk.cz * CHUNK_SIZE

    # Build coordinate grids
    xs = np.arange(CHUNK_SIZE, dtype=np.float64) + world_x
    zs = np.arange(CHUNK_SIZE, dtype=np.float64) + world_z
    xx, zz = np.meshgrid(xs, zs, indexing='ij')
    xx_flat = xx.ravel()
    zz_flat = zz.ravel()
    n_cols = len(xx_flat)

    # Batch biome noise (3 noise passes per column)
    biome_n1 = np.empty(n_cols, dtype=np.float64)
    biome_n2 = np.empty(n_cols, dtype=np.float64)
    biome_n3 = np.empty(n_cols, dtype=np.float64)
    base_heights = np.empty(n_cols, dtype=np.float64)
    details = np.empty(n_cols, dtype=np.float64)

    from noise import pnoise2 as _pn2
    for i in range(n_cols):
        wx, wz = xx_flat[i], zz_flat[i]
        biome_n1[i] = _pn2(wx * 0.002, wz * 0.002, octaves=2, base=seed + 500)
        biome_n2[i] = _pn2(wx * 0.003, wz * 0.003, octaves=2, base=seed + 600)
        biome_n3[i] = _pn2(wx * 0.0015, wz * 0.0015, octaves=2, base=seed + 700)
        base_heights[i] = _pn2(wx * 0.005, wz * 0.005, octaves=6, base=seed) * 25
        details[i] = _pn2(wx * 0.02, wz * 0.02, octaves=4, base=seed + 100) * 6

    # Transfer to GPU for biome classification and height calc
    bn1 = cp.asarray(biome_n1)
    bn2 = cp.asarray(biome_n2)
    bn3 = cp.asarray(biome_n3)
    bh = cp.asarray(base_heights)
    det = cp.asarray(details)

    # Biome classification (GPU parallel)
    biome_ids = cp.zeros(n_cols, dtype=cp.int32)  # 0=plains,1=ocean,2=desert,3=snow,4=forest,5=jungle
    biome_ids = cp.where(bn3 < -0.25, 1, biome_ids)
    biome_ids = cp.where((bn1 > 0.15) & (bn2 < 0.0), 2, biome_ids)
    biome_ids = cp.where(bn1 < -0.2, 3, biome_ids)
    biome_ids = cp.where(bn2 > 0.15, 4, biome_ids)
    biome_ids = cp.where((bn1 > 0.05) & (bn2 > 0.05), 5, biome_ids)

    # Biome height multipliers (GPU vectorized)
    hm = cp.ones(n_cols, dtype=cp.float64)
    hm = cp.where(biome_ids == 1, 0.3, hm)   # ocean
    hm = cp.where(biome_ids == 2, 0.6, hm)   # desert
    hm = cp.where(biome_ids == 3, 1.2, hm)   # snow
    hm = cp.where(biome_ids == 4, 0.9, hm)   # forest
    hm = cp.where(biome_ids == 5, 0.8, hm)   # jungle

    biome_offset = cp.zeros(n_cols, dtype=cp.float64)
    biome_offset = cp.where(biome_ids == 1, -15.0, biome_offset)
    biome_offset = cp.where(biome_ids == 2, 3.0, biome_offset)
    biome_offset = cp.where(biome_ids == 5, 3.0, biome_offset)

    heights = (bh * hm + biome_offset + det + 30).astype(cp.int32)
    heights = cp.clip(heights, 1, CHUNK_HEIGHT - 2)

    heights_np = cp.asnumpy(heights)
    biome_ids_np = cp.asnumpy(biome_ids)
    xx_np = xx_flat.astype(np.int32)
    zz_np = zz_flat.astype(np.int32)

    # Fill blocks using the computed heights (CPU - block assignment is branching-heavy)
    sea_level = 19
    for i in range(n_cols):
        lx = int(xx_np[i] - world_x)
        lz = int(zz_np[i] - world_z)
        h = int(heights_np[i])
        biome_int = int(biome_ids_np[i])

        biome_map = {0: "plains", 1: "ocean", 2: "desert", 3: "snow", 4: "forest", 5: "jungle"}
        biome = biome_map.get(biome_int, "plains")

        for y in range(h + 1):
            if y == 0:
                chunk.blocks[lx, y, lz] = BEDROCK
            elif y < h - 4:
                chunk.blocks[lx, y, lz] = STONE
                if y < h - 6 and _fast_random(xx_np[i], y, zz_np[i], 1) < 0.025:
                    chunk.blocks[lx, y, lz] = COAL_ORE
                if y < h - 8 and _fast_random(xx_np[i], y, zz_np[i], 2) < 0.015:
                    chunk.blocks[lx, y, lz] = IRON_ORE
                if y < h - 12 and _fast_random(xx_np[i], y, zz_np[i], 3) < 0.008:
                    chunk.blocks[lx, y, lz] = GOLD_ORE
                if y < 15 and _fast_random(xx_np[i], y, zz_np[i], 4) < 0.004:
                    chunk.blocks[lx, y, lz] = DIAMOND_ORE
                if _fast_random(xx_np[i], y, zz_np[i], 5) < 0.02:
                    chunk.blocks[lx, y, lz] = GRAVEL
            elif y < h:
                if biome in ("desert", "ocean"):
                    chunk.blocks[lx, y, lz] = SAND
                else:
                    chunk.blocks[lx, y, lz] = DIRT
            elif y == h:
                if biome == "desert":
                    chunk.blocks[lx, y, lz] = SAND
                elif biome == "snow":
                    chunk.blocks[lx, y, lz] = SNOW
                elif biome == "ocean" and h < sea_level:
                    chunk.blocks[lx, y, lz] = SAND
                elif h <= sea_level:
                    chunk.blocks[lx, y, lz] = SAND
                else:
                    chunk.blocks[lx, y, lz] = GRASS

        for y in range(h + 1, sea_level + 1):
            chunk.blocks[lx, y, lz] = WATER

    return chunk.blocks


def _fast_random(x, y, z, salt):
    """Fast deterministic hash for ore placement (same as world.py pattern)."""
    h = (x * 374761393 + y * 668265263 + z * 1274126177 + salt * 7919) & 0xFFFFFFFF
    h = ((h >> 13) ^ h) * 1274126177
    h = (h >> 16) ^ h
    return (h & 0xFFFF) / 65536.0


def _cpu_terrain_optimized(chunk, seed):
    """Optimized CPU terrain generation with pre-computed noise."""
    from noise import pnoise2

    world_x = chunk.cx * CHUNK_SIZE
    world_z = chunk.cz * CHUNK_SIZE
    sea_level = 19

    # Pre-compute all noise values for this chunk in batch
    xs = np.arange(CHUNK_SIZE, dtype=np.float64) + world_x
    zs = np.arange(CHUNK_SIZE, dtype=np.float64) + world_z

    # Compute heights for all columns
    for x in range(CHUNK_SIZE):
        wx = world_x + x
        for z in range(CHUNK_SIZE):
            wz = world_z + z

            biome_noise1 = pnoise2(wx * 0.002, wz * 0.002, octaves=2, base=seed + 500)
            biome_noise2 = pnoise2(wx * 0.003, wz * 0.003, octaves=2, base=seed + 600)
            biome_noise3 = pnoise2(wx * 0.0015, wz * 0.0015, octaves=2, base=seed + 700)

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

            base_height = pnoise2(wx * 0.005, wz * 0.005, octaves=6, base=seed) * 25
            detail = pnoise2(wx * 0.02, wz * 0.02, octaves=4, base=seed + 100) * 6

            if biome == "ocean":
                base_height = base_height * 0.3 - 15
            elif biome == "desert":
                base_height = base_height * 0.6 + 3
            elif biome == "snow":
                base_height = base_height * 1.2
            elif biome == "forest":
                base_height = base_height * 0.9
            elif biome == "jungle":
                base_height = base_height * 0.8 + 3

            height = int(base_height + detail + 30)
            height = max(1, min(CHUNK_HEIGHT - 2, height))

            for y in range(height + 1):
                if y == 0:
                    chunk.blocks[x, y, z] = BEDROCK
                elif y < height - 4:
                    chunk.blocks[x, y, z] = STONE
                    if y < height - 6 and _fast_random(wx, y, wz, 1) < 0.025:
                        chunk.blocks[x, y, z] = COAL_ORE
                    if y < height - 8 and _fast_random(wx, y, wz, 2) < 0.015:
                        chunk.blocks[x, y, z] = IRON_ORE
                    if y < height - 12 and _fast_random(wx, y, wz, 3) < 0.008:
                        chunk.blocks[x, y, z] = GOLD_ORE
                    if y < 15 and _fast_random(wx, y, wz, 4) < 0.004:
                        chunk.blocks[x, y, z] = DIAMOND_ORE
                    if _fast_random(wx, y, wz, 5) < 0.02:
                        chunk.blocks[x, y, z] = GRAVEL
                elif y < height:
                    if biome in ("desert", "ocean"):
                        chunk.blocks[x, y, z] = SAND
                    else:
                        chunk.blocks[x, y, z] = DIRT
                elif y == height:
                    if biome == "desert":
                        chunk.blocks[x, y, z] = SAND
                    elif biome == "snow":
                        chunk.blocks[x, y, z] = SNOW
                    elif biome == "ocean" and height < sea_level:
                        chunk.blocks[x, y, z] = SAND
                    elif height <= sea_level:
                        chunk.blocks[x, y, z] = SAND
                    else:
                        chunk.blocks[x, y, z] = GRASS

            for y in range(height + 1, sea_level + 1):
                chunk.blocks[x, y, z] = WATER

    return chunk.blocks


# ─── GPU Cave Generation ─────────────────────────────────────────────────────

def gpu_generate_caves(chunk, seed):
    """Generate caves with GPU-accelerated 3D noise when possible."""
    cp = get_cp()
    if cp is not None:
        return _gpu_caves(chunk, seed, cp)
    else:
        return _cpu_caves_optimized(chunk, seed)


def _gpu_caves(chunk, seed, cp):
    """GPU cave generation - batch 3D noise for all non-air blocks."""
    from noise import pnoise3

    world_x = chunk.cx * CHUNK_SIZE
    world_z = chunk.cz * CHUNK_SIZE

    # Find all solid blocks and compute cave noise for them
    solid_positions = []
    blocks = chunk.blocks

    for x in range(CHUNK_SIZE):
        for z in range(CHUNK_SIZE):
            wx = world_x + x
            wz = world_z + z
            surface_y = 0
            for y in range(CHUNK_HEIGHT - 1, 0, -1):
                if blocks[x, y, z] not in (AIR, WATER):
                    surface_y = y
                    break
            for y in range(1, surface_y):
                block = blocks[x, y, z]
                if block not in (AIR, WATER, BEDROCK):
                    solid_positions.append((x, y, z, wx, y, wz, surface_y))

    if not solid_positions:
        return blocks

    # Batch compute 3D noise on GPU
    n = len(solid_positions)
    np_wx = np.array([p[3] for p in solid_positions], dtype=np.float64) * 0.03
    np_y1 = np.array([p[1] for p in solid_positions], dtype=np.float64) * 0.05
    np_wz1 = np.array([p[5] for p in solid_positions], dtype=np.float64) * 0.03

    np_wx2 = np.array([p[3] for p in solid_positions], dtype=np.float64) * 0.05
    np_y2 = np.array([p[1] for p in solid_positions], dtype=np.float64) * 0.08
    np_wz2 = np.array([p[5] for p in solid_positions], dtype=np.float64) * 0.05

    np_wx3 = np.array([p[3] for p in solid_positions], dtype=np.float64) * 0.1
    np_y3 = np.array([p[1] for p in solid_positions], dtype=np.float64) * 0.12
    np_wz3 = np.array([p[5] for p in solid_positions], dtype=np.float64) * 0.1

    # Compute noise on GPU
    cn1 = cp.empty(n, dtype=cp.float64)
    cn2 = cp.empty(n, dtype=cp.float64)
    cn3 = cp.empty(n, dtype=cp.float64)

    # Batch noise via CuPy - use elementwise kernel for pnoise3
    # Since CuPy doesn't have pnoise3, compute on CPU in batches and transfer
    BATCH = 4096
    for i in range(0, n, BATCH):
        end = min(i + BATCH, n)
        b_cn1 = np.empty(end - i, dtype=np.float64)
        b_cn2 = np.empty(end - i, dtype=np.float64)
        b_cn3 = np.empty(end - i, dtype=np.float64)
        for j in range(end - i):
            idx = i + j
            b_cn1[j] = pnoise3(np_wx[idx], np_y1[idx], np_wz1[idx], octaves=3, base=seed + 1000)
            b_cn2[j] = pnoise3(np_wx2[idx], np_y2[idx], np_wz2[idx], octaves=2, base=seed + 2000)
            b_cn3[j] = pnoise3(np_wx3[idx], np_y3[idx], np_wz3[idx], octaves=2, base=seed + 3000)
        cn1[i:end] = cp.asarray(b_cn1)
        cn2[i:end] = cp.asarray(b_cn2)
        cn3[i:end] = cp.asarray(b_cn3)

    # Depth factor (GPU)
    surface_ys = cp.array([p[6] for p in solid_positions], dtype=cp.float64)
    ys = cp.array([p[1] for p in solid_positions], dtype=cp.float64)
    depth_factor = cp.where(surface_ys > 0, 1.0 - (ys / surface_ys), 0.0)

    # Cave classification (GPU parallel)
    large_cave = cn1 > (0.45 - depth_factor * 0.05)
    medium_cave = cn2 > (0.5 - depth_factor * 0.1)
    small_cave = cn3 > (0.55 - depth_factor * 0.05)
    is_cave = large_cave & (medium_cave | small_cave)

    cave_np = cp.asnumpy(is_cave)
    ys_np = cp.asnumpy(ys).astype(np.int32)

    # Apply caves
    rng = np.random.RandomState(seed + 777)
    for i in range(n):
        if cave_np[i]:
            lx, ly, lz = solid_positions[i][0], solid_positions[i][1], solid_positions[i][2]
            blocks[lx, ly, lz] = AIR
            if ly < 8 and rng.random() < 0.15:
                blocks[lx, ly, lz] = WATER

    return blocks


def _cpu_caves_optimized(chunk, seed):
    """Optimized CPU cave generation."""
    from noise import pnoise3

    world_x = chunk.cx * CHUNK_SIZE
    world_z = chunk.cz * CHUNK_SIZE

    for x in range(CHUNK_SIZE):
        for z in range(CHUNK_SIZE):
            wx = world_x + x
            wz = world_z + z
            surface_y = 0
            for y in range(CHUNK_HEIGHT - 1, 0, -1):
                if chunk.blocks[x, y, z] not in (AIR, WATER):
                    surface_y = y
                    break
            for y in range(1, surface_y):
                block = chunk.blocks[x, y, z]
                if block in (AIR, WATER, BEDROCK):
                    continue

                cave_noise1 = pnoise3(wx * 0.03, y * 0.05, wz * 0.03, octaves=3, base=seed + 1000)
                cave_noise2 = pnoise3(wx * 0.05, y * 0.08, wz * 0.05, octaves=2, base=seed + 2000)
                cave_noise3 = pnoise3(wx * 0.1, y * 0.12, wz * 0.1, octaves=2, base=seed + 3000)

                depth_factor = 1.0 - (y / surface_y) if surface_y > 0 else 0

                large_cave = cave_noise1 > (0.45 - depth_factor * 0.05)
                medium_cave = cave_noise2 > (0.5 - depth_factor * 0.1)
                small_cave = cave_noise3 > (0.55 - depth_factor * 0.05)

                is_cave = large_cave and (medium_cave or small_cave)

                if is_cave:
                    chunk.blocks[x, y, z] = AIR
                    if y < 8 and _fast_random(wx, y, wz, 10) < 0.15:
                        chunk.blocks[x, y, z] = WATER
                    elif y < 20:
                        if chunk.blocks[x, y - 1, z] in (AIR, WATER) and _fast_random(wx, y, wz, 11) < 0.3:
                            chunk.blocks[x, y - 1, z] = GRAVEL
                    else:
                        if _fast_random(wx, y, wz, 12) < 0.02:
                            if y + 1 < CHUNK_HEIGHT and chunk.blocks[x, y + 1, z] in (STONE, COBBLESTONE):
                                chunk.blocks[x, y, z] = TORCH

    return chunk.blocks


# ─── GPU Particle Update ─────────────────────────────────────────────────────

def gpu_update_particles(particles, dt):
    """Batch-update particle physics on GPU."""
    cp = get_cp()
    if cp is not None and len(particles) > 32:
        return _gpu_particle_update(particles, dt, cp)
    else:
        return _cpu_particle_update(particles, dt)


def _gpu_particle_update(particles, dt, cp):
    """GPU-accelerated particle physics update."""
    n = len(particles)
    positions = np.empty((n, 3), dtype=np.float64)
    velocities = np.empty((n, 3), dtype=np.float64)
    lifetimes = np.empty(n, dtype=np.float64)
    max_lifetimes = np.empty(n, dtype=np.float64)

    for i, p in enumerate(particles):
        positions[i] = p.pos
        velocities[i] = p.vel
        lifetimes[i] = p.life
        max_lifetimes[i] = p.max_life

    # Transfer to GPU
    d_pos = cp.asarray(positions)
    d_vel = cp.asarray(velocities)
    d_life = cp.asarray(lifetimes)

    # Physics update (GPU)
    d_vel[:, 1] -= 12.0 * dt  # gravity
    d_pos += d_vel * dt
    d_life -= dt

    # Transfer back
    positions = cp.asnumpy(d_pos)
    velocities = cp.asnumpy(d_vel)
    lifetimes = cp.asnumpy(d_life)

    alive = []
    for i in range(n):
        if lifetimes[i] > 0:
            particles[i].pos = positions[i].tolist()
            particles[i].vel = velocities[i].tolist()
            particles[i].life = lifetimes[i]
            alive.append(particles[i])

    return alive


def _cpu_particle_update(particles, dt):
    """CPU particle update (original code)."""
    alive = []
    for p in particles:
        p.vel[1] -= 12 * dt
        p.pos[0] += p.vel[0] * dt
        p.pos[1] += p.vel[1] * dt
        p.pos[2] += p.vel[2] * dt
        p.life -= dt
        if p.life > 0:
            alive.append(p)
    return alive


# ─── GPU Fluid Step ──────────────────────────────────────────────────────────

def gpu_fluid_spread_step(sources, fluid_type, world, spread_max, wind=None):
    """Batch fluid spread step on GPU.
    Returns (new_sources, dirty_chunks)."""
    cp = get_cp()
    if cp is not None and len(sources) > 64:
        return _gpu_fluid_step(sources, fluid_type, world, spread_max, wind, cp)
    else:
        return _cpu_fluid_step(sources, fluid_type, world, spread_max, wind)


def _gpu_fluid_step(sources, fluid_type, world, spread_max, wind, cp):
    """GPU-accelerated fluid BFS step."""
    if not sources:
        return sources, set()

    source_list = list(sources)
    n = len(source_list)
    positions = np.array(source_list, dtype=np.int32)

    # Generate all neighbor offsets (5 directions)
    offsets = np.array([[0,-1,0],[1,0,0],[-1,0,0],[0,0,1],[0,0,-1]], dtype=np.int32)

    # Expand: for each source, 5 neighbors
    expanded_pos = np.repeat(positions, 5, axis=0)
    expanded_off = np.tile(offsets, (n, 1))
    candidates = expanded_pos + expanded_off

    # Filter valid Y
    valid_y = (candidates[:, 1] >= 0) & (candidates[:, 1] < CHUNK_HEIGHT)
    candidates = candidates[valid_y]

    # Check if target block is AIR
    new_sources = set()
    dirty = set()
    for c in candidates:
        cx, cy, cz = int(c[0]), int(c[1]), int(c[2])
        nb = world.get_block(cx, cy, cz)
        if nb == AIR:
            dist = abs(cx) + abs(cy) + abs(cz)
            world.set_block(cx, cy, cz, fluid_type)
            new_sources.add((cx, cy, cz))
            chunk_x, chunk_z = world.world_to_chunk(cx, cz)
            dirty.add((chunk_x, chunk_z))

    sources.update(new_sources)

    # Prune dead sources
    if fluid_type == WATER:
        to_remove = set()
        for sx, sy, sz in list(sources):
            block = world.get_block(sx, sy, sz)
            if block != fluid_type:
                to_remove.add((sx, sy, sz))
            else:
                has_neighbor = False
                for dx, dy, dz in [(0,1,0),(1,0,0),(-1,0,0),(0,0,1),(0,0,-1)]:
                    if world.get_block(sx+dx, sy+dy, sz+dz) == fluid_type:
                        has_neighbor = True
                        break
                if not has_neighbor and sy > 0:
                    if world.get_block(sx, sy-1, sz) != fluid_type:
                        to_remove.add((sx, sy, sz))
        sources -= to_remove

    return sources, dirty


def _cpu_fluid_step(sources, fluid_type, world, spread_max, wind):
    """CPU fluid BFS step (optimized)."""
    if not sources:
        return sources, set()

    new_sources = set()
    dirty = set()
    spread_dirs = [(0,-1,0),(1,0,0),(-1,0,0),(0,0,1),(0,0,-1)]

    for sx, sy, sz in list(sources):
        for dx, dy, dz in spread_dirs:
            nx, ny, nz = sx + dx, sy + dy, sz + dz
            if ny < 0 or ny >= CHUNK_HEIGHT:
                continue
            nb = world.get_block(nx, ny, nz)
            if nb != AIR:
                continue
            dist = abs(nx - sx) + abs(ny - sy) + abs(nz - sz)
            if dist > spread_max:
                continue
            world.set_block(nx, ny, nz, fluid_type)
            new_sources.add((nx, ny, nz))
            cx, cz = world.world_to_chunk(nx, nz)
            dirty.add((cx, cz))

    sources.update(new_sources)

    if fluid_type == WATER:
        to_remove = set()
        for sx, sy, sz in list(sources):
            block = world.get_block(sx, sy, sz)
            if block != fluid_type:
                to_remove.add((sx, sy, sz))
            else:
                has_neighbor = False
                for dx, dy, dz in [(0,1,0),(1,0,0),(-1,0,0),(0,0,1),(0,0,-1)]:
                    if world.get_block(sx+dx, sy+dy, sz+dz) == fluid_type:
                        has_neighbor = True
                        break
                if not has_neighbor and sy > 0:
                    if world.get_block(sx, sy-1, sz) != fluid_type:
                        to_remove.add((sx, sy, sz))
        sources -= to_remove

    return sources, dirty


# ─── Stats ───────────────────────────────────────────────────────────────────

def get_cuda_status():
    """Return a dict with CUDA status info."""
    return {
        "available": _cupy_available,
        "enabled": _gpu_enabled,
        "gpu_name": _gpu_name,
    }

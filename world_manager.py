"""Pythmc - World Manager (save/load worlds)"""

import os
import json
import time
import shutil
from pathlib import Path


WORLDS_DIR = os.path.join(os.path.dirname(__file__), "saves")


def ensure_saves_dir():
    """Make sure the saves directory exists."""
    os.makedirs(WORLDS_DIR, exist_ok=True)


def get_worlds_dir():
    return WORLDS_DIR


def list_worlds():
    """List all saved worlds."""
    ensure_saves_dir()
    worlds = []
    for name in os.listdir(WORLDS_DIR):
        world_dir = os.path.join(WORLDS_DIR, name)
        meta_file = os.path.join(world_dir, "world.json")
        if os.path.isdir(world_dir) and os.path.exists(meta_file):
            try:
                with open(meta_file, "r") as f:
                    meta = json.load(f)
                worlds.append({
                    "name": name,
                    "gamemode": meta.get("gamemode", "creative"),
                    "seed": meta.get("seed", 42),
                    "show_coords": meta.get("show_coords", False),
                    "io_enabled": meta.get("io_enabled", False),
                    "created": meta.get("created", 0),
                    "last_played": meta.get("last_played", 0),
                    "play_time": meta.get("play_time", 0),
                    "days_survived": meta.get("days_survived", 0),
                    "blocks_dug": meta.get("blocks_dug", 0),
                    "blocks_placed": meta.get("blocks_placed", 0),
                    "world_settings": meta.get("world_settings", {}),
                })
            except Exception:
                pass
    # Sort by last played (most recent first)
    worlds.sort(key=lambda w: w["last_played"], reverse=True)
    return worlds


def create_world(name, gamemode="survival", seed=None, show_coords=False,
                 io_enabled=False, world_settings=None):
    """Create a new world."""
    ensure_saves_dir()
    if seed is None:
        import random
        seed = random.randint(0, 999999)
    
    world_dir = os.path.join(WORLDS_DIR, name)
    if os.path.exists(world_dir):
        raise ValueError(f"World '{name}' already exists")
    
    os.makedirs(world_dir)
    meta = {
        "name": name,
        "gamemode": gamemode,
        "seed": seed,
        "show_coords": show_coords,
        "io_enabled": io_enabled,
        "io_triggers": [],
        "world_settings": world_settings or {},
        "created": time.time(),
        "last_played": time.time(),
        "play_time": 0,
        "days_survived": 0,
        "blocks_dug": 0,
        "blocks_placed": 0,
    }
    with open(os.path.join(world_dir, "world.json"), "w") as f:
        json.dump(meta, f, indent=2)
    
    # Create player data file
    player_data = {
        "pos": [8.5, 50.0, 8.5],
        "yaw": 0.0,
        "pitch": 0.0,
        "health": 20.0,
        "hunger": 20.0,
        "inventory": {
            "hotbar": [
                {"item": 1, "count": 64},  # GRASS
                {"item": 2, "count": 64},  # DIRT
                {"item": 3, "count": 64},  # STONE
                {"item": 4, "count": 64},  # WOOD
                {"item": 9, "count": 64},  # PLANKS
                {"item": 8, "count": 64},  # COBBLESTONE
                {"item": 6, "count": 64},  # SAND
                {"item": 13, "count": 64}, # GLASS
                {"item": 14, "count": 64}, # BRICK
            ],
            "main": [[{"item": 0, "count": 0} for _ in range(9)] for _ in range(3)],
        },
        "selected_slot": 0,
    }
    with open(os.path.join(world_dir, "player.json"), "w") as f:
        json.dump(player_data, f, indent=2)
    
    return meta


def load_world_meta(name):
    """Load world metadata."""
    meta_file = os.path.join(WORLDS_DIR, name, "world.json")
    if not os.path.exists(meta_file):
        return None
    with open(meta_file, "r") as f:
        return json.load(f)


def save_world_meta(name, meta):
    """Save world metadata."""
    meta_file = os.path.join(WORLDS_DIR, name, "world.json")
    with open(meta_file, "w") as f:
        json.dump(meta, f, indent=2)


def load_player_data(name):
    """Load player data."""
    player_file = os.path.join(WORLDS_DIR, name, "player.json")
    if not os.path.exists(player_file):
        return None
    with open(player_file, "r") as f:
        return json.load(f)


def save_player_data(name, player_data):
    """Save player data."""
    world_dir = os.path.join(WORLDS_DIR, name)
    os.makedirs(world_dir, exist_ok=True)
    player_file = os.path.join(world_dir, "player.json")
    with open(player_file, "w") as f:
        json.dump(player_data, f, indent=2)


def save_chunk_data(world_name, cx, cz, blocks):
    """Save chunk block data."""
    chunks_dir = os.path.join(WORLDS_DIR, world_name, "chunks")
    os.makedirs(chunks_dir, exist_ok=True)
    chunk_file = os.path.join(chunks_dir, f"{cx}_{cz}.bin")
    blocks.tofile(chunk_file)


def load_chunk_data(world_name, cx, cz):
    """Load chunk block data. Returns None if not found."""
    import numpy as np
    chunk_file = os.path.join(WORLDS_DIR, world_name, "chunks", f"{cx}_{cz}.bin")
    if not os.path.exists(chunk_file):
        return None
    try:
        return np.fromfile(chunk_file, dtype=np.uint8).reshape(16, 64, 16)
    except Exception:
        return None


def delete_world(name):
    """Delete a world."""
    world_dir = os.path.join(WORLDS_DIR, name)
    if os.path.exists(world_dir):
        shutil.rmtree(world_dir)


def world_exists(name):
    """Check if a world exists."""
    return os.path.exists(os.path.join(WORLDS_DIR, name, "world.json"))


def update_play_time(name, seconds):
    """Update the play time for a world."""
    meta = load_world_meta(name)
    if meta:
        meta["play_time"] = meta.get("play_time", 0) + seconds
        meta["last_played"] = time.time()
        save_world_meta(name, meta)


def increment_stat(name, stat, amount=1):
    """Increment a stat (days_survived, blocks_dug, blocks_placed)."""
    meta = load_world_meta(name)
    if meta:
        meta[stat] = meta.get(stat, 0) + amount
        save_world_meta(name, meta)


def set_stat(name, stat, value):
    """Set a stat to a specific value."""
    meta = load_world_meta(name)
    if meta:
        meta[stat] = value
        save_world_meta(name, meta)

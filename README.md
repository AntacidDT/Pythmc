# Pythmc - Minecraft Clone in Python

A 3D voxel game built from scratch using Python and OpenGL. No game engine — just raw OpenGL immediate mode, procedural textures, procedural sounds, and bundled dependencies.

**Works on school computers. No pip install needed.**

## How to Run

### Windows
Double-click `run.bat`

### Linux / Mac
```bash
./run.sh
```

### Or directly with Python
```bash
python3 run.py
```

**Requirements:** Python 3.8+. All dependencies (PyOpenGL, Pygame, NumPy, noise) are bundled in the `lib/` folder.

## Controls

| Key | Action |
|-----|--------|
| WASD | Move |
| Mouse | Look around |
| Space | Jump / Fly up / Swim up |
| Shift | Sprint / Fly down |
| Ctrl | Sprint |
| Left Click | Break block / Attack |
| Right Click | Place block / Use / Eat / Open furnace |
| 1-9 | Select hotbar slot |
| E | Inventory & Crafting |
| F | Toggle fly (Creative only) |
| F5 | Toggle third-person camera |
| F11 | Fullscreen |
| G | Freeze/unfreeze day/night |
| R | Respawn when dead |
| / | Console (if cheats enabled) |
| Alt+F2 | Developer debug overlay |
| Esc | Pause menu |

## Features

### World
- Perlin noise terrain generation
- 6 biomes: Plains, Forest, Desert, Snow, Jungle, Ocean
- Caves with 3D noise carving
- Ore generation: Coal, Iron, Gold, Diamond (below Y=15)
- 6 structures: Houses, Towers, Ruins, Wells, Gardens, Electronics Factories
- Trees, flowers, cacti
- Chunk-based rendering with threaded generation
- Save/load world system

### Gameplay (Survival Mode)
- 40+ block types with procedural 16x16 textures
- Block drops (ores drop materials, grass drops dirt, glass drops nothing)
- Item pickup system with floating entities
- Hunger & saturation system with starvation
- Natural regeneration
- Fall damage with armor reduction
- 15 food types with eating mechanic
- Furnace smelting (8 recipes, 4 fuels)
- 80+ crafting recipes including tools, armor, and electronics
- Full armor system (Leather, Iron, Gold, Diamond) with damage reduction
- Diamond tools (best tier)
- Mob drops (raw food, leather, bones, arrows)

### Mobs
- **Passive:** Cow, Sheep, Chicken (OBJ models with walk animation)
- **Hostile:** Zombie, Skeleton (AI with chase/flee states)
- Item drops from blocks and mobs

### Electronics (Unique to Pythmc)
- Resistors, Capacitors (polarized!), Transistors, ICs
- NE555 timer, Logic gates (AND, OR, NOT, NAND, NOR)
- LEDs, Batteries, Switches, Wires
- Polarity system — wrong polarity causes explosions
- Electronics Factories with loot

### Multiplayer
- LAN server hosting (TCP + UDP)
- Player position sync
- Server discovery broadcast
- Proximity-based voice chat

### Atmosphere
- Day/night cycle with sky gradient
- Weather: Rain, Thunder with lightning
- Ambient particles: Dust, Fireflies, Mist
- Stars and moon

### Technical
- 25+ procedural sound effects (no audio files)
- Procedural texture generation (no image files for blocks)
- OBJ model loading with MTL materials
- Third-person camera with player body rendering
- Developer debug overlay (Alt+F2)
- 25+ console commands

## Architecture

28 Python source files, ~10,000+ lines of code.

```
run.py                  Entry point
main.py                 Game orchestrator
constants.py            All block/item/entity IDs and properties
world.py                World generation, chunk system, mesh building
player.py               Player mechanics, physics, collision
renderer.py             HUD, particles, clouds, player body rendering
entities.py             Mobs, AI, item drops
textures.py             Procedural texture generation
crafting.py             80+ recipes
inventory_ui.py         Inventory and crafting UI
furnace_ui.py           Furnace smelting UI
sounds.py               Procedural sound generation
terminal.py             Console commands
atmosphere.py           Weather, particles, sky rendering
circuits.py             Electronics simulation
factory.py              Electronics factory structure
structures.py           World structures
network.py              Multiplayer server/client
voice.py                Voice chat
menu.py                 Main/pause/settings menus
world_screens.py        World selection/creation
multiplayer_screens.py  Host/join screens
credits.py              Credits screen
text_renderer.py        OpenGL text rendering
obj_loader.py           OBJ model loading
builder.py              Structure builder tool
world_manager.py        Save/load management
minecraft.py            Legacy single-file version
```

## Credits

Made by **AntacidDT** — [github.com/AntacidDT](https://github.com/AntacidDT)

Built with:
- Python 3
- PyOpenGL
- Pygame
- NumPy
- Perlin Noise

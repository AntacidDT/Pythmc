# Pythmc - Complete Project Documentation

**Full name:** Pythmc (Python Minecraft)
**Engine:** Pythkernel
**Version:** V2.6 - Loading Screen, Music & Icon
**Language:** Python 3
**Graphics:** PyOpenGL (immediate mode)
**Audio:** Pygame mixer
**Dependencies:** PyOpenGL, Pygame, NumPy, Perlin noise (all bundled in `lib/`)
**Entry point:** `python3 run.py`
**Resolution:** 1280x720 @ 60 FPS

---

## Table of Contents

1. [Core Engine](#1-core-engine)
2. [Block System](#2-block-system)
3. [World Generation](#3-world-generation)
4. [Player System](#4-player-system)
5. [Physics & Collision](#5-physics--collision)
6. [Inventory & Items](#6-inventory--items)
7. [Crafting System](#7-crafting-system)
8. [Furnace System](#8-furnace-system)
9. [Combat & Damage](#9-combat--damage)
10. [Entity System](#10-entity-system)
11. [Armor System](#11-armor-system)
12. [Food & Hunger](#12-food--hunger)
13. [Tool System](#13-tool-system)
14. [Block Drops & Item Pickup](#14-block-drops--item-pickup)
15. [Texture System](#15-texture-system)
16. [Rendering Engine](#16-rendering-engine)
17. [HUD & UI](#17-hud--ui)
18. [Menu System](#18-menu-system)
19. [Sound System](#19-sound-system)
20. [Atmosphere & Weather](#20-atmosphere--weather)
21. [Electronics System](#21-electronics-system)
22. [Structures](#22-structures)
23. [Multiplayer](#23-multiplayer)
24. [Voice Chat](#24-voice-chat)
25. [Console/Terminal](#25-consoleterminal)
26. [Developer Tools](#26-developer-tools)
27. [OBJ Model Loading](#27-obj-model-loading)
28. [World Management](#28-world-management)
29. [Settings](#29-settings)
30. [Credits](#30-credits)

---

## 1. Core Engine

### Architecture
- **28 Python source files** organized by system
- **Immediate mode OpenGL** (glBegin/glEnd) for all rendering
- **Pygame** for windowing, input, audio, and font rendering
- **Threading** for background chunk generation (ChunkGenerator)
- **Purely procedural** - no external assets required (textures, sounds, terrain all generated in code)

### Game States
| State | Description |
|-------|-------------|
| `MENU` | Main menu (Play, Multiplayer, Settings, Credits) |
| `WORLD_SELECT` | Browse and play saved worlds |
| `WORLD_CREATE` | Create a new world (name, gamemode, seed) |
| `PLAYING` | Active gameplay |
| `PAUSED` | Pause menu (Resume, Settings, Save & Quit) |
| `SETTINGS` | Render distance, sensitivity, volume, FOV |
| `CREDITS` | Maker info and tools |
| `HOST_GAME` | Multiplayer host screen |
| `JOIN_GAME` | Multiplayer join screen |

### Controls
| Key | Action |
|-----|--------|
| WASD | Move |
| Space | Jump / Fly up / Swim up |
| Shift (L) | Sprint / Fly down |
| Ctrl (L) | Sprint |
| Mouse | Look around |
| Left Click | Break block / Attack entity |
| Right Click | Place block / Use item / Eat food / Open furnace-crafting |
| 1-9 | Select hotbar slot |
| E | Open inventory / Crafting / Furnace |
| F | Toggle fly (Creative only) |
| F5 | Toggle third-person camera |
| F11 | Toggle fullscreen |
| G | Toggle day/night freeze |
| R | Respawn (when dead) |
| / | Open terminal (cheats only) |
| Alt+F2 | Toggle developer debug overlay |
| Esc | Pause menu |

### Key Constants
```
CHUNK_SIZE = 16
CHUNK_HEIGHT = 64
RENDER_DISTANCE = 4 chunks
SEED = 42 (default)
FPS = 60
```

---

## 2. Block System

### Block IDs (0-41)

| ID | Name | Solid | Transparent | Notes |
|----|------|-------|-------------|-------|
| 0 | Air | No | Yes | |
| 1 | Grass | Yes | No | Drops dirt. Tintable per-block. |
| 2 | Dirt | Yes | No | |
| 3 | Stone | Yes | No | |
| 4 | Wood | Yes | No | Tree trunk. Tintable. |
| 5 | Leaves | Yes | Yes | Drops apple/stick. Tintable. |
| 6 | Sand | Yes | No | Tintable. |
| 7 | Water | No | Yes | Player swims in it. |
| 8 | Cobblestone | Yes | No | |
| 9 | Planks | Yes | No | Tintable. |
| 10 | Bedrock | Yes | No | Unbreakable in survival. |
| 11 | Coal Ore | Yes | No | Drops coal. |
| 12 | Iron Ore | Yes | No | Drops raw iron. |
| 13 | Glass | Yes | Yes | Drops nothing. |
| 14 | Brick | Yes | No | |
| 15 | Snow | Yes | No | Tintable. |
| 16 | Cactus | Yes | No | Tintable. |
| 17 | Torch | No | Yes | Non-solid decorative. |
| 18 | Gravel | Yes | No | |
| 19 | Gold Ore | Yes | No | Drops raw gold. |
| 20 | Crafting Table | Yes | No | Right-click opens 3x3 grid. |
| 21 | Furnace | Yes | No | Right-click opens smelting UI. |
| 22 | Copper Wire | No | Yes | Electronic block. |
| 23 | Gold Wire | No | Yes | Electronic block. |
| 24 | Resistor | Yes | No | Electronic block. |
| 25 | Capacitor | Yes | No | Electronic block. |
| 26 | NPN Transistor | Yes | No | Electronic block. |
| 27 | PNP Transistor | Yes | No | Electronic block. |
| 28 | Red LED | Yes | No | Electronic block. |
| 29 | Green LED | Yes | No | Electronic block. |
| 30 | Blue LED | Yes | No | Electronic block. |
| 31 | Battery | Yes | No | Electronic block. |
| 32 | Switch | Yes | No | Electronic block. |
| 33 | Button | Yes | No | Electronic block. |
| 34 | Circuit Board | Yes | No | Electronic block. |
| 35 | Silicon | Yes | No | Electronic block. |
| 36 | Copper Block | Yes | No | Electronic block. |
| 37 | NE555 Timer | Yes | No | Electronic block. |
| 38 | Logic Gate | Yes | No | Electronic block. |
| 39 | Buzzer | Yes | No | Electronic block. |
| 40 | Diamond Ore | Yes | No | Drops diamond. Generates below Y=15. |

### Block Properties
- **SOLID_BLOCKS**: IDs 1-99 minus {water, torch, copper wire, gold wire}
- **TRANSPARENT**: {air, water, glass, leaves, torch, copper wire, gold wire}
- **PLACEABLE_BLOCKS**: All keys in BLOCK_NAMES (validated before placement)
- **ITEM_TO_BLOCK**: Maps placed-item IDs to block IDs (CRAFTING_TABLE->20, FURNACE->21, TORCH_ITEM->17)

### Per-Block Tinting
Certain blocks (grass, leaves, sand, snow, cactus, planks, wood) get a **per-block random color tint** computed during chunk mesh building using a deterministic hash of world coordinates. This means no two grass blocks look exactly the same, but the variation is consistent across chunk rebuilds. Uses integer hash for speed, no floating-point randomness.

---

## 3. World Generation

### Terrain
- **Perlin noise** (pnoise2) for height map
- **Multiple octaves** (3-6) for natural-looking terrain
- **Sea level** at Y=20 (water fills below)
- **Bedrock** at Y=0
- **Stone** dominates from Y=5 to surface
- **Dirt/Grass** at surface in temperate biomes
- **Sand** at surface in desert/ocean biomes
- **Snow** at surface in snow biome

### Biomes
| Biome | Terrain | Special |
|-------|---------|---------|
| Plains | Flat, grass | Flowers |
| Forest | Rolling, grass, trees | Dense trees |
| Desert | Sandy, flat | Cacti |
| Snow | Hilly, snow | Snow blocks, ice |
| Jungle | Dense vegetation | Thick trees |
| Ocean | Below sea level | Sand floor, water |

### Ores
| Ore | Y Range | Frequency | Drop |
|-----|---------|-----------|------|
| Coal | Below Y=40 | ~2% | Coal |
| Iron | Below Y=30 | ~1.5% | Raw Iron |
| Gold | Below Y=20 | ~1% | Raw Gold |
| Diamond | Below Y=15 | ~0.4% | Diamond |

### Caves
- 3D Perlin noise (pnoise3) for cave carving
- Cave entrances near surface
- Gravel floors in some caves
- Deep lava at lowest levels (currently rendered as water placeholder)

### Trees
- Generated on grass blocks in forest/plains biomes
- **Trunk**: 4-6 blocks tall, WOOD blocks
- **Leaves**: 5x5 canopy around top of trunk, LEAVES blocks
- Corner leaf blocks have 65% chance of being omitted for natural shape

### Structures
| Structure | Description |
|-----------|-------------|
| **Small House** | Wooden walls, planks roof, door opening, torch inside |
| **Stone Tower** | Cobblestone walls, 3 floors, spiral pattern |
| **Ruins** | Broken stone/brick walls, overgrown with gravel |
| **Well** | Circular stone base, water in center |
| **Garden** | Fenced area with flowers and crops |
| **Electronics Factory** | Industrial building with loot chests containing electronic components |

### Chunk System
- **16x16x64** blocks per chunk
- **Background thread** (ChunkGenerator) handles terrain generation
- **Main thread** builds mesh and OpenGL display lists
- **Time-budgeted meshing**: up to 5ms per frame to prevent freezes
- **Pre-generation**: Chunks generated 2 chunks ahead of player
- **Neighbor dirtying**: New chunks mark neighbors dirty for border face rebuild
- **Unloading**: Chunks beyond render distance + 3 are cleaned up

---

## 4. Player System

### Attributes
| Attribute | Default | Description |
|-----------|---------|-------------|
| `pos` | (0.5, 100, 0.5) | 3D position (numpy float64) |
| `velocity` | (0, 0, 0) | Movement velocity |
| `yaw` | 0.0 | Horizontal rotation (degrees) |
| `pitch` | 0.0 | Vertical rotation (degrees) |
| `health` | 20.0 | Current health |
| `max_health` | 20.0 | Maximum health |
| `hunger` | 20.0 | Hunger bar |
| `max_hunger` | 20.0 | Maximum hunger |
| `saturation` | 5.0 | Saturation (drains before hunger) |
| `creative` | False | Creative mode flag |
| `flying` | False | Flight mode |
| `on_ground` | False | Ground contact |
| `in_water` | False | Submerged check |
| `dead` | False | Death state |
| `third_person` | False | Third-person camera |
| `selected_slot` | 0 | Active hotbar slot (0-8) |
| `fall_distance` | 0.0 | Accumulated fall height |
| `attack_cooldown` | 0.0 | Time between attacks |
| `hurt_timer` | 0.0 | Invincibility frames after hit |
| `spawn_immunity` | 3.0 | Initial spawn protection seconds |
| `crafting_open` | False | Crafting UI state |
| `walk_cycle` | 0.0 | Walk animation phase |
| `arm_swing` | 0.0 | Arm swing angle |
| `eating` | False | Eating state |
| `eat_timer` | 0.0 | Eating progress timer |
| `eat_duration` | 1.6 | Seconds to eat |
| `eat_item` | None | Currently eating item |
| `armor` | [0,0,0,0] | 4 armor slots: [helmet, chestplate, leggings, boots] |
| `regen_cooldown` | 0.0 | Cooldown between regen ticks |

### Methods
| Method | Description |
|--------|-------------|
| `update(dt, keys)` | Main update loop: movement, physics, hunger, regen |
| `get_forward()` | Camera forward vector |
| `get_right()` | Camera right vector |
| `get_eye_pos()` | Eye position (pos + PLAYER_HEIGHT) |
| `take_damage(amount)` | Apply damage with armor reduction |
| `die()` | Set dead state, start respawn timer |
| `_spawn()` | Find safe spawn point |
| `eat(item_type)` | Start eating food item |
| `equip_armor(item_type)` | Equip armor from held slot |
| `get_armor_defense()` | Sum of armor defense points |

---

## 5. Physics & Collision

### Movement Speeds
| State | Speed |
|-------|-------|
| Walking | 4.3 blocks/s |
| Sprinting | 6.5 blocks/s |
| Swimming | 3.0 blocks/s |
| Flying | 12.0 blocks/s |

### Physics
- **Gravity**: -25.0 blocks/s^2
- **Jump speed**: 9.0 blocks/s
- **Water drag**: 0.6 multiplier per frame
- **Max fall speed**: -50.0 blocks/s
- **Break/place cooldown**: 0.2 seconds
- **Max reach**: 6.0 blocks

### Player Hitbox
- **Width**: 0.3 blocks (diameter)
- **Height**: 1.62 blocks (eye height)
- 27 collision test points (3x3x3 grid at feet/mid/head)

### Collision Detection
- **Axis-separated collision resolution**: X, Y, Z resolved independently
- **Swept collision on Y axis**: Subdivides vertical movement into steps to prevent tunneling at high velocities
- **Block lookup**: Uses `world.get_block()` which returns STONE for unloaded chunks (prevents falling through unloaded terrain)
- **Correct negative coordinates**: `world_to_chunk()` uses `math.floor()` for proper negative coordinate handling

### Fall Damage
- Applies when falling more than 3 blocks
- Damage = fall_distance - 3.0
- Reduced by armor (25-point defense scale)
- No fall damage in creative mode or during spawn immunity

---

## 6. Inventory & Items

### Inventory Layout
- **Hotbar**: 9 slots (displayed at bottom of screen)
- **Main inventory**: 9 columns x 3 rows = 27 slots
- **Armor**: 4 slots (helmet, chestplate, leggings, boots)
- **Crafting**: 2x2 grid (from inventory) or 3x3 grid (at crafting table)

### Item Categories

#### Tools (100-109)
| ID | Name | Mining Speed | Damage | Type |
|----|------|-------------|--------|------|
| 100 | Stick | - | - | Material |
| 101 | Wood Pickaxe | 2.0 | 1.5 | Pickaxe |
| 102 | Wood Axe | 2.0 | 1.5 | Axe |
| 103 | Wood Sword | 1.0 | 3.0 | Sword |
| 104 | Stone Pickaxe | 3.0 | 2.0 | Pickaxe |
| 105 | Stone Axe | 3.0 | 2.0 | Axe |
| 106 | Stone Sword | 1.0 | 4.0 | Sword |
| 107 | Iron Pickaxe | 4.0 | 2.5 | Pickaxe |
| 108 | Iron Axe | 4.0 | 2.5 | Axe |
| 109 | Iron Sword | 1.0 | 5.0 | Sword |

#### Diamond Tools (120-124)
| ID | Name | Mining Speed | Damage | Type |
|----|------|-------------|--------|------|
| 120 | Diamond | - | - | Material |
| 121 | Diamond Pickaxe | 6.0 | 3.0 | Pickaxe |
| 122 | Diamond Axe | 6.0 | 3.0 | Axe |
| 123 | Diamond Sword | 1.0 | 7.0 | Sword |
| 124 | Diamond Shovel | - | - | Shovel |

#### Crafted Items (110-119)
| ID | Name |
|----|------|
| 110 | Crafting Table |
| 111 | Furnace |
| 112 | Torch |
| 113 | Coal |
| 114 | Iron Ingot |
| 115 | Gold Ingot |
| 116 | Raw Iron |
| 117 | Raw Gold |

#### Food Items (130-143)
| ID | Name | Hunger | Saturation | Cooked? |
|----|------|--------|------------|---------|
| 130 | Raw Beef | 3 | 1.8 | No |
| 131 | Cooked Beef | 8 | 12.8 | Yes |
| 132 | Raw Chicken | 2 | 1.2 | No |
| 133 | Cooked Chicken | 6 | 7.2 | Yes |
| 134 | Raw Mutton | 2 | 1.2 | No |
| 135 | Cooked Mutton | 6 | 7.2 | Yes |
| 136 | Bread | 5 | 6.0 | No |
| 137 | Apple | 4 | 2.4 | No |
| 138 | Golden Apple | 20 | 20.0 | No |
| 139 | Cookie | 2 | 0.4 | No |
| 140 | Steak | 8 | 12.8 | Yes |
| 141 | Carrot | 3 | 3.6 | No |
| 142 | Potato | 1 | 0.6 | No |
| 143 | Wheat | 1 | 0.3 | No |

#### Materials (144-148)
| ID | Name |
|----|------|
| 144 | Leather |
| 145 | Feather |
| 146 | Wool |
| 147 | Bone |
| 148 | Arrow |

#### Armor (150-165)
| ID | Name | Defense | Slot |
|----|------|---------|------|
| 150 | Leather Helmet | 1 | Helmet |
| 151 | Leather Tunic | 3 | Chestplate |
| 152 | Leather Pants | 2 | Leggings |
| 153 | Leather Boots | 1 | Boots |
| 154 | Iron Helmet | 2 | Helmet |
| 155 | Iron Chestplate | 6 | Chestplate |
| 156 | Iron Leggings | 5 | Leggings |
| 157 | Iron Boots | 2 | Boots |
| 158 | Gold Helmet | 2 | Helmet |
| 159 | Gold Chestplate | 6 | Chestplate |
| 160 | Gold Leggings | 5 | Leggings |
| 161 | Gold Boots | 2 | Boots |
| 162 | Diamond Helmet | 3 | Helmet |
| 163 | Diamond Chestplate | 8 | Chestplate |
| 164 | Diamond Leggings | 6 | Leggings |
| 165 | Diamond Boots | 3 | Boots |

#### Electronic Components (200-235)
| ID | Name |
|----|------|
| 200 | Copper Wire |
| 201 | Gold Wire |
| 202 | 100R Resistor |
| 203 | 1K Resistor |
| 204 | 10K Resistor |
| 205 | Ceramic Capacitor |
| 206 | Electrolytic Capacitor |
| 207 | Tantalum Capacitor |
| 208 | NPN Transistor |
| 209 | PNP Transistor |
| 210 | Red LED |
| 211 | Green LED |
| 212 | Blue LED |
| 213 | White LED |
| 214 | 9V Battery |
| 215 | AA Battery |
| 216 | Switch |
| 217 | Button |
| 218 | Circuit Board |
| 219 | Silicon Wafer |
| 220 | Copper Wire |
| 221 | NE555 Timer |
| 222 | AND Gate |
| 223 | OR Gate |
| 224 | NOT Gate |
| 225 | NAND Gate |
| 226 | NOR Gate |
| 227 | Buzzer |
| 228 | Multimeter |
| 229 | Soldering Iron |
| 230 | Solder Wire |
| 231 | PCB Board |
| 232 | Diode |
| 233 | Push Button |
| 234 | Relay |
| 235 | Potentiometer |

### Item Display
- Items rendered as colored cubes in-world (ITEM_COLORS dict)
- Held items shown in hand during first-person
- Hotbar shows selected item name text

---

## 7. Crafting System

### Grid Sizes
- **2x2**: From inventory (E key)
- **3x3**: At crafting table (right-click)

### Recipe Matching
- Shaped recipes with offset matching (recipe can be placed anywhere in the grid)
- Exact item matching (AIR required for empty slots)

### Complete Recipe List

#### Basic
| Recipe | Result | Count |
|--------|--------|-------|
| 1 Wood | 4 Planks | 4 |
| 2 Planks (vertical) | 4 Stick | 4 |

#### Tools
| Recipe | Result |
|--------|--------|
| 3 Planks + 2 Stick (T-shape) | Wood Pickaxe |
| 3 Planks + 2 Stick (L-shape) | Wood Axe |
| 2 Planks + 1 Stick (vertical) | Wood Sword |
| 3 Cobble + 2 Stick | Stone Pickaxe |
| 3 Cobble + 2 Stick | Stone Axe |
| 2 Cobble + 1 Stick | Stone Sword |
| 3 Iron + 2 Stick | Iron Pickaxe |
| 3 Iron + 2 Stick | Iron Axe |
| 2 Iron + 1 Stick | Iron Sword |
| 3 Diamond + 2 Stick | Diamond Pickaxe |
| 3 Diamond + 2 Stick | Diamond Axe |
| 2 Diamond + 1 Stick | Diamond Sword |
| 1 Diamond + 2 Stick | Diamond Shovel |

#### Armor (16 recipes)
- Leather: Helmet, Tunic, Pants, Boots
- Iron: Helmet, Chestplate, Leggings, Boots
- Gold: Helmet, Chestplate, Leggings, Boots
- Diamond: Helmet, Chestplate, Leggings, Boots

#### Food
| Recipe | Result | Count |
|--------|--------|-------|
| 3 Wheat (horizontal) | Bread | 1 |
| 2 Wheat (horizontal) | Cookie | 8 |

#### Blocks
| Recipe | Result | Count |
|--------|--------|-------|
| 4 Planks (2x2) | Crafting Table | 1 |
| 8 Cobblestone (hollow square) | Furnace | 1 |
| 1 Coal + 1 Stick (vertical) | Torch | 4 |
| 8 Sand (hollow square) | Glass | 8 |

#### Electronic (14 recipes)
| Recipe | Result |
|--------|--------|
| 1 Copper Block | 8 Copper Wire |
| 1 Gold Ingot | 4 Gold Wire |
| Planks/Wire/Planks (3x3) | Circuit Board |
| Coal+Stick+Coal | 4x 100R Resistor |
| Iron+Glass+Iron | 2x Ceramic Capacitor |
| Iron+Glass+Iron / Gold+Air+Gold | Electrolytic Capacitor |
| Silicon+Wire+Silicon / Wire+Silicon+Wire | NPN Transistor |
| Silicon+Wire+Silicon / Wire+Silicon+Wire | PNP Transistor |
| Glass+Coal+Glass / Coal+Glass+Coal | 2x Red LED |
| Glass+Cactus+Glass / Cactus+Glass+Cactus | 2x Green LED |
| Glass+Water+Glass / Water+Glass+Water | 2x Blue LED |
| Iron+Coal+Iron / Iron+Coal+Iron / Iron+Coal+Iron | 9V Battery |
| Iron+Coal+Iron | 2x AA Battery |
| Iron+Stick+Iron | Switch |
| Iron+Stick | Button |
| Sand+Coal+Sand | 2x Silicon Wafer |
| 9 Copper Wire (3x3) | Copper Block |
| Circuit+Transistor+Circuit / Resistor+Cap+Resistor / Circuit+Wire+Circuit | NE555 Timer |
| Circuit+Transistor+Circuit / Wire+Wire+Wire | AND Gate |
| Transistor+Air+Transistor / Wire+Circuit+Wire | OR Gate |
| Resistor+Transistor+Circuit / Wire+Wire+Wire | NOT Gate |
| Iron+Wire+Iron / Wire+Coal+Wire / Iron+Wire+Iron | Buzzer |
| Glass+Iron+Glass / Wire+Circuit+Wire / Iron+Coal+Iron | Multimeter |
| Iron+Iron+Stick / Coal+Wire+Stick | Soldering Iron |
| Gold+Gold | 4x Solder Wire |
| Planks+Wire+Planks / Wire+Circuit+Wire / Planks+Wire+Planks | PCB Board |
| Silicon+Wire | 2x Diode |
| Resistor+Stick+Iron | Potentiometer |

---

## 8. Furnace System

### UI
- Opens on right-click of Furnace block
- 3 slots: Input, Fuel, Output
- Visual flame indicator when fuel is burning
- Progress arrow shows smelt progress
- Player inventory displayed below

### Smelting Recipes
| Input | Output |
|-------|--------|
| Raw Iron | Iron Ingot |
| Raw Gold | Gold Ingot |
| Sand | Glass |
| Cobblestone | Stone |
| Raw Beef | Steak |
| Raw Chicken | Cooked Chicken |
| Raw Mutton | Cooked Mutton |
| Potato | Bread |

### Fuel Values (seconds of burn time)
| Fuel | Burn Time |
|------|-----------|
| Coal | 8.0s |
| Planks | 1.5s |
| Wood | 1.5s |
| Stick | 0.5s |

---

## 9. Combat & Damage

### Attack Mechanics
- Left-click within reach (6 blocks) deals damage
- Attack cooldown: 0.2 seconds between attacks
- Tool damage: Sword damage varies by tier (3.0 wood to 7.0 diamond)

### Damage Sources
| Source | Damage |
|--------|--------|
| Fall (per block beyond 3) | 1.0 per block |
| Zombie melee | 3.0 |
| Skeleton melee | 4.0 |
| Starvation | 1.0 per tick (when hunger=0) |
| Void (Y < -10) | Instant death |

### Damage Reduction
- Armor defense points reduce damage: `damage *= max(0.2, 1.0 - armor_def / 25.0)`
- Diamond full set: 20 defense = 80% reduction
- Iron full set: 15 defense = 60% reduction
- Leather full set: 7 defense = 28% reduction

### Death
- Health reaches 0 triggers death
- Death screen shows "You Died" with respawn button
- 3-second respawn timer
- Respawn at world spawn point
- Inventory preserved (no item drops on death)

---

## 10. Entity System

### Mob Types

#### Passive Mobs
| Mob | Health | Speed | Drops | Spawn |
|-----|--------|-------|-------|-------|
| Cow | 10 | 2.0 | 1-3 Raw Beef, 0-2 Leather | Day, plains/forest |
| Sheep | 8 | 2.0 | 1-2 Raw Mutton, 1 Wool | Day, plains |
| Chicken | 4 | 2.5 | 1 Raw Chicken, 0-2 Feather | Day, plains |

#### Hostile Mobs
| Mob | Health | Speed | Damage | Drops | Spawn |
|-----|--------|-------|--------|-------|-------|
| Zombie | 20 | 2.5 | 3 | 0-1 Iron, 0-2 Arrow | Night, any biome |
| Skeleton | 20 | 2.8 | 4 | 1-2 Bone, 0-3 Arrow | Night, any biome, 8 block range |

### AI System
- **Wander**: Random movement within home area
- **Chase**: Move toward player when within detection range
- **Flee**: Move away from player (passive mobs when attacked)
- **Despawn**: Entities beyond spawn radius removed
- Spawn radius: 15-50 blocks from player

### OBJ Model Loading
- Cow, Sheep, Chicken, Zombie, Skeleton loaded from `.obj` files
- Parts separated for animation (head, legs, body, torso)
- MTL materials with texture support
- Per-part rendering for walk animation

### Item Drops
- Spawned when mobs die or blocks break
- Float in world with bob animation
- 30-tick pickup delay after spawn
- Picked up by walking near (2.5 block radius)
- Added to player inventory on pickup
- Dropped on ground if inventory full

---

## 11. Armor System

### Armor Slots
4 slots: Helmet (0), Chestplate (1), Leggings (2), Boots (3)

### Materials and Defense
| Material | Helmet | Chest | Legs | Boots | Total |
|----------|--------|-------|------|-------|-------|
| Leather | 1 | 3 | 2 | 1 | 7 |
| Iron | 2 | 6 | 5 | 2 | 15 |
| Gold | 2 | 6 | 5 | 2 | 15 |
| Diamond | 3 | 8 | 6 | 3 | 20 |

### Equipping
- Right-click while holding armor item
- Swaps with currently equipped armor in that slot
- Visual rendering on player body in third-person mode

### Armor Colors
Each material has a distinct color for third-person rendering:
- Leather: Brown (0.55, 0.35, 0.18)
- Iron: Silver (0.70, 0.68, 0.65)
- Gold: Yellow (0.85, 0.75, 0.20)
- Diamond: Cyan (0.25, 0.80, 0.85)

---

## 12. Food & Hunger

### Hunger Mechanics
- Maximum hunger: 20
- Maximum saturation: 20
- **Drain rate**: 0.01 base per second
  - Walking: 2x drain
  - Sprinting: 4x drain
- Saturation drains before hunger
- When saturation = 0, hunger drains at 3x rate

### Starvation
- At hunger = 0: 1 HP damage every 4 seconds

### Natural Regeneration
- Requires: hunger >= 17 AND saturation > 0 AND standing still
- Heals 1 HP every 0.5 seconds
- Consumes 1.0 saturation per heal tick

### Eating
- Right-click while holding food
- 1.6 second eat duration
- Progress bar shown in HUD
- Interrupted by movement or taking damage
- Food consumed and hunger restored on completion

---

## 13. Tool System

### Tool Tiers
| Tier | Material | Mining Speed | Damage |
|------|----------|-------------|--------|
| Wood | Planks | 2.0 | 1.5-3.0 |
| Stone | Cobblestone | 3.0 | 2.0-4.0 |
| Iron | Iron Ingot | 4.0 | 2.5-5.0 |
| Diamond | Diamond | 6.0 | 3.0-7.0 |

### Tool Types
- **Pickaxe**: Effective on stone, ores, glass, brick
- **Axe**: Effective on wood, planks
- **Sword**: Extra damage to entities
- **Shovel**: Effective on dirt, grass, sand, gravel

### Tool Effectiveness
Using the correct tool type gives faster mining. Wrong tool still works but slower.

---

## 14. Block Drops & Item Pickup

### Block Drop Rules
| Block | Drop |
|-------|------|
| Grass | 1 Dirt |
| Leaves | 0-1 Apple, 0-2 Stick |
| Coal Ore | 1 Coal |
| Iron Ore | 1 Raw Iron |
| Gold Ore | 1 Raw Gold |
| Diamond Ore | 1 Diamond |
| Glass | Nothing |
| Cactus | Nothing |
| Bedrock | Nothing |
| All other blocks | Themselves |

### Item Pickup
- Items spawn as floating entities at block break location
- Player picks up items within 2.5 block radius
- Items added to first available inventory slot
- If inventory full, items remain on ground
- 30-tick (1.5s) pickup delay after spawn
- Items bob up and down with rotation

---

## 15. Texture System

### Procedural Generation
All textures are 16x16 pixel numpy arrays generated at startup. No image files used for blocks.

### Block Textures (42 textures)
Each block has up to 3 textures: top, bottom, side (some share).

| Texture | Base Color | Features |
|---------|-----------|----------|
| Grass Top | Green (30,180,50) | Random green variation |
| Grass Side | Dirt base | Green strip at top (rows 13-15) |
| Dirt | Brown (134,96,67) | Noise variation |
| Stone | Gray (140,140,140) | Darker spots, cracks |
| Wood Top | Tan (150,120,60) | Ring pattern |
| Wood Side | Brown (120,80,30) | Vertical bark lines |
| Leaves | Dark green (46,148,31) | Sparse pattern, 30% transparent holes |
| Sand | Tan (224,210,148) | Fine grain noise |
| Water | Blue (56,115,217) | Semi-transparent |
| Cobblestone | Gray (122,122,122) | Stone pattern with cracks |
| Planks | Tan (184,148,82) | Horizontal wood grain |
| Bedrock | Dark gray (72,72,72) | Heavy noise |
| Coal Ore | Gray base | Black coal specks |
| Iron Ore | Gray base | Pinkish-brown specks |
| Gold Ore | Gray base | Yellow-gold specks |
| Diamond Ore | Gray base | Cyan specks |
| Glass | Light blue (210,235,250) | Transparent with white border |
| Brick | Red (174,82,72) | Brick pattern with mortar lines |
| Snow | White (240,245,255) | Slight variation |
| Snow Side | Dirt base | White strip at top (rows 13-15) |
| Cactus | Green (56,158,46) | Vertical ridges |
| Torch | Yellow-orange | Flame pattern |
| Gravel | Gray-brown | Coarse grain |
| Crafting Table Top | Wood with grid pattern |
| Crafting Table Side | Wood with tool marks |
| Furnace Top | Gray with circle |
| Furnace Side | Stone with dark opening |
| Coal Ore | Stone with black spots |
| Iron Ore | Stone with tan spots |
| Gold Ore | Stone with yellow spots |
| Diamond Ore | Stone with cyan spots |

### Texture Atlas
- All textures packed into a single atlas at startup
- UV coordinates mapped per-face per-block
- Texture bind once per render pass (opaque then transparent)

---

## 16. Rendering Engine

### OpenGL Setup
- Immediate mode (glBegin/glEnd)
- Depth testing enabled
- Back-face culling disabled (for correct winding with transparency)
- GL_COLOR_MATERIAL for vertex-based coloring
- GL_LIGHT0 for ambient directional lighting
- Perspective projection (70 degree FOV)

### Chunk Rendering
- Display lists (glNewList/glCallList) for each chunk
- Opaque blocks rendered first, then transparent blocks
- Face culling: Only faces adjacent to transparent blocks are rendered
- Cross-chunk face culling at borders

### Face Winding
All 6 face directions have correct outward-pointing normals:
- +Y (top), -Y (bottom), +X, -X, +Z, -Z

### UV Mapping
Each face direction maps texture coordinates correctly:
- Top/Bottom: XZ plane to UV
- Sides (+X/-X): ZY plane to UV
- Front/Back (+Z/-Z): XY plane to UV

### Lighting
- Face-based shading: top=1.0, front=0.85, sides=0.7, bottom=0.5
- Per-block color tinting for natural variation
- GL_COLOR_MATERIAL with GL_AMBIENT_AND_DIFFUSE

### Particle System
- Break particles: 12 per block, inherit block color
- Hit particles: 8 particles on entity hit
- Gravity-affected, fade over time
- Drawn as GL_POINTS

### Cloud Renderer
- Flat cloud layer at high altitude
- Noise-based density map (35% coverage)
- Scrolls with time

### Sky Rendering
- Gradient sky color based on time of day
- Stars visible at night
- Moon with phases

### Player Body (Third Person)
- Head (cube with eyes/pupils)
- Body (torso cube)
- 2 Arms (with swing animation)
- 2 Legs (with walk animation)
- Armor overlay on each body part
- Walk cycle synced to movement
- Arm swing: 45 degrees during walk

---

## 17. HUD & UI

### HUD Elements
| Element | Position | Description |
|---------|----------|-------------|
| Crosshair | Center | White + shape |
| Health bar | Bottom-left | Heart icons (red) |
| Hunger bar | Bottom-center-right | Gold squares |
| Armor bar | Above health | Shield icons |
| Hotbar | Bottom-center | 9 inventory slots |
| Selected item name | Above hotbar | White text with shadow |
| Experience bar | Above hotbar | Green bar |
| FPS counter | Top-left | Frame rate |
| Eating overlay | Center | Progress bar during eating |

### Death Screen
- Dark overlay
- "You Died" text
- Respawn button
- Health and hunger shown

### Inventory UI
- Full inventory overlay when E pressed
- 2x2 crafting grid (or 3x3 at crafting table)
- Armor slots with item display
- Mouse click to move items between slots
- Right-click to split stacks

### Crafting UI
- Shows matched recipe result
- Click to craft (consumes ingredients)
- Real-time recipe matching as items placed

### Furnace UI
- Input slot (left)
- Fuel slot (bottom-left)
- Output slot (right)
- Flame indicator (burning fuel)
- Progress arrow (smelting progress)
- Timer display

---

## 18. Menu System

### Main Menu
- **Play**: Opens world selection
- **Multiplayer**: Host or Join game
- **Settings**: Game settings
- **Credits**: Project credits

### World Selection
- List of saved worlds
- Shows: name, gamemode, play time, seed
- Buttons: Play, Delete

### World Creation
- World name input
- Gamemode selection (Creative/Survival)
- Seed input (optional)
- Show coordinates toggle
- Create button

### Pause Menu
- Resume
- Settings
- Save & Quit (saves player data and world state)

### Settings
- Render distance
- Mouse sensitivity
- Music volume
- FOV

---

## 19. Sound System

### Audio Settings
- Sample rate: 22050 Hz
- Channels: Mono (converted to stereo for pygame)
- Buffer: 512 samples

### All Sounds (25+ procedural)

#### Block Sounds
| Sound | Method | Description |
|-------|--------|-------------|
| break_stone | crunch | Low-frequency crunch with noise |
| break_dirt | crunch | Soft earthy crunch |
| break_wood | crunch | Higher frequency wood snap |
| break_grass | crunch | Leafy rustle |
| break_glass | shatter | High-frequency noise burst |
| break_sand | crunch | Soft sandy crunch |
| place_stone | thud | Low thud |
| place_dirt | thud | Soft earth thud |
| place_wood | thud | Wooden thud |
| place_glass | tink | High-pitched tink |

#### Player Sounds
| Sound | Method | Description |
|-------|--------|-------------|
| step_stone | step | Quick stone tap |
| step_dirt | step | Soft earth tap |
| step_wood | step | Wooden tap |
| step_grass | step | Grass rustle |
| step_sand | step | Sandy shuffle |
| jump | jump | Rising tone swoosh |
| land | thud | Impact thud |
| hurt | hurt | Pain vocalization with pitch wobble |
| death | death | Descending tone |

#### UI Sounds
| Sound | Method | Description |
|-------|--------|-------------|
| click | click | Quick high-frequency click |
| place_fail | buzz | Error buzz (slight detune) |

#### Entity Sounds
| Sound | Method | Description |
|-------|--------|-------------|
| cow | moo | Low moo with harmonics |
| chicken | cluck | High pecking sounds |
| sheep | baa | Mid-range bleat |
| zombie | groan | Low guttural groan |
| skeleton | rattle | Bone rattling noise |
| entity_hurt | hit | Quick impact |
| entity_death | pop | Quick pop |

### Sound Generation
All sounds generated from scratch using:
- sine, square, saw, noise waveforms
- ADSR envelopes (attack, decay, sustain, release)
- Frequency modulation
- Noise mixing
- Exponential decay

---

## 20. Atmosphere & Weather

### Day/Night Cycle
- Time variable: 0.0 to 1.0
- Default: 0.25 (noon)
- Day speed: 0.005 per frame
- G key freezes time
- `/time day/night/noon/midnight` commands

### Weather System
- **Clear**: No precipitation
- **Rain**: Visual rain particles, ambient sound
- **Thunder**: Lightning flashes, rain

### Ambient Particles
- **Daytime**: Dust/pollen particles (light colors, slow drift)
- **Nighttime**: Mist particles (blue-gray, slow movement)
- **Fireflies**: Yellow glowing particles at night

### Lightning
- Random flashes illuminate the scene
- White flash overlay with fade
- Sound effect on strike

### Sky Rendering
- Gradient sky color interpolation (day: blue, sunset: orange, night: dark blue)
- Star field at night (points with varying brightness)
- Moon with simple rendering

---

## 21. Electronics System

### Circuit Simulator
- Node-based circuit graph
- Power sources (batteries) provide voltage
- Components connect via wire blocks
- Signal propagation through component chain

### Component Types
| Type | Variants | Behavior |
|------|----------|----------|
| Resistor | 100R, 1K, 10K | Limits current flow |
| Capacitor | Ceramic, Electrolytic, Tantalum | Stores charge. Electrolytic/Tantalum are POLARIZED. |
| Transistor | NPN, PNP | Signal amplification/switching |
| LED | Red, Green, Blue, White | Emits light when powered (forward voltage: 2.0-3.2V) |
| Diode | - | One-way current flow (0.7V drop) |
| IC | NE555, AND, OR, NOT, NAND, NOR | Logic processing |
| Battery | 9V, AA | Power source |
| Wire | Copper, Gold | Signal conductor |
| Switch | - | Manual on/off |
| Button | - | Momentary activation |
| Buzzer | - | Audio output |

### Polarity System
- Components have polarity (positive/negative/neutral)
- **Capacitors** (electrolytic, tantalum) and **LEDs** have polarized terminals
- **Wrong polarity causes explosion** (visual effect + block destruction)

### Circuit Board
- Physical base for component placement
- Visual trace routing
- Schematic display mode

---

## 22. Structures

### Structure Types

| Structure | Size | Materials | Location |
|-----------|------|-----------|----------|
| Small House | 7x5x7 | Wood, Planks, Glass | Plains, Forest |
| Stone Tower | 5x12x5 | Cobblestone, Stone | Any biome |
| Ruins | 8x4x8 | Stone, Brick, Gravel | Any biome |
| Well | 5x3x5 | Cobblestone, Water | Plains |
| Garden | 6x2x6 | Planks (fence), Flowers | Plains |
| Electronics Factory | 10x8x10 | Iron, Glass, Circuit Board | Random chunks |

### Electronics Factory Loot
Contains chests with randomized electronic components:
- Resistors, Capacitors
- Transistors, LEDs
- Circuit Boards, Batteries
- Wire, Switches

---

## 23. Multiplayer

### Architecture
- **TCP**: Reliable messages (join, chat, block changes, position)
- **UDP**: Fast position updates, server discovery
- **Server**: Hosted by one player (GameServer class)
- **Clients**: Connect via IP or LAN discovery

### Server Features
- Player count tracking (max 8)
- Position synchronization
- Block change broadcasting
- Chat messages
- Server discovery via UDP broadcast

### Client Features
- Auto-discover servers on LAN
- Connect via IP:port
- Receive position updates
- Send block changes
- Chat system

### Voice Chat (see Section 24)

---

## 24. Voice Chat

### Architecture
- **UDP** for audio transmission
- **Proximity-based**: Closer players hear louder
- **Push-to-talk** (V key)
- **Configurable**: Can be disabled

### Audio Settings
- Sample rate: 16000 Hz (lower for network efficiency)
- Channels: Mono
- Chunk size: 1024 samples

### Features
- Volume attenuation by distance
- Mute/unmute toggle
- Voice activation mode
- Per-player volume based on distance

---

## 25. Console/Terminal

### Access
- Press `/` to open (cheats must be enabled)
- Command history (up/down arrows)
- Tab completion (planned)

### Commands
| Command | Usage | Description |
|---------|-------|-------------|
| `/help` | - | List all commands |
| `/give <item> [count]` | `/give diamond 64` | Give items to player |
| `/tp <x> <y> <z>` | `/tp 0 100 0` | Teleport to coordinates |
| `/time <day/night/noon/midnight>` | `/time night` | Set time of day |
| `/gamemode <creative/survival>` | `/gamemode survival` | Change gamemode |
| `/heal` | - | Full health and hunger |
| `/kill` | - | Kill player (survival only) |
| `/fly` | - | Toggle flight (creative only) |
| `/speed <normal/fast/insane>` | `/speed fast` | Change movement speed |
| `/spawn` | - | Teleport to world spawn |
| `/seed` | - | Show world seed |
| `/clear` | - | Clear entire inventory |
| `/fill <item>` | `/fill dirt` | Fill hotbar with item |
| `/summon <mob>` | `/summon zombie` | Spawn entity nearby |
| `/weather <clear/rain/thunder>` | `/weather rain` | Change weather |
| `/invincible` | - | Toggle invincibility |

### Item Name Matching
Commands accept item names (case-insensitive):
- Block names: "grass", "stone", "diamond_ore"
- Item names: "diamond", "iron_ingot", "cooked_beef"
- Partial matching supported

---

## 26. Developer Tools

### Debug Overlay (Alt+F2)
Toggle with Alt+F2. Shows:

**Player Info:**
- XYZ position (2 decimal places)
- Current chunk coordinates
- Velocity vector
- On ground / Flying status
- Health and Hunger bars
- Saturation value
- Armor equipped and total defense
- Creative mode / Dead status

**World Info:**
- Loaded chunks count
- Dirty chunks count
- Pending chunks count
- Render distance

**Target Block Info (crosshair):**
- Block position [X, Y, Z]
- Block name and ID
- Solid/transparent status
- Place position
- Face direction hit (top/bottom/left/right/front/back)

**Block Neighbor Info:**
- All 6 neighbors with positions
- Block names and solid status

**Block Data JSON:**
```json
{
  "id": 1,
  "name": "Grass",
  "solid": true,
  "position": [0, 64, 0],
  "faces": {
    "+Y": "Air", "-Y": "Dirt",
    "+X": "Stone", "-X": "Stone",
    "+Z": "Stone", "-Z": "Stone"
  }
}
```

**Other:**
- Day time value and speed

---

## 27. OBJ Model Loading

### Supported Features
- Wavefront OBJ format
- MTL material files
- Texture coordinates
- Group/object separation for part animation
- Per-part rendering
- Scale factor
- Automatic centering

### Loaded Models
| Model | Parts | File |
|-------|-------|------|
| Cow | backleftleg, backrightleg, frontrightleg, frontleftleg, cowmilkarea, head, torso | cow.obj |
| Sheep | torso, head, frontleftleg, backleftleg, backrightleg, frontrightleg | sheep.obj |
| Chicken | torso, leftleg, rightleg, head | chicken.obj |
| Zombie | head, body, leftarm, rightarm, leftleg, rightleg | zombie.obj |
| Skeleton | head, body, leftarm, rightarm, leftleg, rightleg | skeleton.obj |

### Mob Renderer
- `load_model(entity_type, obj_path, scale)`: Load OBJ for entity type
- `draw_mob(entity_type, pos, rotation, walk_cycle, hit_flash)`: Render with animation
- `draw_part(entity_type, part_name)`: Render individual part
- Walk animation: Legs swing based on walk_cycle parameter
- Hit flash: Red tint when damaged

---

## 28. World Management

### Save System
- Worlds stored in `saves/` directory
- Each world has its own folder
- Chunk data: numpy arrays saved as raw binary
- Player data: JSON (position, health, hunger, armor, inventory, selected slot)
- World metadata: JSON (name, seed, gamemode, creation time, play time)

### Save Data Format
```json
{
  "name": "My World",
  "seed": 42,
  "gamemode": "creative",
  "created": "2025-01-01 12:00:00",
  "play_time": 3600.0,
  "show_coords": true,
  "cheats": false
}
```

### Player Data Format
```json
{
  "pos": [0.5, 100.0, 0.5],
  "yaw": 0.0,
  "pitch": 0.0,
  "health": 20.0,
  "hunger": 20.0,
  "armor": [0, 0, 0, 0],
  "inventory": {
    "hotbar": [{"item": 1, "count": 64}, ...],
    "main": [[{"item": 0, "count": 0}, ...], ...]
  },
  "selected_slot": 0
}
```

### Gamemode Persistence
- Gamemode saved with world metadata
- Creative mode: Unlimited blocks, flying, no hunger/damage
- Survival mode: Limited resources, hunger, fall damage, mob damage

---

## 29. Settings

| Setting | Default | Range | Description |
|---------|---------|-------|-------------|
| Render distance | 4 | 2-8 | Chunk render distance |
| Sensitivity | 0.15 | 0.05-0.5 | Mouse look sensitivity |
| Volume | 0.5 | 0.0-1.0 | Master volume |
| FOV | 70 | 60-110 | Field of view |

---

## 30. Credits

### Made by
**AntacidDT** (GitHub: https://github.com/AntacidDT)

### Tools Used
- **Python 3** - Core language
- **PyOpenGL** - Graphics rendering
- **Pygame** - Windowing, audio, input, fonts
- **NumPy** - Array math, noise generation
- **Perlin Noise** - Terrain generation
- **Git** - Version control

### Special Thanks
- All procedural content generated from code - zero external assets required
- Built from scratch, works on school computers without pip install (dependencies bundled in `lib/`)

---

## File Structure

```
MCbyMimo/
├── run.py                  # Entry point
├── main.py                 # Game orchestrator (870+ lines)
├── constants.py            # All IDs, names, properties (600+ lines)
├── world.py                # World gen, chunks, mesh building (600+ lines)
├── player.py               # Player mechanics (370+ lines)
├── renderer.py             # HUD, particles, clouds, player body (430+ lines)
├── entities.py             # Mobs, AI, item drops (610+ lines)
├── textures.py             # Procedural texture generation (380+ lines)
├── crafting.py             # Recipes (280+ lines)
├── inventory_ui.py         # Inventory and crafting UI (430+ lines)
├── furnace_ui.py           # Furnace smelting UI (420+ lines)
├── sounds.py               # Procedural sound generation (330+ lines)
├── terminal.py             # Console commands (440+ lines)
├── atmosphere.py           # Weather, particles, sky (310+ lines)
├── circuits.py             # Electronics simulation (300+ lines)
├── factory.py              # Factory structure (200+ lines)
├── structures.py           # World structures (250+ lines)
├── network.py              # Multiplayer server/client (580+ lines)
├── voice.py                # Voice chat (290+ lines)
├── menu.py                 # Main/pause/settings menus (400+ lines)
├── world_screens.py        # World selection/creation (500+ lines)
├── multiplayer_screens.py  # Host/join screens (310+ lines)
├── credits.py              # Credits screen (50+ lines)
├── text_renderer.py        # OpenGL text rendering (100+ lines)
├── obj_loader.py           # OBJ model loading (390+ lines)
├── builder.py              # Structure builder tool (660+ lines)
├── minecraft.py            # Legacy single-file version (1100+ lines)
├── world_manager.py        # Save/load management (150+ lines)
├── lib/                    # Bundled dependencies
│   ├── OpenGL/             # PyOpenGL
│   ├── pygame/             # Pygame
│   ├── numpy/              # NumPy
│   └── noise/              # Perlin noise
├── mobs(withtextures)/     # OBJ mob models + textures
│   ├── cow.obj, sheep.obj, chicken.obj, zombie.obj, skeleton.obj
│   └── *.mtl, *.png
├── saves/                  # World save data
└── projectcause.md         # This file
```

---

## Version History

### V1.9 - The General Update
- Block drops (specific items per block)
- Item pickup system
- Hunger overhaul (saturation, starvation, regen)
- Food system (14 food types with eating mechanic)
- Armor system (16 armor items, 4 materials, damage reduction)
- Furnace smelting UI (8 recipes, 4 fuels)
- Diamond tier (ore generation, tools, armor)
- Player body rendering (third-person with walk animation)
- Third-person camera (F5 toggle)
- 80+ crafting recipes (including armor, food, electronics)
- Animal drops (raw food, materials)
- Block tinting (per-block color variation)
- Developer debug overlay (Alt+F2)
- Chunk loading optimization (time-budgeted, pre-generation)
- Collision fixes (swept Y-axis, unloaded chunk safety)
- Face orientation fixes (correct winding order)
- Block placement validation (items can't be placed as blocks)

### V1.8 - The Electronics Update
- Electronics factory structures with loot
- Circuit simulation engine
- Electronic components (resistors, capacitors, transistors, ICs, LEDs)
- Logic gates (AND, OR, NOT, NAND, NOR)
- NE555 timer
- Polarity system with explosions
- 14+ electronic crafting recipes

### V1.7 - The Atmosphere Update
- Weather system (rain, thunder)
- Lightning with visual flash
- Ambient particles (dust, fireflies, mist)
- Star field and moon
- Day/night cycle with sky gradient

### V1.6 - The Multiplayer Update
- LAN server hosting
- TCP+UDP networking
- Player position sync
- Server discovery broadcast
- Voice chat (proximity-based UDP)

### V1.5 - The Sound Update
- 25+ procedural sound effects
- Block breaking/placing sounds per material
- Footstep sounds per surface
- Entity sounds (moo, cluck, baa, groan, rattle)
- Player hurt/death sounds
- UI click sounds

### V1.4 - The Entity Update
- OBJ model loading with MTL materials
- Per-part rendering for animation
- AI system (wander, chase, flee)
- Passive mobs (cow, sheep, chicken)
- Hostile mobs (zombie, skeleton)
- Entity drops on death
- Spawn/despawn system

### V1.3 - The Structure Update
- Small house generation
- Stone tower generation
- Ruins generation
- Well generation
- Garden generation
- Structure builder tool with JSON export

### V2.2 - Natural Disasters Update
- 15 natural disasters with biome-specific triggers
- Chain event system (earthquake->tsunami, lightning->wildfire, meteor->volcanic)
- Screen shake with intensity scaling
- Disaster warning HUD with name and timer
- DisasterManager for cooldowns and active disaster tracking
- DisasterRenderer integration with camera offset

### V2.1 - Better Physics Update
- Explosion system with radius, hardness-based destruction, entity damage
- Falling block entities (explosion debris) with physics
- Fluid simulation (water/lava spread, wind-affected)
- Wind system (direction, gusts, affects fluids+particles+rain)
- Block gravity (sand/gravel fall)
- TNT and Obsidian blocks
- Lava damage and swim physics
- New biome blocks: Podzol, Mycelium, Sponge, Glowstone

### V2.0 - Settings & IO Update
- Pixel font rendering
- Settings manager (physics/world/screen)
- IO trigger system (13 trigger types)
- World creation UI with tabbed settings
- Stats display on world select
- Session stat tracking

### V1.2 - The Cave Update
- 3D Perlin noise cave generation
- Cave entrances
- Gravel floors
- Deep lava
- Coal, iron, gold ore generation

### V1.1 - The Biome Update
- 6 biomes (Plains, Forest, Desert, Snow, Jungle, Ocean)
- Biome-specific terrain
- Tree generation
- Flower generation
- Cactus generation

### V1.0 - Initial Release
- Core voxel engine
- Chunk-based world
- Block breaking/placing
- Basic inventory
- Crafting system
- Creative/survival modes
- Save/load system
- Terminal commands
- Credits screen

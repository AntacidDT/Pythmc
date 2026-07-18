# Pythmc - Minecraft clone written using Python3.

3D Voxel Survival and Creative game, with unique features.

*Engine*: Pythkernel (Specialized for Pythmc)

To run the game:
In Windows, double click run.bat
In Linux or MacOS: ./run.sh 
Or just do python3 run.py

Prerequisites: Python 3.8 or newer.
Other necessary Numpy or OpenGL is bundled in the /lib folder.

*Controls* 

| Key | Action |
|-----|--------|
| WASD | Move |
| Mouse | Look around |
| Space | Jump / Fly up / Swim up |
| Shift | Sneak (ground) / Fly down |
| Ctrl | Sprint (also prevents sneaking) |
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

Updates:
V1.3: The Structure Update
brought small house generations, ruins, wells, gardens, structure builder tool, stone tower generation.

V1.4: The Entity Update
brought OBJ Models, per part rendering for animation, wander chase flee system, passive and hostile mobs, entity drops on death and spawn/despawn system.

V1.5: The Sound Update
brought 25 procedural sound effects, block breaking and placing sounds per material, footstep sounds per surface, entity sounds, player hurt/death sounds, UI click sounds.

V1.6: The Multiplayer Update
LAN Server Hosting, TCP+UDP Hosting, Player pos sync, Server discovery broadcast, Voice chat (proximity based UDP)

V1.7: The Atmosphere Update
Weather system, lightning with visual flash, ambient particles, star field and moon, day night cycle with sky gradient.

V1.8: The Wires and Silicon Update.
electronic factory structures with loot, circuit simulation engine, electronic components (resistors, caps, transistors, IC's, LEDs), Logic gates (AND, OR, NOT, NAND, NOR), NE555 Timer IC, Polarity system with explosions, 14+ electronic crafting recipes.

V1.9: The General Update.
Block drops, item pickup, hunger overhaul, food system, armor system, furnace smelting UI, diamond tier, player body rendering, third person camera, 80+ crafting recipes, animal drops, block tinting (per block color variation), developer debug (ALT F2), chunk loading optimization (Time budgeted, pre-generation), collision fixes, face orientation fixes, block placement validations (items can't be placed as blocks).

V2.0: Settings and IO Update.
Pixel font rendering, settings manager, io trigger system, world creation UI, stats display on world select, session stat tracking

ABOUT IO SYSTEM;
IO systems work by linking events in game (eg. player health on 5 heart) to terminal commands your OS can execute. Its set only by player, and in Multiplayer, a host can't execute commands on someone elses PC, only players can set it. Worlds have IO Toggles that let you switch off and on the IO system for that specific world.

V2.1: Better Physics Update.
Explosions system with radius, hardness based destruction, entity damage. falling block entities, with physics. fluid simulation, wind system (direction, gusts, affects fluids, particles and rain), bloc gravity (sand/gravel fall), tnt and obsidian, lava damage and swim pjysics. new biome blocks: podzol, mycelium, sponge, glowstone.

V2.2: Natural Disasters Update
15 natural disasters with biome specific triggers, chain event system, screen shake with intensity scaling, disastermanager for cooldowns and active disaster tracking, disasterrenderer for integ. with camera offset.

V2.3: The CUDA Update.
added support for CUDA/CuPy. NVIDIA GPU detection at boot, and if its detected and theres CUDA Toolkit then it activates, makes NVIDIA devices run potentially faster. GPU Terrain noise, cave carving, particle physics, fluid spread, Settings/GPU Tab for on off toggle, and safe cpu fallback when CUDA unavailable.

V2.4: The Better Quality Update
Outlined pixel font, character customization, 3d world background on all menu screens, first person hand, multiplayer name tags, sneaking mechanic, hud fix.

V2.5: Stability and Optimizations
crash fixes and null safety, fixed missing imports, try/expect crash reco, around all ensure world methods, around chunk gen with fallback, sound manager wrapped in try/except, memory cleanup, performance tuning.

V2.6: Loading Screen, Music and Icon.
Pythmc logo in taskbar, Animated loading screen, MIDI music player (37 of MIDI compositions + you can add/remove any you want in the music folder)
Clothing system. 37 MIDI Tracks (Terra Serafina series)

V2.7: UI Overhaul.
main menu restructured, 4 vertical tabs (Play, Multiplayer, Customize, Settings), Each tab opens a submenu panel with relevant buttons, play -> singleplayer, structure builder. Multiplayer -> host game, join game. Customize -> Character. 
Settings -> Settings, Credits, Quit Game.

*World*
- Perlin noise terrain generation
- 6 biomes: Plains, Forest, Desert, Snow, Jungle, Ocean
- Caves with 3D noise carving
- Ore generation: Coal, Iron, Gold, Diamond (below Y=15)
- 6 structures: Houses, Towers, Ruins, Wells, Gardens, Electronics Factories
- Trees, flowers, cacti
- Chunk-based rendering with threaded generation
- Save/load world system

*Gameplay (survival mode)*
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

*Mobs*
- *Passive:* Cow, Sheep, Chicken (OBJ models with walk animation)
- *Hostile:* Zombie, Skeleton (AI with chase/flee states)
- Item drops from blocks and mobs

*Electronics (Unique to Pythmc)*
- Resistors, Capacitors (polarized!), Transistors, ICs
- NE555 timer, Logic gates (AND, OR, NOT, NAND, NOR)
- LEDs, Batteries, Switches, Wires
- Polarity system — wrong polarity causes explosions
- Electronics Factories with loot

*Multiplayer*
- LAN server hosting (TCP + UDP)
- Player position sync
- Server discovery broadcast
- Proximity-based voice chat

*Atmosphere*
- Day/night cycle with sky gradient
- Weather: Rain, Thunder with lightning
- Ambient particles: Dust, Fireflies, Mist
- Stars and moon

*Natural Disasters*
- 15 disasters: Earthquake, Tornado, Tsunami, Sandstorm, Blizzard, Volcanic Eruption, Wildfire, Whirlpool, Meteor Strike, Sinkhole, Avalanche, Mudslide, Ice Storm, Flash Flood, Lightning Barrage
- Biome-specific triggers (desert gets sandstorms, ocean gets tsunamis)
- Chain events (earthquake can trigger tsunami, lightning can trigger wildfire)
- Screen shake with intensity scaling
- HUD warning with disaster name and timer

*Better Quality*
- Outlined pixel font (1px black border for readability)
- Character customization (skin, shirt, pants, eyes color pickers)
- 3D world background on all menu screens
- First-person hand + held block rendering
- Multiplayer name tags (billboard text above heads)
- Sneaking mechanic (Shift on ground: slower speed, edge protection, crouch view)
- Survival HUD fix (item name above hearts, no overlap)

*Loading, Music and Icon*
- Game window icon (Pythmc logo)
- Animated loading screen with progress bar, world name, and gameplay tips
- Procedural ambient background music (layered pads, arpeggios, bass)
- Music auto-plays during gameplay, loops seamlessly

*Technical*
- 25+ procedural sound effects (no audio files)
- Procedural texture generation (no image files for blocks)
- OBJ model loading with MTL materials
- Third-person camera with player body rendering
- Developer debug overlay (Alt+F2)
- 25+ console commands
- V2.3: NVIDIA CUDA GPU acceleration (CuPy)
  - Batch terrain noise generation on GPU
  - GPU-accelerated cave carving (3D noise)
  - GPU particle physics update
  - GPU fluid spread simulation
  - Auto-detects NVIDIA GPU, on/off toggle in Settings > GPU

*Architecture*

35 Python source files, ~16,000+ lines of code.

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
physics.py              Explosions, fluid sim, wind, falling blocks
disasters.py            15 natural disasters with chain events
cuda_manager.py         NVIDIA CUDA GPU acceleration (CuPy)
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
pixel_font.py           Pixel font rendering
obj_loader.py           OBJ model loading
builder.py              Structure builder tool
world_manager.py        Save/load management
settings_manager.py     Per-world settings
io_system.py            IO trigger system
minecraft.py            Legacy single-file version
```

*Credits*

Made by AntacidDT — [github.com/AntacidDT](https://github.com/AntacidDT)

Built with:
- Python 3
- PyOpenGL
- Pygame
- NumPy
- Perlin Noise

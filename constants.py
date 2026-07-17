"""Pythmc - Constants and Block Types - V1.9 The General Update"""

# ─── Screen ──────────────────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 1280, 720
FPS = 60

# ─── World ───────────────────────────────────────────────────────────────────
CHUNK_SIZE = 16
CHUNK_HEIGHT = 64
RENDER_DISTANCE = 4
SEED = 42

# ─── Physics ─────────────────────────────────────────────────────────────────
GRAVITY = -25.0
JUMP_SPEED = 9.0
PLAYER_HEIGHT = 1.62
PLAYER_WIDTH = 0.3
WALK_SPEED = 4.3
SPRINT_SPEED = 6.5
SWIM_SPEED = 3.0
FLY_SPEED = 12.0
BREAK_COOLDOWN = 0.2
PLACE_COOLDOWN = 0.2
MAX_REACH = 6.0
WATER_DRAG = 0.6

# ─── Block Types ─────────────────────────────────────────────────────────────
AIR = 0
GRASS = 1
DIRT = 2
STONE = 3
WOOD = 4
LEAVES = 5
SAND = 6
WATER = 7
COBBLESTONE = 8
PLANKS = 9
BEDROCK = 10
COAL_ORE = 11
IRON_ORE = 12
GLASS = 13
BRICK = 14
SNOW = 15
CACTUS = 16
TORCH = 17
GRAVEL = 18
GOLD_ORE = 19
CRAFTING_TABLE_BLOCK = 20
FURNACE_BLOCK = 21
DIAMOND_ORE = 40

# Electronic Blocks (22-39)
WIRE_COPPER = 22
WIRE_GOLD = 23
RESISTOR_BLOCK = 24
CAPACITOR_BLOCK = 25
TRANSISTOR_NPN = 26
TRANSISTOR_PNP = 27
LED_RED = 28
LED_GREEN = 29
LED_BLUE = 30
BATTERY_BLOCK = 31
SWITCH_BLOCK = 32
BUTTON_BLOCK = 33
CIRCUIT_BOARD = 34
SILICON_BLOCK = 35
COPPER_BLOCK = 36
NE555_BLOCK = 37
LOGIC_GATE = 38
BUZZER_BLOCK = 39

# ─── Item Types (non-block) ──────────────────────────────────────────────────
# Tools (100-109)
STICK = 100
WOODEN_PICKAXE = 101
WOODEN_AXE = 102
WOODEN_SWORD = 103
STONE_PICKAXE = 104
STONE_AXE = 105
STONE_SWORD = 106
IRON_PICKAXE = 107
IRON_AXE = 108
IRON_SWORD = 109

# Diamond Tools (120-124)
DIAMOND = 120
DIAMOND_PICKAXE = 121
DIAMOND_AXE = 122
DIAMOND_SWORD = 123
DIAMOND_SHOVEL = 124

# Crafted items (110-119)
CRAFTING_TABLE = 110
FURNACE = 111
TORCH_ITEM = 112
COAL = 113
IRON_INGOT = 114
GOLD_INGOT = 115
RAW_IRON = 116
RAW_GOLD = 117

# ─── Food Items (130-149) ────────────────────────────────────────────────────
RAW_BEEF = 130
COOKED_BEEF = 131
RAW_CHICKEN = 132
COOKED_CHICKEN = 133
RAW_MUTTON = 134
COOKED_MUTTON = 135
BREAD = 136
APPLE = 137
GOLDEN_APPLE = 138
COOKIE = 139
STEAK = 140
CARROT = 141
POTATO = 142
WHEAT = 143
LEATHER = 144
FEATHER = 145
WOOL = 146
BONE = 147
ARROW = 148

# ─── Armor Items (150-165) ──────────────────────────────────────────────────
LEATHER_HELMET = 150
LEATHER_CHESTPLATE = 151
LEATHER_LEGGINGS = 152
LEATHER_BOOTS = 153
IRON_HELMET = 154
IRON_CHESTPLATE = 155
IRON_LEGGINGS = 156
IRON_BOOTS = 157
GOLD_HELMET = 158
GOLD_CHESTPLATE = 159
GOLD_LEGGINGS = 160
GOLD_BOOTS = 161
DIAMOND_HELMET = 162
DIAMOND_CHESTPLATE = 163
DIAMOND_LEGGINGS = 164
DIAMOND_BOOTS = 165

# ─── Electronic components (200-249) ─────────────────────────────────────────
WIRE_COPPER_ITEM = 200
WIRE_GOLD_ITEM = 201
RESISTOR_100R = 202
RESISTOR_1K = 203
RESISTOR_10K = 204
CAPACITOR_CERAMIC = 205
CAPACITOR_ELECTRO = 206
CAPACITOR_TANTALUM = 207
TRANSISTOR_NPN_ITEM = 208
TRANSISTOR_PNP_ITEM = 209
LED_RED_ITEM = 210
LED_GREEN_ITEM = 211
LED_BLUE_ITEM = 212
LED_WHITE_ITEM = 213
BATTERY_9V = 214
BATTERY_AA = 215
SWITCH_ITEM = 216
BUTTON_ITEM = 217
CIRCUIT_BOARD_ITEM = 218
SILICON_WAFER = 219
COPPER_WIRE = 220
NE555_TIMER = 221
LOGIC_AND = 222
LOGIC_OR = 223
LOGIC_NOT = 224
LOGIC_NAND = 225
LOGIC_NOR = 226
BUZZER = 227
MULTIMETER = 228
SOLDERING_IRON = 229
SOLDER_WIRE = 230
PCB_BOARD = 231
DIODE = 232
PUSH_BUTTON = 233
RELAY = 234
POTENTIOMETER = 235

# ─── Block/Item Names ────────────────────────────────────────────────────────
BLOCK_NAMES = {
    AIR: "Air", GRASS: "Grass", DIRT: "Dirt", STONE: "Stone",
    WOOD: "Wood", LEAVES: "Leaves", SAND: "Sand", WATER: "Water",
    COBBLESTONE: "Cobble", PLANKS: "Planks", BEDROCK: "Bedrock",
    COAL_ORE: "Coal Ore", IRON_ORE: "Iron Ore", GLASS: "Glass", BRICK: "Brick",
    SNOW: "Snow", CACTUS: "Cactus", TORCH: "Torch", GRAVEL: "Gravel",
    GOLD_ORE: "Gold Ore", DIAMOND_ORE: "Diamond Ore",
    CRAFTING_TABLE_BLOCK: "Crafting Table", FURNACE_BLOCK: "Furnace",
    WIRE_COPPER: "Copper Wire", WIRE_GOLD: "Gold Wire",
    RESISTOR_BLOCK: "Resistor", CAPACITOR_BLOCK: "Capacitor",
    TRANSISTOR_NPN: "NPN Transistor", TRANSISTOR_PNP: "PNP Transistor",
    LED_RED: "Red LED", LED_GREEN: "Green LED", LED_BLUE: "Blue LED",
    BATTERY_BLOCK: "Battery", SWITCH_BLOCK: "Switch", BUTTON_BLOCK: "Button",
    CIRCUIT_BOARD: "Circuit Board", SILICON_BLOCK: "Silicon",
    COPPER_BLOCK: "Copper Block", NE555_BLOCK: "NE555 Timer",
    LOGIC_GATE: "Logic Gate", BUZZER_BLOCK: "Buzzer",
}

ITEM_NAMES = {}
ITEM_NAMES.update(BLOCK_NAMES)
ITEM_NAMES.update({
    STICK: "Stick", WOODEN_PICKAXE: "Wood Pickaxe", WOODEN_AXE: "Wood Axe",
    WOODEN_SWORD: "Wood Sword", STONE_PICKAXE: "Stone Pickaxe", STONE_AXE: "Stone Axe",
    STONE_SWORD: "Stone Sword", IRON_PICKAXE: "Iron Pickaxe", IRON_AXE: "Iron Axe",
    IRON_SWORD: "Iron Sword", CRAFTING_TABLE: "Crafting Table", FURNACE: "Furnace",
    TORCH_ITEM: "Torch", COAL: "Coal", IRON_INGOT: "Iron Ingot", GOLD_INGOT: "Gold Ingot",
    RAW_IRON: "Raw Iron", RAW_GOLD: "Raw Gold",
    DIAMOND: "Diamond", DIAMOND_PICKAXE: "Diamond Pickaxe",
    DIAMOND_AXE: "Diamond Axe", DIAMOND_SWORD: "Diamond Sword",
    DIAMOND_SHOVEL: "Diamond Shovel",
    RAW_BEEF: "Raw Beef", COOKED_BEEF: "Cooked Beef",
    RAW_CHICKEN: "Raw Chicken", COOKED_CHICKEN: "Cooked Chicken",
    RAW_MUTTON: "Raw Mutton", COOKED_MUTTON: "Cooked Mutton",
    BREAD: "Bread", APPLE: "Apple", GOLDEN_APPLE: "Golden Apple",
    COOKIE: "Cookie", STEAK: "Steak", CARROT: "Carrot",
    POTATO: "Potato", WHEAT: "Wheat", LEATHER: "Leather",
    FEATHER: "Feather", WOOL: "Wool", BONE: "Bone", ARROW: "Arrow",
    LEATHER_HELMET: "Leather Helmet", LEATHER_CHESTPLATE: "Leather Tunic",
    LEATHER_LEGGINGS: "Leather Pants", LEATHER_BOOTS: "Leather Boots",
    IRON_HELMET: "Iron Helmet", IRON_CHESTPLATE: "Iron Chestplate",
    IRON_LEGGINGS: "Iron Leggings", IRON_BOOTS: "Iron Boots",
    GOLD_HELMET: "Gold Helmet", GOLD_CHESTPLATE: "Gold Chestplate",
    GOLD_LEGGINGS: "Gold Leggings", GOLD_BOOTS: "Gold Boots",
    DIAMOND_HELMET: "Diamond Helmet", DIAMOND_CHESTPLATE: "Diamond Chestplate",
    DIAMOND_LEGGINGS: "Diamond Leggings", DIAMOND_BOOTS: "Diamond Boots",
    WIRE_COPPER_ITEM: "Copper Wire", WIRE_GOLD_ITEM: "Gold Wire",
    RESISTOR_100R: "100R Resistor", RESISTOR_1K: "1K Resistor", RESISTOR_10K: "10K Resistor",
    CAPACITOR_CERAMIC: "Ceramic Cap", CAPACITOR_ELECTRO: "Electrolytic Cap",
    CAPACITOR_TANTALUM: "Tantalum Cap", TRANSISTOR_NPN_ITEM: "NPN Transistor",
    TRANSISTOR_PNP_ITEM: "PNP Transistor", LED_RED_ITEM: "Red LED",
    LED_GREEN_ITEM: "Green LED", LED_BLUE_ITEM: "Blue LED", LED_WHITE_ITEM: "White LED",
    BATTERY_9V: "9V Battery", BATTERY_AA: "AA Battery", SWITCH_ITEM: "Switch",
    BUTTON_ITEM: "Button", CIRCUIT_BOARD_ITEM: "Circuit Board",
    SILICON_WAFER: "Silicon Wafer", COPPER_WIRE: "Copper Wire",
    NE555_TIMER: "NE555 Timer", LOGIC_AND: "AND Gate", LOGIC_OR: "OR Gate",
    LOGIC_NOT: "NOT Gate", LOGIC_NAND: "NAND Gate", LOGIC_NOR: "NOR Gate",
    BUZZER: "Buzzer", MULTIMETER: "Multimeter", SOLDERING_IRON: "Soldering Iron",
    SOLDER_WIRE: "Solder Wire", PCB_BOARD: "PCB Board", DIODE: "Diode",
    PUSH_BUTTON: "Push Button", RELAY: "Relay", POTENTIOMETER: "Potentiometer",
})

# ─── Block/Item Colors ───────────────────────────────────────────────────────
BLOCK_COLORS = {
    GRASS:       ((0.30, 0.78, 0.20), (0.55, 0.35, 0.15), (0.40, 0.26, 0.13)),
    DIRT:        ((0.55, 0.35, 0.15), (0.55, 0.35, 0.15), (0.55, 0.35, 0.15)),
    STONE:       ((0.55, 0.55, 0.55), (0.50, 0.50, 0.50), (0.45, 0.45, 0.45)),
    WOOD:        ((0.55, 0.42, 0.22), (0.40, 0.28, 0.12), (0.55, 0.42, 0.22)),
    LEAVES:      ((0.18, 0.58, 0.12), (0.15, 0.52, 0.10), (0.12, 0.48, 0.08)),
    SAND:        ((0.88, 0.82, 0.58), (0.82, 0.78, 0.52), (0.78, 0.72, 0.48)),
    WATER:       ((0.22, 0.45, 0.85), (0.18, 0.38, 0.78), (0.15, 0.32, 0.70)),
    COBBLESTONE: ((0.48, 0.48, 0.48), (0.42, 0.42, 0.42), (0.38, 0.38, 0.38)),
    PLANKS:      ((0.72, 0.58, 0.32), (0.68, 0.52, 0.28), (0.65, 0.48, 0.25)),
    BEDROCK:     ((0.28, 0.28, 0.28), (0.22, 0.22, 0.22), (0.18, 0.18, 0.18)),
    COAL_ORE:    ((0.48, 0.48, 0.48), (0.42, 0.42, 0.42), (0.38, 0.38, 0.38)),
    IRON_ORE:    ((0.55, 0.52, 0.48), (0.58, 0.55, 0.50), (0.52, 0.48, 0.42)),
    GOLD_ORE:    ((0.55, 0.52, 0.48), (0.60, 0.55, 0.42), (0.52, 0.48, 0.42)),
    DIAMOND_ORE: ((0.45, 0.45, 0.48), (0.30, 0.65, 0.70), (0.25, 0.55, 0.60)),
    GLASS:       ((0.82, 0.92, 0.98), (0.80, 0.90, 0.95), (0.78, 0.88, 0.92)),
    BRICK:       ((0.68, 0.32, 0.28), (0.62, 0.30, 0.25), (0.58, 0.28, 0.22)),
    SNOW:        ((0.95, 0.97, 1.00), (0.90, 0.92, 0.95), (0.85, 0.88, 0.92)),
    CACTUS:      ((0.22, 0.62, 0.18), (0.18, 0.55, 0.15), (0.15, 0.48, 0.12)),
    TORCH:       ((0.95, 0.80, 0.30), (0.90, 0.72, 0.25), (0.85, 0.65, 0.20)),
    GRAVEL:      ((0.52, 0.50, 0.48), (0.48, 0.46, 0.44), (0.44, 0.42, 0.40)),
    CRAFTING_TABLE_BLOCK: ((0.72, 0.58, 0.32), (0.68, 0.52, 0.28), (0.65, 0.48, 0.25)),
    FURNACE_BLOCK:        ((0.50, 0.50, 0.50), (0.45, 0.45, 0.45), (0.40, 0.40, 0.40)),
    WIRE_COPPER:    ((0.72, 0.45, 0.20), (0.68, 0.42, 0.18), (0.64, 0.39, 0.16)),
    WIRE_GOLD:      ((0.85, 0.75, 0.20), (0.80, 0.70, 0.18), (0.75, 0.65, 0.16)),
    RESISTOR_BLOCK: ((0.60, 0.55, 0.45), (0.55, 0.50, 0.40), (0.50, 0.45, 0.35)),
    CAPACITOR_BLOCK:((0.30, 0.30, 0.35), (0.25, 0.25, 0.30), (0.20, 0.20, 0.25)),
    TRANSISTOR_NPN: ((0.20, 0.20, 0.22), (0.18, 0.18, 0.20), (0.16, 0.16, 0.18)),
    TRANSISTOR_PNP: ((0.22, 0.20, 0.20), (0.20, 0.18, 0.18), (0.18, 0.16, 0.16)),
    LED_RED:        ((0.90, 0.15, 0.15), (0.85, 0.12, 0.12), (0.80, 0.10, 0.10)),
    LED_GREEN:      ((0.15, 0.85, 0.15), (0.12, 0.80, 0.12), (0.10, 0.75, 0.10)),
    LED_BLUE:       ((0.15, 0.15, 0.90), (0.12, 0.12, 0.85), (0.10, 0.10, 0.80)),
    BATTERY_BLOCK:  ((0.25, 0.25, 0.28), (0.20, 0.20, 0.22), (0.15, 0.15, 0.18)),
    SWITCH_BLOCK:   ((0.70, 0.70, 0.72), (0.65, 0.65, 0.67), (0.60, 0.60, 0.62)),
    BUTTON_BLOCK:   ((0.80, 0.20, 0.20), (0.75, 0.18, 0.18), (0.70, 0.15, 0.15)),
    CIRCUIT_BOARD:  ((0.15, 0.50, 0.20), (0.12, 0.45, 0.18), (0.10, 0.40, 0.15)),
    SILICON_BLOCK:  ((0.45, 0.45, 0.48), (0.40, 0.40, 0.43), (0.35, 0.35, 0.38)),
    COPPER_BLOCK:   ((0.72, 0.45, 0.20), (0.68, 0.42, 0.18), (0.64, 0.39, 0.16)),
    NE555_BLOCK:    ((0.20, 0.20, 0.22), (0.18, 0.18, 0.20), (0.16, 0.16, 0.18)),
    LOGIC_GATE:     ((0.25, 0.25, 0.28), (0.22, 0.22, 0.25), (0.20, 0.20, 0.22)),
    BUZZER_BLOCK:   ((0.80, 0.75, 0.20), (0.75, 0.70, 0.18), (0.70, 0.65, 0.16)),
}

ITEM_COLORS = {}
ITEM_COLORS.update(BLOCK_COLORS)
ITEM_COLORS.update({
    STICK:          ((0.60, 0.45, 0.20), (0.55, 0.40, 0.18), (0.50, 0.35, 0.15)),
    WOODEN_PICKAXE: ((0.60, 0.45, 0.20), (0.55, 0.40, 0.18), (0.50, 0.35, 0.15)),
    WOODEN_AXE:     ((0.60, 0.45, 0.20), (0.55, 0.40, 0.18), (0.50, 0.35, 0.15)),
    WOODEN_SWORD:   ((0.60, 0.45, 0.20), (0.55, 0.40, 0.18), (0.50, 0.35, 0.15)),
    STONE_PICKAXE:  ((0.55, 0.55, 0.55), (0.50, 0.50, 0.50), (0.45, 0.45, 0.45)),
    STONE_AXE:      ((0.55, 0.55, 0.55), (0.50, 0.50, 0.50), (0.45, 0.45, 0.45)),
    STONE_SWORD:    ((0.55, 0.55, 0.55), (0.50, 0.50, 0.50), (0.45, 0.45, 0.45)),
    IRON_PICKAXE:   ((0.70, 0.68, 0.65), (0.65, 0.63, 0.60), (0.60, 0.58, 0.55)),
    IRON_AXE:       ((0.70, 0.68, 0.65), (0.65, 0.63, 0.60), (0.60, 0.58, 0.55)),
    IRON_SWORD:     ((0.70, 0.68, 0.65), (0.65, 0.63, 0.60), (0.60, 0.58, 0.55)),
    CRAFTING_TABLE: ((0.72, 0.58, 0.32), (0.68, 0.52, 0.28), (0.65, 0.48, 0.25)),
    FURNACE:        ((0.50, 0.50, 0.50), (0.45, 0.45, 0.45), (0.40, 0.40, 0.40)),
    TORCH_ITEM:     ((0.95, 0.80, 0.30), (0.90, 0.72, 0.25), (0.85, 0.65, 0.20)),
    COAL:           ((0.20, 0.20, 0.20), (0.15, 0.15, 0.15), (0.10, 0.10, 0.10)),
    IRON_INGOT:     ((0.70, 0.68, 0.65), (0.65, 0.63, 0.60), (0.60, 0.58, 0.55)),
    GOLD_INGOT:     ((0.85, 0.75, 0.20), (0.80, 0.70, 0.18), (0.75, 0.65, 0.15)),
    RAW_IRON:       ((0.55, 0.45, 0.40), (0.60, 0.50, 0.45), (0.50, 0.40, 0.35)),
    RAW_GOLD:       ((0.60, 0.55, 0.25), (0.65, 0.60, 0.30), (0.55, 0.50, 0.20)),
    DIAMOND:        ((0.25, 0.80, 0.85), (0.20, 0.70, 0.75), (0.15, 0.60, 0.65)),
    DIAMOND_PICKAXE:((0.25, 0.80, 0.85), (0.20, 0.70, 0.75), (0.55, 0.40, 0.18)),
    DIAMOND_AXE:    ((0.25, 0.80, 0.85), (0.20, 0.70, 0.75), (0.55, 0.40, 0.18)),
    DIAMOND_SWORD:  ((0.25, 0.80, 0.85), (0.20, 0.70, 0.75), (0.55, 0.40, 0.18)),
    DIAMOND_SHOVEL: ((0.25, 0.80, 0.85), (0.20, 0.70, 0.75), (0.55, 0.40, 0.18)),
    # Food items
    RAW_BEEF:       ((0.70, 0.25, 0.20), (0.80, 0.30, 0.25), (0.60, 0.20, 0.15)),
    COOKED_BEEF:    ((0.55, 0.35, 0.20), (0.65, 0.45, 0.28), (0.45, 0.30, 0.15)),
    RAW_CHICKEN:    ((0.90, 0.75, 0.65), (0.95, 0.80, 0.70), (0.85, 0.70, 0.60)),
    COOKED_CHICKEN: ((0.75, 0.55, 0.30), (0.80, 0.60, 0.35), (0.70, 0.50, 0.25)),
    RAW_MUTTON:     ((0.75, 0.30, 0.25), (0.80, 0.35, 0.30), (0.70, 0.25, 0.20)),
    COOKED_MUTTON:  ((0.60, 0.40, 0.25), (0.65, 0.45, 0.30), (0.55, 0.35, 0.20)),
    BREAD:          ((0.75, 0.55, 0.25), (0.80, 0.60, 0.30), (0.70, 0.50, 0.20)),
    APPLE:          ((0.85, 0.15, 0.10), (0.90, 0.20, 0.15), (0.20, 0.55, 0.15)),
    GOLDEN_APPLE:   ((0.90, 0.75, 0.15), (0.95, 0.80, 0.20), (0.85, 0.70, 0.10)),
    COOKIE:         ((0.75, 0.55, 0.25), (0.45, 0.30, 0.15), (0.70, 0.50, 0.20)),
    STEAK:          ((0.55, 0.30, 0.18), (0.65, 0.40, 0.25), (0.45, 0.25, 0.12)),
    CARROT:         ((0.90, 0.50, 0.10), (0.95, 0.55, 0.15), (0.20, 0.60, 0.15)),
    POTATO:         ((0.80, 0.72, 0.50), (0.85, 0.78, 0.55), (0.75, 0.68, 0.45)),
    WHEAT:          ((0.80, 0.72, 0.30), (0.85, 0.78, 0.35), (0.75, 0.68, 0.25)),
    LEATHER:        ((0.55, 0.35, 0.18), (0.60, 0.40, 0.22), (0.50, 0.30, 0.15)),
    FEATHER:        ((0.90, 0.90, 0.88), (0.95, 0.95, 0.93), (0.85, 0.85, 0.83)),
    WOOL:           ((0.90, 0.90, 0.90), (0.95, 0.95, 0.95), (0.85, 0.85, 0.85)),
    BONE:           ((0.90, 0.88, 0.80), (0.95, 0.93, 0.85), (0.85, 0.83, 0.75)),
    ARROW:          ((0.50, 0.40, 0.25), (0.55, 0.45, 0.30), (0.45, 0.35, 0.20)),
    # Armor items
    LEATHER_HELMET:     ((0.55, 0.35, 0.18), (0.60, 0.40, 0.22), (0.50, 0.30, 0.15)),
    LEATHER_CHESTPLATE: ((0.55, 0.35, 0.18), (0.60, 0.40, 0.22), (0.50, 0.30, 0.15)),
    LEATHER_LEGGINGS:   ((0.55, 0.35, 0.18), (0.60, 0.40, 0.22), (0.50, 0.30, 0.15)),
    LEATHER_BOOTS:      ((0.55, 0.35, 0.18), (0.60, 0.40, 0.22), (0.50, 0.30, 0.15)),
    IRON_HELMET:     ((0.70, 0.68, 0.65), (0.75, 0.73, 0.70), (0.65, 0.63, 0.60)),
    IRON_CHESTPLATE: ((0.70, 0.68, 0.65), (0.75, 0.73, 0.70), (0.65, 0.63, 0.60)),
    IRON_LEGGINGS:   ((0.70, 0.68, 0.65), (0.75, 0.73, 0.70), (0.65, 0.63, 0.60)),
    IRON_BOOTS:      ((0.70, 0.68, 0.65), (0.75, 0.73, 0.70), (0.65, 0.63, 0.60)),
    GOLD_HELMET:     ((0.85, 0.75, 0.20), (0.90, 0.80, 0.25), (0.80, 0.70, 0.15)),
    GOLD_CHESTPLATE: ((0.85, 0.75, 0.20), (0.90, 0.80, 0.25), (0.80, 0.70, 0.15)),
    GOLD_LEGGINGS:   ((0.85, 0.75, 0.20), (0.90, 0.80, 0.25), (0.80, 0.70, 0.15)),
    GOLD_BOOTS:      ((0.85, 0.75, 0.20), (0.90, 0.80, 0.25), (0.80, 0.70, 0.15)),
    DIAMOND_HELMET:     ((0.25, 0.80, 0.85), (0.30, 0.85, 0.90), (0.20, 0.75, 0.80)),
    DIAMOND_CHESTPLATE: ((0.25, 0.80, 0.85), (0.30, 0.85, 0.90), (0.20, 0.75, 0.80)),
    DIAMOND_LEGGINGS:   ((0.25, 0.80, 0.85), (0.30, 0.85, 0.90), (0.20, 0.75, 0.80)),
    DIAMOND_BOOTS:      ((0.25, 0.80, 0.85), (0.30, 0.85, 0.90), (0.20, 0.75, 0.80)),
    # Electronic items
    WIRE_COPPER_ITEM: ((0.72, 0.45, 0.20), (0.68, 0.42, 0.18), (0.64, 0.39, 0.16)),
    WIRE_GOLD_ITEM:   ((0.85, 0.75, 0.20), (0.80, 0.70, 0.18), (0.75, 0.65, 0.16)),
    RESISTOR_100R:    ((0.60, 0.55, 0.45), (0.55, 0.50, 0.40), (0.50, 0.45, 0.35)),
    RESISTOR_1K:      ((0.60, 0.55, 0.45), (0.55, 0.50, 0.40), (0.50, 0.45, 0.35)),
    RESISTOR_10K:     ((0.60, 0.55, 0.45), (0.55, 0.50, 0.40), (0.50, 0.45, 0.35)),
    CAPACITOR_CERAMIC:((0.65, 0.60, 0.55), (0.60, 0.55, 0.50), (0.55, 0.50, 0.45)),
    CAPACITOR_ELECTRO:((0.30, 0.30, 0.35), (0.25, 0.25, 0.30), (0.20, 0.20, 0.25)),
    CAPACITOR_TANTALUM:((0.35, 0.25, 0.20), (0.30, 0.22, 0.18), (0.25, 0.18, 0.15)),
    TRANSISTOR_NPN_ITEM: ((0.20, 0.20, 0.22), (0.18, 0.18, 0.20), (0.16, 0.16, 0.18)),
    TRANSISTOR_PNP_ITEM: ((0.22, 0.20, 0.20), (0.20, 0.18, 0.18), (0.18, 0.16, 0.16)),
    LED_RED_ITEM:    ((0.90, 0.15, 0.15), (0.85, 0.12, 0.12), (0.80, 0.10, 0.10)),
    LED_GREEN_ITEM:  ((0.15, 0.85, 0.15), (0.12, 0.80, 0.12), (0.10, 0.75, 0.10)),
    LED_BLUE_ITEM:   ((0.15, 0.15, 0.90), (0.12, 0.12, 0.85), (0.10, 0.10, 0.80)),
    LED_WHITE_ITEM:  ((0.95, 0.95, 0.95), (0.90, 0.90, 0.90), (0.85, 0.85, 0.85)),
    BATTERY_9V:      ((0.25, 0.25, 0.28), (0.20, 0.20, 0.22), (0.15, 0.15, 0.18)),
    BATTERY_AA:      ((0.25, 0.25, 0.28), (0.20, 0.20, 0.22), (0.15, 0.15, 0.18)),
    SWITCH_ITEM:     ((0.70, 0.70, 0.72), (0.65, 0.65, 0.67), (0.60, 0.60, 0.62)),
    BUTTON_ITEM:     ((0.80, 0.20, 0.20), (0.75, 0.18, 0.18), (0.70, 0.15, 0.15)),
    CIRCUIT_BOARD_ITEM:((0.15, 0.50, 0.20), (0.12, 0.45, 0.18), (0.10, 0.40, 0.15)),
    SILICON_WAFER:   ((0.45, 0.45, 0.48), (0.40, 0.40, 0.43), (0.35, 0.35, 0.38)),
    COPPER_WIRE:     ((0.72, 0.45, 0.20), (0.68, 0.42, 0.18), (0.64, 0.39, 0.16)),
    NE555_TIMER:     ((0.20, 0.20, 0.22), (0.18, 0.18, 0.20), (0.16, 0.16, 0.18)),
    LOGIC_AND:       ((0.25, 0.25, 0.28), (0.22, 0.22, 0.25), (0.20, 0.20, 0.22)),
    LOGIC_OR:        ((0.25, 0.25, 0.28), (0.22, 0.22, 0.25), (0.20, 0.20, 0.22)),
    LOGIC_NOT:       ((0.25, 0.25, 0.28), (0.22, 0.22, 0.25), (0.20, 0.20, 0.22)),
    LOGIC_NAND:      ((0.25, 0.25, 0.28), (0.22, 0.22, 0.25), (0.20, 0.20, 0.22)),
    LOGIC_NOR:       ((0.25, 0.25, 0.28), (0.22, 0.22, 0.25), (0.20, 0.20, 0.22)),
    BUZZER:          ((0.80, 0.75, 0.20), (0.75, 0.70, 0.18), (0.70, 0.65, 0.16)),
    MULTIMETER:      ((0.85, 0.65, 0.15), (0.80, 0.60, 0.12), (0.75, 0.55, 0.10)),
    SOLDERING_IRON:  ((0.50, 0.50, 0.55), (0.45, 0.45, 0.50), (0.40, 0.40, 0.45)),
    SOLDER_WIRE:     ((0.75, 0.75, 0.78), (0.70, 0.70, 0.73), (0.65, 0.65, 0.68)),
    PCB_BOARD:       ((0.15, 0.50, 0.20), (0.12, 0.45, 0.18), (0.10, 0.40, 0.15)),
    DIODE:           ((0.20, 0.20, 0.22), (0.18, 0.18, 0.20), (0.16, 0.16, 0.18)),
    PUSH_BUTTON:     ((0.80, 0.20, 0.20), (0.75, 0.18, 0.18), (0.70, 0.15, 0.15)),
    RELAY:           ((0.30, 0.30, 0.32), (0.25, 0.25, 0.28), (0.20, 0.20, 0.22)),
    POTENTIOMETER:   ((0.40, 0.35, 0.30), (0.35, 0.30, 0.25), (0.30, 0.25, 0.20)),
})

# ─── Sets ────────────────────────────────────────────────────────────────────
TRANSPARENT = {AIR, WATER, GLASS, LEAVES, TORCH, WIRE_COPPER, WIRE_GOLD}
SOLID_BLOCKS = set(range(1, 100)) - {WATER, TORCH, WIRE_COPPER, WIRE_GOLD}

# ─── Face Data ───────────────────────────────────────────────────────────────
FACE_DIRS = [(0,1,0),(0,-1,0),(1,0,0),(-1,0,0),(0,0,1),(0,0,-1)]

FACE_VERTS = [
    [(0,1,1),(1,1,1),(1,1,0),(0,1,0)],
    [(0,0,0),(1,0,0),(1,0,1),(0,0,1)],
    [(1,0,0),(1,1,0),(1,1,1),(1,0,1)],
    [(0,0,1),(0,1,1),(0,1,0),(0,0,0)],
    [(1,0,1),(1,1,1),(0,1,1),(0,0,1)],
    [(0,0,0),(0,1,0),(1,1,0),(1,0,0)],
]

# ─── Block Drops ─────────────────────────────────────────────────────────────
# Maps block_type -> [(item, min_count, max_count)]
# If block not listed, it drops itself x1
BLOCK_DROPS = {
    GRASS: [(DIRT, 1, 1)],
    LEAVES: [(APPLE, 0, 1), (STICK, 0, 2)],
    COAL_ORE: [(COAL, 1, 1)],
    IRON_ORE: [(RAW_IRON, 1, 1)],
    GOLD_ORE: [(RAW_GOLD, 1, 1)],
    DIAMOND_ORE: [(DIAMOND, 1, 1)],
    GLASS: [],
    CACTUS: [],
    BEDROCK: [],
}

# ─── Food Properties ─────────────────────────────────────────────────────────
# item -> (hunger_restore, saturation, is_cooked)
FOOD_PROPERTIES = {
    RAW_BEEF:       (3, 1.8, False),
    COOKED_BEEF:    (8, 12.8, True),
    STEAK:          (8, 12.8, True),
    RAW_CHICKEN:    (2, 1.2, False),
    COOKED_CHICKEN: (6, 7.2, True),
    RAW_MUTTON:     (2, 1.2, False),
    COOKED_MUTTON:  (6, 7.2, True),
    BREAD:          (5, 6.0, False),
    APPLE:          (4, 2.4, False),
    GOLDEN_APPLE:   (20, 20.0, False),
    COOKIE:         (2, 0.4, False),
    CARROT:         (3, 3.6, False),
    POTATO:         (1, 0.6, False),
    WHEAT:          (1, 0.3, False),
}

# ─── Furnace Recipes ────────────────────────────────────────────────────────
# input_item -> output_item (requires fuel)
FURNACE_RECIPES = {
    RAW_IRON:      IRON_INGOT,
    RAW_GOLD:      GOLD_INGOT,
    SAND:          GLASS,
    COBBLESTONE:   STONE,
    RAW_BEEF:      STEAK,
    RAW_CHICKEN:   COOKED_CHICKEN,
    RAW_MUTTON:    COOKED_MUTTON,
    POTATO:        BREAD,
}

# Fuel values in seconds of burn time
FUEL_VALUES = {
    COAL: 8.0,
    COAL: 8.0,
    PLANKS: 1.5,
    STICK: 0.5,
    WOOD: 1.5,
}

# ─── Tool Properties ─────────────────────────────────────────────────────────
TOOL_PROPERTIES = {
    WOODEN_PICKAXE: (2.0, 1.5, "pickaxe"),
    WOODEN_AXE:     (2.0, 1.5, "axe"),
    WOODEN_SWORD:   (1.0, 3.0, "sword"),
    STONE_PICKAXE:  (3.0, 2.0, "pickaxe"),
    STONE_AXE:      (3.0, 2.0, "axe"),
    STONE_SWORD:    (1.0, 4.0, "sword"),
    IRON_PICKAXE:   (4.0, 2.5, "pickaxe"),
    IRON_AXE:       (4.0, 2.5, "axe"),
    IRON_SWORD:     (1.0, 5.0, "sword"),
    DIAMOND_PICKAXE:(6.0, 3.0, "pickaxe"),
    DIAMOND_AXE:    (6.0, 3.0, "axe"),
    DIAMOND_SWORD:  (1.0, 7.0, "sword"),
}

TOOL_EFFECTIVE = {
    "pickaxe": {STONE, COBBLESTONE, IRON_ORE, GOLD_ORE, COAL_ORE, GLASS, BRICK, DIAMOND_ORE},
    "axe":     {WOOD, PLANKS},
    "sword":   set(),
    "shovel":  {DIRT, GRASS, SAND, GRAVEL},
}

# ─── Armor Properties ────────────────────────────────────────────────────────
# item -> (armor_points, slot_type)
ARMOR_PROPERTIES = {
    LEATHER_HELMET:     (1, "helmet"),
    LEATHER_CHESTPLATE: (3, "chestplate"),
    LEATHER_LEGGINGS:   (2, "leggings"),
    LEATHER_BOOTS:      (1, "boots"),
    IRON_HELMET:        (2, "helmet"),
    IRON_CHESTPLATE:    (6, "chestplate"),
    IRON_LEGGINGS:      (5, "leggings"),
    IRON_BOOTS:         (2, "boots"),
    GOLD_HELMET:        (2, "helmet"),
    GOLD_CHESTPLATE:    (6, "chestplate"),
    GOLD_LEGGINGS:      (5, "leggings"),
    GOLD_BOOTS:         (2, "boots"),
    DIAMOND_HELMET:     (3, "helmet"),
    DIAMOND_CHESTPLATE: (8, "chestplate"),
    DIAMOND_LEGGINGS:   (6, "leggings"),
    DIAMOND_BOOTS:      (3, "boots"),
}

# Armor material colors for rendering
ARMOR_COLORS = {
    LEATHER_HELMET:     (0.55, 0.35, 0.18),
    LEATHER_CHESTPLATE: (0.55, 0.35, 0.18),
    LEATHER_LEGGINGS:   (0.55, 0.35, 0.18),
    LEATHER_BOOTS:      (0.55, 0.35, 0.18),
    IRON_HELMET:        (0.70, 0.68, 0.65),
    IRON_CHESTPLATE:    (0.70, 0.68, 0.65),
    IRON_LEGGINGS:      (0.70, 0.68, 0.65),
    IRON_BOOTS:         (0.70, 0.68, 0.65),
    GOLD_HELMET:        (0.85, 0.75, 0.20),
    GOLD_CHESTPLATE:    (0.85, 0.75, 0.20),
    GOLD_LEGGINGS:      (0.85, 0.75, 0.20),
    GOLD_BOOTS:         (0.85, 0.75, 0.20),
    DIAMOND_HELMET:     (0.25, 0.80, 0.85),
    DIAMOND_CHESTPLATE: (0.25, 0.80, 0.85),
    DIAMOND_LEGGINGS:   (0.25, 0.80, 0.85),
    DIAMOND_BOOTS:      (0.25, 0.80, 0.85),
}

ARMOR_SLOT_TYPES = {
    "helmet": LEATHER_HELMET,
    "chestplate": LEATHER_CHESTPLATE,
    "leggings": LEATHER_LEGGINGS,
    "boots": LEATHER_BOOTS,
}

# ─── Electronic Component Properties ─────────────────────────────────────────
COMPONENT_PROPERTIES = {
    RESISTOR_100R:    ("resistor", 100, False, 50),
    RESISTOR_1K:      ("resistor", 1000, False, 50),
    RESISTOR_10K:     ("resistor", 10000, False, 50),
    CAPACITOR_CERAMIC:("capacitor", 0.000001, False, 50),
    CAPACITOR_ELECTRO:("capacitor", 0.001, True, 25),
    CAPACITOR_TANTALUM:("capacitor", 0.0001, True, 16),
    TRANSISTOR_NPN_ITEM: ("transistor", "NPN", False, 40),
    TRANSISTOR_PNP_ITEM: ("transistor", "PNP", True, 40),
    LED_RED_ITEM:     ("led", 2.0, True, 3.3),
    LED_GREEN_ITEM:   ("led", 2.2, True, 3.3),
    LED_BLUE_ITEM:    ("led", 3.0, True, 3.3),
    LED_WHITE_ITEM:   ("led", 3.2, True, 3.3),
    DIODE:            ("diode", 0.7, True, 50),
    NE555_TIMER:      ("ic", "555", False, 16),
    LOGIC_AND:        ("ic", "AND", False, 5),
    LOGIC_OR:         ("ic", "OR", False, 5),
    LOGIC_NOT:        ("ic", "NOT", False, 5),
    LOGIC_NAND:       ("ic", "NAND", False, 5),
    LOGIC_NOR:        ("ic", "NOR", False, 5),
}

POLARITY_COLORS = {
    "positive": (0.9, 0.1, 0.1),
    "negative": (0.1, 0.1, 0.9),
    "neutral":  (0.5, 0.5, 0.5),
}

# ─── Entity Types ────────────────────────────────────────────────────────────
ENTITY_COW = "cow"
ENTITY_SHEEP = "sheep"
ENTITY_CHICKEN = "chicken"
ENTITY_ZOMBIE = "zombie"
ENTITY_SKELETON = "skeleton"

ENTITY_COLORS = {
    ENTITY_COW:      ((0.35, 0.22, 0.12), (0.90, 0.90, 0.90), (0.2, 0.2, 0.2)),
    ENTITY_SHEEP:    ((0.90, 0.90, 0.90), (0.60, 0.55, 0.50), (0.2, 0.2, 0.2)),
    ENTITY_CHICKEN:  ((0.95, 0.92, 0.85), (0.85, 0.20, 0.15), (0.1, 0.1, 0.1)),
    ENTITY_ZOMBIE:   ((0.30, 0.60, 0.30), (0.25, 0.50, 0.25), (0.1, 0.3, 0.1)),
    ENTITY_SKELETON: ((0.85, 0.85, 0.80), (0.70, 0.70, 0.65), (0.15, 0.15, 0.15)),
}

ENTITY_STATS = {
    ENTITY_COW:      (10, 2.0, 0, False, 0),
    ENTITY_SHEEP:    (8,  2.0, 0, False, 0),
    ENTITY_CHICKEN:  (4,  2.5, 0, False, 0),
    ENTITY_ZOMBIE:   (20, 2.5, 3, True, 2.0),
    ENTITY_SKELETON: (20, 2.8, 4, True, 8.0),
}

ENTITY_DROPS = {
    ENTITY_COW:      [(RAW_BEEF, 1, 3), (LEATHER, 0, 2)],
    ENTITY_SHEEP:    [(RAW_MUTTON, 1, 2), (WOOL, 1, 1)],
    ENTITY_CHICKEN:  [(RAW_CHICKEN, 1, 1), (FEATHER, 0, 2)],
    ENTITY_ZOMBIE:   [(IRON_INGOT, 0, 1), (ARROW, 0, 2)],
    ENTITY_SKELETON: [(BONE, 1, 2), (ARROW, 0, 3)],
}

# Add CHARCOAL alias for furnace fuel (treated as COAL for fuel purposes)
CHARCOAL = COAL

# ─── Placeable Blocks ────────────────────────────────────────────────────────
# Items that have block forms and should place as blocks
ITEM_TO_BLOCK = {
    CRAFTING_TABLE: CRAFTING_TABLE_BLOCK,
    FURNACE: FURNACE_BLOCK,
    TORCH_ITEM: TORCH,
}

PLACEABLE_BLOCKS = set(BLOCK_NAMES.keys())

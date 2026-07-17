"""Pythmc - Crafting System - V1.9"""

from constants import *


class CraftingRecipe:
    """A shaped crafting recipe."""
    def __init__(self, pattern, result, count=1):
        self.pattern = pattern
        self.result = result
        self.count = count
        self.height = len(pattern)
        self.width = max(len(row) for row in pattern)

    def matches(self, grid, grid_size=3):
        for oy in range(grid_size - self.height + 1):
            for ox in range(grid_size - self.width + 1):
                if self._check_offset(grid, ox, oy, grid_size):
                    return True
        return False

    def _check_offset(self, grid, ox, oy, grid_size):
        for y in range(grid_size):
            for x in range(grid_size):
                grid_item = grid[y][x]
                py = y - oy
                px = x - ox
                if 0 <= py < self.height and 0 <= px < len(self.pattern[py]):
                    pattern_item = self.pattern[py][px]
                    if grid_item != pattern_item:
                        return False
                else:
                    if grid_item != AIR:
                        return False
        return True


CRAFTING_RECIPES = []

def _add(pattern, result, count=1):
    CRAFTING_RECIPES.append(CraftingRecipe(pattern, result, count))

# ─── Basic Recipes ───────────────────────────────────────────────────────────

_add([[WOOD]], PLANKS, 4)

_add([[PLANKS],
      [PLANKS]], STICK, 4)

# ─── Tool Recipes ────────────────────────────────────────────────────────────

# Wooden
_add([[PLANKS, PLANKS, PLANKS],
      [AIR,    STICK,  AIR],
      [AIR,    STICK,  AIR]], WOODEN_PICKAXE)

_add([[PLANKS, PLANKS, AIR],
      [PLANKS, STICK,  AIR],
      [AIR,    STICK,  AIR]], WOODEN_AXE)

_add([[PLANKS, AIR],
      [PLANKS, AIR],
      [STICK,  AIR]], WOODEN_SWORD)

# Stone
_add([[COBBLESTONE, COBBLESTONE, COBBLESTONE],
      [AIR,         STICK,       AIR],
      [AIR,         STICK,       AIR]], STONE_PICKAXE)

_add([[COBBLESTONE, COBBLESTONE, AIR],
      [COBBLESTONE, STICK,       AIR],
      [AIR,         STICK,       AIR]], STONE_AXE)

_add([[COBBLESTONE, AIR],
      [COBBLESTONE, AIR],
      [STICK,       AIR]], STONE_SWORD)

# Iron
_add([[IRON_INGOT, IRON_INGOT, IRON_INGOT],
      [AIR,        STICK,      AIR],
      [AIR,        STICK,      AIR]], IRON_PICKAXE)

_add([[IRON_INGOT, IRON_INGOT, AIR],
      [IRON_INGOT, STICK,      AIR],
      [AIR,        STICK,      AIR]], IRON_AXE)

_add([[IRON_INGOT, AIR],
      [IRON_INGOT, AIR],
      [STICK,      AIR]], IRON_SWORD)

# Diamond
_add([[DIAMOND, DIAMOND, DIAMOND],
      [AIR,     STICK,   AIR],
      [AIR,     STICK,   AIR]], DIAMOND_PICKAXE)

_add([[DIAMOND, DIAMOND, AIR],
      [DIAMOND, STICK,   AIR],
      [AIR,     STICK,   AIR]], DIAMOND_AXE)

_add([[DIAMOND, AIR],
      [DIAMOND, AIR],
      [STICK,   AIR]], DIAMOND_SWORD)

_add([[AIR,     DIAMOND, AIR],
      [AIR,     STICK,   AIR],
      [AIR,     STICK,   AIR]], DIAMOND_SHOVEL)

# ─── Armor Recipes ───────────────────────────────────────────────────────────

# Leather Armor
_add([[LEATHER, LEATHER, LEATHER],
      [LEATHER, AIR,     LEATHER]], LEATHER_HELMET)

_add([[LEATHER, AIR,     LEATHER],
      [LEATHER, LEATHER, LEATHER],
      [LEATHER, LEATHER, LEATHER]], LEATHER_CHESTPLATE)

_add([[LEATHER, LEATHER, LEATHER],
      [LEATHER, AIR,     LEATHER],
      [LEATHER, AIR,     LEATHER]], LEATHER_LEGGINGS)

_add([[LEATHER, AIR, LEATHER],
      [LEATHER, AIR, LEATHER]], LEATHER_BOOTS)

# Iron Armor
_add([[IRON_INGOT, IRON_INGOT, IRON_INGOT],
      [IRON_INGOT, AIR,        IRON_INGOT]], IRON_HELMET)

_add([[IRON_INGOT, AIR,        IRON_INGOT],
      [IRON_INGOT, IRON_INGOT, IRON_INGOT],
      [IRON_INGOT, IRON_INGOT, IRON_INGOT]], IRON_CHESTPLATE)

_add([[IRON_INGOT, IRON_INGOT, IRON_INGOT],
      [IRON_INGOT, AIR,        IRON_INGOT],
      [IRON_INGOT, AIR,        IRON_INGOT]], IRON_LEGGINGS)

_add([[IRON_INGOT, AIR, IRON_INGOT],
      [IRON_INGOT, AIR, IRON_INGOT]], IRON_BOOTS)

# Gold Armor
_add([[GOLD_INGOT, GOLD_INGOT, GOLD_INGOT],
      [GOLD_INGOT, AIR,        GOLD_INGOT]], GOLD_HELMET)

_add([[GOLD_INGOT, AIR,        GOLD_INGOT],
      [GOLD_INGOT, GOLD_INGOT, GOLD_INGOT],
      [GOLD_INGOT, GOLD_INGOT, GOLD_INGOT]], GOLD_CHESTPLATE)

_add([[GOLD_INGOT, GOLD_INGOT, GOLD_INGOT],
      [GOLD_INGOT, AIR,        GOLD_INGOT],
      [GOLD_INGOT, AIR,        GOLD_INGOT]], GOLD_LEGGINGS)

_add([[GOLD_INGOT, AIR, GOLD_INGOT],
      [GOLD_INGOT, AIR, GOLD_INGOT]], GOLD_BOOTS)

# Diamond Armor
_add([[DIAMOND, DIAMOND, DIAMOND],
      [DIAMOND, AIR,     DIAMOND]], DIAMOND_HELMET)

_add([[DIAMOND, AIR,     DIAMOND],
      [DIAMOND, DIAMOND, DIAMOND],
      [DIAMOND, DIAMOND, DIAMOND]], DIAMOND_CHESTPLATE)

_add([[DIAMOND, DIAMOND, DIAMOND],
      [DIAMOND, AIR,     DIAMOND],
      [DIAMOND, AIR,     DIAMOND]], DIAMOND_LEGGINGS)

_add([[DIAMOND, AIR, DIAMOND],
      [DIAMOND, AIR, DIAMOND]], DIAMOND_BOOTS)

# ─── Food Recipes ────────────────────────────────────────────────────────────

# Bread (3 wheat)
_add([[WHEAT, WHEAT, WHEAT]], BREAD)

# Cookie (wheat + wheat)
_add([[WHEAT, WHEAT]], COOKIE, 8)

# ─── Block Recipes ───────────────────────────────────────────────────────────

_add([[PLANKS, PLANKS],
      [PLANKS, PLANKS]], CRAFTING_TABLE)

_add([[COBBLESTONE, COBBLESTONE, COBBLESTONE],
      [COBBLESTONE, AIR,         COBBLESTONE],
      [COBBLESTONE, COBBLESTONE, COBBLESTONE]], FURNACE)

_add([[COAL],
      [STICK]], TORCH_ITEM, 4)

_add([[SAND, SAND, SAND],
      [SAND, AIR,  SAND],
      [SAND, SAND, SAND]], GLASS, 8)

# ─── Electronic Component Recipes ────────────────────────────────────────────

_add([[COPPER_BLOCK]], WIRE_COPPER_ITEM, 8)
_add([[GOLD_INGOT]], WIRE_GOLD_ITEM, 4)

_add([[PLANKS, PLANKS, PLANKS],
      [WIRE_COPPER_ITEM, WIRE_COPPER_ITEM, WIRE_COPPER_ITEM],
      [PLANKS, PLANKS, PLANKS]], CIRCUIT_BOARD_ITEM)

_add([[COAL, STICK, COAL]], RESISTOR_100R, 4)
_add([[IRON_INGOT, GLASS, IRON_INGOT]], CAPACITOR_CERAMIC, 2)

_add([[IRON_INGOT, GLASS, IRON_INGOT],
      [GOLD_INGOT, AIR, GOLD_INGOT]], CAPACITOR_ELECTRO)

_add([[SILICON_WAFER, WIRE_COPPER_ITEM, SILICON_WAFER],
      [WIRE_COPPER_ITEM, SILICON_WAFER, WIRE_COPPER_ITEM]], TRANSISTOR_NPN_ITEM)

_add([[SILICON_WAFER, WIRE_GOLD_ITEM, SILICON_WAFER],
      [WIRE_GOLD_ITEM, SILICON_WAFER, WIRE_GOLD_ITEM]], TRANSISTOR_PNP_ITEM)

_add([[GLASS, COAL, GLASS],
      [COAL, GLASS, COAL]], LED_RED_ITEM, 2)

_add([[GLASS, CACTUS, GLASS],
      [CACTUS, GLASS, CACTUS]], LED_GREEN_ITEM, 2)

_add([[GLASS, WATER, GLASS],
      [WATER, GLASS, WATER]], LED_BLUE_ITEM, 2)

_add([[IRON_INGOT, COAL, IRON_INGOT],
      [IRON_INGOT, COAL, IRON_INGOT],
      [IRON_INGOT, COAL, IRON_INGOT]], BATTERY_9V)

_add([[IRON_INGOT, COAL, IRON_INGOT]], BATTERY_AA, 2)

_add([[IRON_INGOT, STICK, IRON_INGOT]], SWITCH_ITEM)
_add([[IRON_INGOT, STICK]], BUTTON_ITEM)
_add([[SAND, COAL, SAND]], SILICON_WAFER, 2)

_add([[WIRE_COPPER_ITEM, WIRE_COPPER_ITEM, WIRE_COPPER_ITEM],
      [WIRE_COPPER_ITEM, WIRE_COPPER_ITEM, WIRE_COPPER_ITEM],
      [WIRE_COPPER_ITEM, WIRE_COPPER_ITEM, WIRE_COPPER_ITEM]], COPPER_BLOCK)

_add([[CIRCUIT_BOARD_ITEM, TRANSISTOR_NPN_ITEM, CIRCUIT_BOARD_ITEM],
      [RESISTOR_100R, CAPACITOR_CERAMIC, RESISTOR_100R],
      [CIRCUIT_BOARD_ITEM, WIRE_COPPER_ITEM, CIRCUIT_BOARD_ITEM]], NE555_TIMER)

_add([[CIRCUIT_BOARD_ITEM, TRANSISTOR_NPN_ITEM, CIRCUIT_BOARD_ITEM],
      [WIRE_COPPER_ITEM, WIRE_COPPER_ITEM, WIRE_COPPER_ITEM]], LOGIC_AND)

_add([[TRANSISTOR_NPN_ITEM, AIR, TRANSISTOR_NPN_ITEM],
      [WIRE_COPPER_ITEM, CIRCUIT_BOARD_ITEM, WIRE_COPPER_ITEM]], LOGIC_OR)

_add([[RESISTOR_1K, TRANSISTOR_NPN_ITEM, CIRCUIT_BOARD_ITEM],
      [WIRE_COPPER_ITEM, WIRE_COPPER_ITEM, WIRE_COPPER_ITEM]], LOGIC_NOT)

_add([[IRON_INGOT, WIRE_COPPER_ITEM, IRON_INGOT],
      [WIRE_COPPER_ITEM, COAL, WIRE_COPPER_ITEM],
      [IRON_INGOT, WIRE_COPPER_ITEM, IRON_INGOT]], BUZZER)

_add([[GLASS, IRON_INGOT, GLASS],
      [WIRE_COPPER_ITEM, CIRCUIT_BOARD_ITEM, WIRE_COPPER_ITEM],
      [IRON_INGOT, COAL, IRON_INGOT]], MULTIMETER)

_add([[IRON_INGOT, IRON_INGOT, STICK],
      [COAL, WIRE_COPPER_ITEM, STICK]], SOLDERING_IRON)

_add([[GOLD_INGOT, GOLD_INGOT]], SOLDER_WIRE, 4)

_add([[PLANKS, WIRE_COPPER_ITEM, PLANKS],
      [WIRE_COPPER_ITEM, CIRCUIT_BOARD_ITEM, WIRE_COPPER_ITEM],
      [PLANKS, WIRE_COPPER_ITEM, PLANKS]], PCB_BOARD)

_add([[SILICON_WAFER, WIRE_COPPER_ITEM]], DIODE, 2)
_add([[RESISTOR_1K, STICK, IRON_INGOT]], POTENTIOMETER)


def find_recipe(grid, grid_size=3):
    """Find a matching recipe for the given crafting grid."""
    for recipe in CRAFTING_RECIPES:
        if recipe.width > grid_size or recipe.height > grid_size:
            continue
        if recipe.matches(grid, grid_size):
            return recipe.result, recipe.count
    return AIR, 0


def get_all_recipes():
    return CRAFTING_RECIPES

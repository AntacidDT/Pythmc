"""Pythmc - Command Terminal with Cheats

Opens with '/' key. Commands are typed and executed.
Cheats must be enabled at world creation - can't be disabled once active.
"""

import math
import pygame
from pygame.locals import *
import numpy as np
from OpenGL.GL import *
from constants import *
from text_renderer import text_renderer


# All available commands
COMMANDS = {
    "help": "Show all commands",
    "give": "give <item> [count] - Give items",
    "tp": "tp <x> <y> <z> - Teleport",
    "time": "time <day/night/noon/midnight> - Set time",
    "gamemode": "gamemode <creative/survival> - Switch mode",
    "heal": "heal - Restore health and hunger",
    "kill": "kill - Kill yourself",
    "fly": "fly - Toggle fly mode",
    "speed": "speed <normal/fast/insane> - Set movement speed",
    "spawn": "spawn - Teleport to world spawn",
    "seed": "seed - Show world seed",
    "clear": "clear - Clear inventory",
    "fill": "fill <item> - Fill hotbar with item",
    "enchant": "enchant - Max enchant (placeholder)",
    "summon": "summon <mob> - Spawn entity nearby",
    "weather": "weather <clear/rain> - Set weather",
    "difficulty": "difficulty <peaceful/easy/hard> - Set difficulty",
    "invincible": "invincible - Toggle invincible mode (no damage)",
    "msg": "msg <player> <message> - Send private message",
    "list": "list - List online players",
    "kick": "kick <player> - Kick player (host only)",
}


class Terminal:
    """In-game command terminal."""
    
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.open = False
        self.input_text = ""
        self.cursor_blink = 0
        self.history = []  # Command history
        self.history_idx = -1
        self.output_lines = []  # Recent output messages
        self.max_output = 8
        
    def toggle(self):
        self.open = not self.open
        if self.open:
            self.input_text = ""
            self.history_idx = -1
    
    def handle_event(self, event, game):
        """Handle keyboard events. Returns True if event was consumed."""
        if not self.open:
            return False
        
        
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE or event.key == K_SLASH:
                self.open = False
                return True
            elif event.key == K_RETURN:
                self._execute_command(game)
                return True
            elif event.key == K_BACKSPACE:
                self.input_text = self.input_text[:-1]
                return True
            elif event.key == K_UP:
                # History up
                if self.history:
                    self.history_idx = min(self.history_idx + 1, len(self.history) - 1)
                    self.input_text = self.history[-(self.history_idx + 1)]
                return True
            elif event.key == K_DOWN:
                # History down
                if self.history_idx > 0:
                    self.history_idx -= 1
                    self.input_text = self.history[-(self.history_idx + 1)]
                else:
                    self.history_idx = -1
                    self.input_text = ""
                return True
            elif event.unicode and event.unicode.isprintable():
                if len(self.input_text) < 100:
                    self.input_text += event.unicode
                return True
        
        return True  # Consume all events when open
    
    def _execute_command(self, game):
        """Parse and execute a command."""
        cmd_text = self.input_text.strip()
        if not cmd_text:
            return
        
        # Add to history
        self.history.append(cmd_text)
        self.history_idx = -1
        self.input_text = ""
        
        # Parse command
        if not cmd_text.startswith("/"):
            cmd_text = "/" + cmd_text
        
        parts = cmd_text[1:].split()  # Remove leading /
        if not parts:
            return
        
        cmd = parts[0].lower()
        args = parts[1:]
        
        # Execute
        self._output(f"> {cmd_text}")
        
        if cmd == "help":
            self._cmd_help()
        elif cmd == "give":
            self._cmd_give(game, args)
        elif cmd == "tp":
            self._cmd_tp(game, args)
        elif cmd == "time":
            self._cmd_time(game, args)
        elif cmd == "gamemode":
            self._cmd_gamemode(game, args)
        elif cmd == "heal":
            self._cmd_heal(game)
        elif cmd == "kill":
            self._cmd_kill(game)
        elif cmd == "fly":
            self._cmd_fly(game)
        elif cmd == "speed":
            self._cmd_speed(game, args)
        elif cmd == "spawn":
            self._cmd_spawn(game)
        elif cmd == "seed":
            self._cmd_seed(game)
        elif cmd == "clear":
            self._cmd_clear(game)
        elif cmd == "fill":
            self._cmd_fill(game, args)
        elif cmd == "summon":
            self._cmd_summon(game, args)
        elif cmd == "weather":
            self._cmd_weather(game, args)
        elif cmd == "invincible":
            self._cmd_invincible(game)
        elif cmd == "enchant":
            self._output("Enchantment not implemented yet!")
        else:
            self._output(f"Unknown command: {cmd}")
            self._output("Type /help for commands")
    
    def _output(self, text):
        """Add output line."""
        self.output_lines.append(text)
        if len(self.output_lines) > self.max_output:
            self.output_lines.pop(0)
    
    def _cmd_help(self):
        self._output("=== COMMANDS ===")
        for cmd, desc in COMMANDS.items():
            self._output(f"/{cmd}: {desc}")
    
    def _cmd_give(self, game, args):
        if not args:
            self._output("Usage: /give <item> [count]")
            return
        
        item_name = args[0].upper()
        count = int(args[1]) if len(args) > 1 else 64
        
        # Find item by name
        item_id = None
        for k, v in BLOCK_NAMES.items():
            if v.upper() == item_name:
                item_id = k
                break
        
        # Also check item names
        if item_id is None:
            from constants import ITEM_NAMES
            for k, v in ITEM_NAMES.items():
                if v.upper() == item_name:
                    item_id = k
                    break
        
        if item_id is None:
            self._output(f"Unknown item: {args[0]}")
            return
        
        leftover = game.player.inventory.add_item(item_id, count)
        given = count - leftover
        self._output(f"Gave {given}x {BLOCK_NAMES.get(item_id, 'item')}")
    
    def _cmd_tp(self, game, args):
        if len(args) < 3:
            self._output("Usage: /tp <x> <y> <z>")
            return
        
        try:
            x = float(args[0])
            y = float(args[1])
            z = float(args[2])
            game.player.pos[0] = x
            game.player.pos[1] = y
            game.player.pos[2] = z
            game.player.velocity = np.array([0.0, 0.0, 0.0])
            self._output(f"Teleported to {x:.1f}, {y:.1f}, {z:.1f}")
        except ValueError:
            self._output("Invalid coordinates")
    
    def _cmd_time(self, game, args):
        if not args:
            self._output("Usage: /time <day/night/noon/midnight>")
            return
        
        t = args[0].lower()
        if t == "day":
            game.day_time = 0.25
            self._output("Time set to day")
        elif t == "night":
            game.day_time = 0.75
            self._output("Time set to night")
        elif t == "noon":
            game.day_time = 0.25
            self._output("Time set to noon")
        elif t == "midnight":
            game.day_time = 0.75
            self._output("Time set to midnight")
        else:
            self._output("Unknown time: use day/night/noon/midnight")
    
    def _cmd_gamemode(self, game, args):
        if not args:
            self._output("Usage: /gamemode <creative/survival>")
            return
        
        mode = args[0].lower()
        if mode == "creative":
            game.player.creative = True
            game.player.health = game.player.max_health
            game.player.hunger = 20.0
            self._output("Gamemode set to Creative")
        elif mode == "survival":
            game.player.creative = False
            game.player.flying = False
            self._output("Gamemode set to Survival")
        else:
            self._output("Unknown mode: use creative/survival")
    
    def _cmd_heal(self, game):
        game.player.health = game.player.max_health
        game.player.hunger = 20.0
        game.player.dead = False
        self._output("Healed to full health and hunger")
    
    def _cmd_kill(self, game):
        if not game.player.creative:
            game.player.health = 0
            game.player.die()
            self._output("You died!")
        else:
            self._output("Can't die in creative mode!")
    
    def _cmd_fly(self, game):
        if game.player.creative:
            game.player.flying = not game.player.flying
            state = "ON" if game.player.flying else "OFF"
            self._output(f"Fly mode: {state}")
        else:
            self._output("Fly only available in creative mode")
    
    def _cmd_speed(self, game, args):
        if not args:
            self._output("Usage: /speed <normal/fast/insane>")
            return
        
        s = args[0].lower()
        if s == "normal":
            from constants import WALK_SPEED, SPRINT_SPEED
            self._output("Speed set to normal")
        elif s == "fast":
            self._output("Speed set to fast")
        elif s == "insane":
            self._output("Speed set to insane")
        else:
            self._output("Unknown speed: use normal/fast/insane")
    
    def _cmd_spawn(self, game):
        game.player.pos[0] = 8.5
        game.player.pos[2] = 8.5
        game.player.pos[1] = float(game.world.get_height(8, 8) + 2)
        game.player.velocity = np.array([0.0, 0.0, 0.0])
        self._output("Teleported to spawn")
    
    def _cmd_seed(self, game):
        self._output(f"World seed: {game.world.seed}")
    
    def _cmd_clear(self, game):
        for slot in game.player.inventory.hotbar:
            slot.clear()
        for row in game.player.inventory.main:
            for slot in row:
                slot.clear()
        self._output("Inventory cleared")
    
    def _cmd_fill(self, game, args):
        if not args:
            self._output("Usage: /fill <item>")
            return
        
        item_name = args[0].upper()
        item_id = None
        for k, v in BLOCK_NAMES.items():
            if v.upper() == item_name:
                item_id = k
                break
        
        if item_id is None:
            self._output(f"Unknown item: {args[0]}")
            return
        
        for slot in game.player.inventory.hotbar:
            slot.set(item_id, 64)
        self._output(f"Hotbar filled with {BLOCK_NAMES.get(item_id, 'item')}")
    
    def _cmd_summon(self, game, args):
        if not args:
            self._output("Usage: /summon <cow/sheep/chicken/zombie/skeleton>")
            return
        
        mob = args[0].lower()
        from entities import Entity
        
        valid_mobs = {
            "sheep": ENTITY_SHEEP, "chicken": ENTITY_CHICKEN,
            "zombie": ENTITY_ZOMBIE, "skeleton": ENTITY_SKELETON,
        }
        
        if mob not in valid_mobs:
            self._output(f"Unknown mob: {args[0]}")
            return
        
        # Spawn near player
        import random
        px = game.player.pos[0] + random.uniform(-3, 3)
        pz = game.player.pos[2] + random.uniform(-3, 3)
        py = game.player.pos[1]
        
        entity = Entity(valid_mobs[mob], [px, py, pz], game.world)
        game.entity_manager.entities.append(entity)
        self._output(f"Summoned {mob}")
    
    def _cmd_weather(self, game, args):
        if not args:
            self._output("Usage: /weather <clear/rain>")
            return
        w = args[0].lower()
        if w == "clear":
            self._output("Weather set to clear")
        elif w == "rain":
            self._output("Weather set to rain")
        else:
            self._output("Unknown weather: use clear/rain")
    
    def _cmd_invincible(self, game):
        game.player.creative = not game.player.creative
        if game.player.creative:
            game.player.health = game.player.max_health
            game.player.hunger = 20.0
            self._output("Invincible mode ON")
        else:
            self._output("Invincible mode OFF")
    
    def draw(self):
        """Draw the terminal overlay."""
        if not self.open:
            return
        
        
        glDisable(GL_LIGHTING)
        glDisable(GL_FOG)
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.screen_w, 0, self.screen_h, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        # Semi-transparent background
        glColor4f(0, 0, 0, 0.7)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(self.screen_w, 0)
        glVertex2f(self.screen_w, self.screen_h * 0.4)
        glVertex2f(0, self.screen_h * 0.4)
        glEnd()
        
        # Output lines
        y = 20
        for line in self.output_lines:
            text_renderer.draw_text(10, y, line, "small", (0.8, 0.8, 0.8))
            y += 18
        
        # Input line
        input_y = self.screen_h * 0.4 - 30
        text_renderer.draw_text(10, input_y, "> " + self.input_text + "_", 
                               "medium", (1.0, 1.0, 1.0))
        
        # Help hint
        text_renderer.draw_text(10, input_y - 25, "Type /help for commands | ESC to close", 
                               "small", (0.5, 0.5, 0.5))
        
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_FOG)


# Import numpy for teleport
import numpy as np

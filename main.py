#!/usr/bin/env python3
"""
Pythmc - Minecraft Clone
Main orchestrator - ties all systems together

V2.4 - The Better Quality Update
  Font outline, character customization, 3D menu backgrounds, first-person hand,
  multiplayer name tags, sneaking mechanic, HUD fixes

Controls:
  WASD - Move | Space - Jump | Shift - Sneak (ground) / Descend (fly) | Ctrl - Sprint
  Mouse Look | Left Click - Break/Attack | Right Click - Place/Use
  1-9 - Select Hotbar Slot | F - Toggle Fly (Creative) | / - Terminal (if cheats)
  G - Freeze Time | F11 - Fullscreen | Esc - Pause Menu | R - Respawn
  F5 - Toggle Third Person | Right Click (food) - Eat | Right Click (furnace block) - Open furnace
"""

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import time
import os
import random

from constants import *
from world import World, raycast
from player import Player
from entities import EntityManager, ItemDrop
from renderer import (
    ParticleSystem, CloudRenderer, HUD,
    draw_target_block, update_sky, init_gl, draw_player_body,
    draw_falling_blocks, get_character_colors, draw_first_person_hand
)
from menu import MainMenu, PauseMenu, SettingsMenu, CharacterCustomizationScreen
from inventory_ui import CraftingUI
from text_renderer import text_renderer
from textures import texture_manager
from sounds import sound_manager
from terminal import Terminal
from obj_loader import mob_renderer
from builder import StructureBuilder
from world_screens import WorldSelectScreen, WorldCreateScreen
from multiplayer_screens import HostGameScreen, JoinGameScreen
from network import multiplayer
from atmosphere import AtmosphereRenderer
from voice import voice_chat
from credits import CreditsScreen
from furnace_ui import FurnaceUI
from settings_manager import settings_manager
from io_system import io_manager
from physics import PhysicsManager
from disasters import DisasterManager
from cuda_manager import try_init_cupy, set_cuda_enabled, get_cuda_status, is_cuda_enabled
import world_manager


class GameState:
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    SETTINGS = "settings"
    WORLD_SELECT = "world_select"
    WORLD_CREATE = "world_create"
    CREDITS = "credits"
    BUILDER = "builder"
    HOST_GAME = "host_game"
    JOIN_GAME = "join_game"
    CHARACTER = "character"


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)
        pygame.display.gl_set_attribute(pygame.GL_DOUBLEBUFFER, 1)
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Pythmc")
        self.clock = pygame.time.Clock()
        self.running = True
        self.keys = {}
        self.mouse_captured = False

        text_renderer.init()
        texture_manager.init()
        sound_manager.init()

        # V2.3: CUDA GPU detection
        cuda_ok = try_init_cupy()
        cuda_pref = settings_manager.get("gpu", "cuda_enabled")
        set_cuda_enabled(cuda_ok and bool(cuda_pref))
        if cuda_ok:
            status = get_cuda_status()
            print(f"  CUDA: {status['gpu_name']}")
        
        self.step_timer = 0
        self.step_interval = 0.4
        self.dev_mode = False

        self.state = GameState.MENU
        self.previous_state = GameState.MENU

        self.main_menu = MainMenu(SCREEN_W, SCREEN_H)
        self.pause_menu = PauseMenu(SCREEN_W, SCREEN_H)
        self.settings_menu = SettingsMenu(SCREEN_W, SCREEN_H)
        self.crafting_ui = CraftingUI(SCREEN_W, SCREEN_H)
        self.furnace_ui = FurnaceUI(SCREEN_W, SCREEN_H)
        self.terminal = Terminal(SCREEN_W, SCREEN_H)
        self.builder = StructureBuilder(SCREEN_W, SCREEN_H)
        self.world_select = WorldSelectScreen(SCREEN_W, SCREEN_H)
        self.world_create = WorldCreateScreen(SCREEN_W, SCREEN_H)
        self.host_screen = HostGameScreen(SCREEN_W, SCREEN_H)
        self.join_screen = JoinGameScreen(SCREEN_W, SCREEN_H)
        self.credits_screen = CreditsScreen(SCREEN_W, SCREEN_H)
        self.character_screen = CharacterCustomizationScreen(SCREEN_W, SCREEN_H)

        self.current_world_name = None
        self.current_world_meta = None
        self.play_session_start = 0
        self.cheats_enabled = False

        self.world = None
        self.player = None
        self.entity_manager = None
        self.particles = None
        self.clouds = None
        self.hud = None
        self.atmosphere = None
        self.disaster_manager = None

        self.sensitivity = settings_manager.get("screen", "sensitivity")
        self.day_time = 0.25
        self.day_speed = settings_manager.get("world", "day_speed")
        self.world_time = 0.0

        self.last_break = 0
        self.last_place = 0
        self.fps_counter = 0
        self.fps_display = 0
        self.fps_timer = 0

        # V2.0 stat tracking
        self.blocks_dug_session = 0
        self.blocks_placed_session = 0
        self.days_survived = 0
        self.day_accumulator = 0.0

        self._load_mob_models()

    def _load_mob_models(self):
        mobs_dir = os.path.join(os.path.dirname(__file__), "mobs(withtextures)")
        if not os.path.exists(mobs_dir):
            mobs_dir = os.path.join(os.path.dirname(__file__), "mobs")
        
        if not os.path.exists(mobs_dir):
            return
        
        model_map = {
            "cow.obj": ENTITY_COW,
            "sheep.obj": ENTITY_SHEEP,
            "chicken.obj": ENTITY_CHICKEN,
            "zombie.obj": ENTITY_ZOMBIE,
            "skeleton.obj": ENTITY_SKELETON,
        }
        
        for filename, entity_type in model_map.items():
            obj_path = os.path.join(mobs_dir, filename)
            if os.path.exists(obj_path):
                mob_renderer.load_model(entity_type, obj_path, scale=1.0)

    def _init_game(self, world_meta=None):
        init_gl()
        
        if world_meta:
            seed = world_meta.get("seed", 42)
            gamemode = world_meta.get("gamemode", "creative")
            self.cheats_enabled = world_meta.get("cheats", False)
            self.current_world_name = world_meta["name"]
            self.current_world_meta = world_meta
        else:
            seed = SEED
            gamemode = "creative"
            self.cheats_enabled = False
            self.current_world_name = None
            self.current_world_meta = None
        
        self.play_session_start = time.time()
        self.world = World(seed=seed)
        self.player = Player(self.world)
        self.player.creative = (gamemode == "creative")
        self.entity_manager = EntityManager(self.world)
        self.particles = ParticleSystem()
        self.clouds = CloudRenderer(seed)
        self.atmosphere = AtmosphereRenderer(seed)
        self.hud = HUD(SCREEN_W, SCREEN_H)
        self.physics = PhysicsManager()
        self.day_time = 0.25
        self.world_time = 0.0

        # V2.0 stat tracking
        self.blocks_dug_session = 0
        self.blocks_placed_session = 0
        self.days_survived = 0
        self.day_accumulator = 0.0

        # Apply per-world settings
        ws = world_meta.get("world_settings", {}) if world_meta else {}
        if ws:
            for cat, vals in ws.items():
                for key, val in vals.items():
                    self._apply_setting(cat, key, val)

        # Load IO
        if self.current_world_name:
            io_manager.load_from_world(self.current_world_name)

        if multiplayer.is_connected():
            voice_chat.init(str(id(self)), multiplayer.client.server_ip if multiplayer.client else None)

        pcx, pcz = self.world.world_to_chunk(int(self.player.pos[0]), int(self.player.pos[2]))
        self.physics.init(self.world, pcx, pcz)

        self.disaster_manager = DisasterManager()

    def _apply_setting(self, category, key, value):
        """Apply a setting value to the game."""
        import constants as const
        if hasattr(const, key.upper()):
            setattr(const, key.upper(), value)

    def _save_and_exit(self):
        if self.current_world_name and self.current_world_meta:
            session_time = time.time() - self.play_session_start
            world_manager.update_play_time(self.current_world_name, session_time)

            # Save V2.0 stats
            world_manager.increment_stat(self.current_world_name, "blocks_dug", self.blocks_dug_session)
            world_manager.increment_stat(self.current_world_name, "blocks_placed", self.blocks_placed_session)
            world_manager.increment_stat(self.current_world_name, "days_survived", self.days_survived)
            
            player_data = {
                "pos": self.player.pos.tolist(),
                "yaw": self.player.yaw,
                "pitch": self.player.pitch,
                "health": self.player.health,
                "hunger": self.player.hunger,
                "armor": self.player.armor,
                "inventory": {
                    "hotbar": [
                        {"item": slot.item, "count": slot.count}
                        for slot in self.player.inventory.hotbar
                    ],
                    "main": [
                        [{"item": slot.item, "count": slot.count} for slot in row]
                        for row in self.player.inventory.main
                    ],
                },
                "selected_slot": self.player.selected_slot,
            }
            world_manager.save_player_data(self.current_world_name, player_data)

            # Save IO
            io_manager.save_to_world(self.current_world_name)
        
        self.world = None
        self.player = None
        self.entity_manager = None
        self.state = GameState.MENU

    def _center_mouse(self):
        pygame.mouse.set_pos(SCREEN_W // 2, SCREEN_H // 2)

    def _handle_menu_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
                return

            if self.state == GameState.MENU:
                result = self.main_menu.handle_event(event)
                if result == "play":
                    self.world_select.refresh()
                    self.state = GameState.WORLD_SELECT
                elif result == "host_multiplayer":
                    self.state = GameState.HOST_GAME
                elif result == "join_multiplayer":
                    self.state = GameState.JOIN_GAME
                elif result == "structure_builder":
                    self.state = GameState.BUILDER
                elif result == "settings":
                    self.previous_state = GameState.MENU
                    self.state = GameState.SETTINGS
                elif result == "credits":
                    self.state = GameState.CREDITS
                elif result == "character":
                    self.state = GameState.CHARACTER
                elif result == "quit":
                    self.running = False

            elif self.state == GameState.HOST_GAME:
                result = self.host_screen.handle_event(event)
                if result == "back":
                    self.state = GameState.MENU
                elif isinstance(result, dict) and result.get("action") == "host":
                    if multiplayer.host_game(result["world_name"], result["player_name"]):
                        self._init_game({"name": result["world_name"], "seed": 42, "gamemode": "creative", "cheats": True})
                        self.state = GameState.PLAYING
                        self.mouse_captured = True
                        pygame.mouse.set_visible(False)
                        pygame.event.set_grab(True)
                        self._center_mouse()
                    else:
                        self.host_screen.status = "Failed to host!"

            elif self.state == GameState.JOIN_GAME:
                result = self.join_screen.handle_event(event)
                if result == "back":
                    self.state = GameState.MENU
                elif isinstance(result, dict) and result.get("action") == "join":
                    if multiplayer.join_game(result["ip"], result["player_name"]):
                        self._init_game({"name": "Multiplayer", "seed": 42, "gamemode": "creative", "cheats": False})
                        self.state = GameState.PLAYING
                        self.mouse_captured = True
                        pygame.mouse.set_visible(False)
                        pygame.event.set_grab(True)
                        self._center_mouse()
                    else:
                        self.join_screen.status = "Failed to connect!"

            elif self.state == GameState.PAUSED:
                result = self.pause_menu.handle_event(event)
                if result == "resume":
                    self.state = GameState.PLAYING
                    self.mouse_captured = True
                    pygame.mouse.set_visible(False)
                    pygame.event.set_grab(True)
                    self._center_mouse()
                elif result == "settings":
                    self.previous_state = GameState.PAUSED
                    self.state = GameState.SETTINGS
                elif result == "quit_to_menu":
                    self._save_and_exit()
                    self.mouse_captured = False
                    pygame.mouse.set_visible(True)
                    pygame.event.set_grab(False)

            elif self.state == GameState.SETTINGS:
                result = self.settings_menu.handle_event(event)
                if result == "back":
                    self.sensitivity = settings_manager.get("screen", "sensitivity")
                    self.state = self.previous_state

            elif self.state == GameState.WORLD_SELECT:
                result = self.world_select.handle_event(event)
                if result == "back":
                    self.state = GameState.MENU
                elif result == "create_new":
                    self.state = GameState.WORLD_CREATE
                elif isinstance(result, dict) and result.get("action") == "play":
                    world_meta = result["world"]
                    self._init_game(world_meta)
                    self.state = GameState.PLAYING
                    self.mouse_captured = True
                    pygame.mouse.set_visible(False)
                    pygame.event.set_grab(True)
                    self._center_mouse()

            elif self.state == GameState.WORLD_CREATE:
                result = self.world_create.handle_event(event)
                if result == "back":
                    self.state = GameState.WORLD_SELECT
                elif isinstance(result, dict) and result.get("action") == "create":
                    try:
                        meta = world_manager.create_world(
                            result["name"],
                            result["gamemode"],
                            result["seed"],
                            result["show_coords"],
                            result.get("io_enabled", False),
                            result.get("world_settings", None),
                        )
                        self._init_game(meta)
                        self.state = GameState.PLAYING
                        self.mouse_captured = True
                        pygame.mouse.set_visible(False)
                        pygame.event.set_grab(True)
                        self._center_mouse()
                    except ValueError:
                        pass

            elif self.state == GameState.CREDITS:
                result = self.credits_screen.handle_event(event)
                if result == "back":
                    self.state = GameState.MENU

            elif self.state == GameState.CHARACTER:
                result = self.character_screen.handle_event(event)
                if result == "back":
                    self.state = GameState.MENU

    def _handle_game_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
                return

            if event.type == KEYDOWN:
                self.keys[event.key] = True

                if event.key == K_ESCAPE:
                    self.state = GameState.PAUSED
                    self.mouse_captured = False
                    pygame.mouse.set_visible(True)
                    pygame.event.set_grab(False)
                    return

                elif K_1 <= event.key <= K_9:
                    self.player.selected_slot = event.key - K_1
                elif event.key == K_f:
                    if self.player.creative:
                        self.player.flying = not self.player.flying
                elif event.key == K_g:
                    self.day_speed = 0.0 if self.day_speed > 0 else 0.005
                elif event.key == K_r:
                    if self.player.dead:
                        self.player.dead = False
                        self.player._spawn()
                elif event.key == K_F11:
                    pygame.display.toggle_fullscreen()
                elif event.key == K_e:
                    if self.crafting_ui.open:
                        self.crafting_ui.open = False
                        self.player.crafting_open = False
                        self.mouse_captured = True
                        pygame.mouse.set_visible(False)
                        pygame.event.set_grab(True)
                        self._center_mouse()
                    elif self.furnace_ui.open:
                        self.furnace_ui.open = False
                        self.mouse_captured = True
                        pygame.mouse.set_visible(False)
                        pygame.event.set_grab(True)
                        self._center_mouse()
                    else:
                        self.crafting_ui.open = True
                        self.player.crafting_open = True
                        self.mouse_captured = False
                        pygame.mouse.set_visible(True)
                        pygame.event.set_grab(False)
                elif event.key == K_F5:
                    self.player.third_person = not self.player.third_person
                elif event.key == K_F2 and (event.mod & KMOD_ALT):
                    self.dev_mode = not self.dev_mode
                elif event.key == K_SLASH:
                    if self.cheats_enabled:
                        self.terminal.toggle()
                        if self.terminal.open:
                            self.mouse_captured = False
                            pygame.mouse.set_visible(True)
                            pygame.event.set_grab(False)
                        else:
                            self.mouse_captured = True
                            pygame.mouse.set_visible(False)
                            pygame.event.set_grab(True)
                            self._center_mouse()
                    else:
                        self._output_to_screen("Cheats not enabled for this world!")

            elif event.type == KEYUP:
                self.keys[event.key] = False

            elif event.type == MOUSEBUTTONDOWN:
                if self.crafting_ui.open:
                    self.crafting_ui.handle_click(
                        event.pos[0], event.pos[1],
                        self.player.inventory,
                        event.button
                    )
                    return

                if self.furnace_ui.open:
                    self.furnace_ui.handle_click(
                        event.pos[0], event.pos[1],
                        self.player.inventory,
                        event.button
                    )
                    return

                if not self.mouse_captured:
                    self.mouse_captured = True
                    pygame.mouse.set_visible(False)
                    pygame.event.set_grab(True)
                    self._center_mouse()
                    return
                if event.button == 1:
                    self._break_or_attack()
                elif event.button == 3:
                    self._right_click_use()
                elif event.button == 4:
                    self.player.selected_slot = (self.player.selected_slot - 1) % 9
                elif event.button == 5:
                    self.player.selected_slot = (self.player.selected_slot + 1) % 9

            elif event.type == MOUSEMOTION and self.mouse_captured:
                dx, dy = event.rel
                self.player.yaw -= dx * self.sensitivity
                self.player.pitch += dy * self.sensitivity
                self.player.pitch = max(-89, min(89, self.player.pitch))
                self._center_mouse()

    def _break_or_attack(self):
        now = time.time()
        if now - self.last_break < BREAK_COOLDOWN:
            return

        if self.entity_manager.attack_entity(
            self.player.pos.copy(),
            self.player.get_forward(),
            5
        ):
            self.particles.emit_hit(self.player.pos + self.player.get_forward() * 2)
            sound_manager.play('entity_hurt')
            self.last_break = now
            return

        eye = self.player.get_eye_pos()
        hit, _, _ = raycast(self.world, eye, self.player.get_forward())
        if not hit:
            return
        x, y, z = hit
        block = self.world.get_block(x, y, z)
        if block == BEDROCK and not self.player.creative:
            return
        if block != AIR:
            # V2.1: TNT ignition
            if block == TNT:
                self.world.set_block(x, y, z, AIR)
                self.physics.trigger_tnt(x, y, z, self.world, self.entity_manager)
                sound_manager.play('entity_hurt', 0.8)
                self.last_break = now
                return

            self.world.set_block(x, y, z, AIR)
            self.particles.emit((x, y, z), block, 15)
            
            if not self.player.creative:
                drops = BLOCK_DROPS.get(block, [(block, 1, 1)])
                for item_type, min_count, max_count in drops:
                    count = random.randint(min_count, max_count)
                    if count > 0:
                        leftover = self.player.inventory.add_item(item_type, count)
                        if leftover > 0:
                            drop = ItemDrop([x + 0.5, y + 0.5, z + 0.5], item_type, leftover)
                            self.entity_manager.item_drops.append(drop)
            
            self._play_break_sound(block)
            self.last_break = now
            self.blocks_dug_session += 1
            self.physics.on_block_removed(x, y, z, block)
            cx, cz = self.world.world_to_chunk(x, z)
            key = self.world.get_chunk_key(cx, cz)
            if key in self.world.chunks:
                self.world.chunks[key].build_mesh(self.world)
                self.world.dirty_chunks.discard(key)

    def _right_click_use(self):
        now = time.time()
        if now - self.last_place < PLACE_COOLDOWN:
            return
        
        eye = self.player.get_eye_pos()
        hit, place_pos, _ = raycast(self.world, eye, self.player.get_forward())
        
        if hit:
            x, y, z = hit
            block = self.world.get_block(x, y, z)
            
            # Right-click on furnace block -> open furnace UI
            if block == FURNACE_BLOCK:
                if not self.furnace_ui.open:
                    self.furnace_ui.open = True
                    self.mouse_captured = False
                    pygame.mouse.set_visible(True)
                    pygame.event.set_grab(False)
                    self.last_place = now
                    return
            
            # Right-click on crafting table -> open crafting UI
            if block == CRAFTING_TABLE_BLOCK:
                if not self.crafting_ui.open:
                    self.crafting_ui.open = True
                    self.player.crafting_open = True
                    self.mouse_captured = False
                    pygame.mouse.set_visible(True)
                    pygame.event.set_grab(False)
                    self.last_place = now
                    return
        
        # Check if holding food -> eat
        held_item = self.player.inventory.hotbar[self.player.selected_slot].item
        if held_item in FOOD_PROPERTIES:
            if not self.player.eating and self.player.hunger < self.player.max_hunger:
                self.player.eat(held_item)
                self.last_place = now
                return
        
        # Check if holding armor -> equip
        if held_item in ARMOR_PROPERTIES:
            self.player.equip_armor(held_item)
            self.last_place = now
            return
        
        # Place block
        if not place_pos:
            return
        px, py, pz = place_pos
        if py < 0 or py >= CHUNK_HEIGHT:
            return
        block_type = self.player.hotbar[self.player.selected_slot]
        if block_type == AIR:
            return
        
        # Map item IDs to block IDs (e.g. TORCH_ITEM -> TORCH)
        block_type = ITEM_TO_BLOCK.get(block_type, block_type)
        
        # Only place actual blocks
        if block_type not in PLACEABLE_BLOCKS:
            return
        
        if self.player._pos_occupied(px, py, pz):
            return
        existing = self.world.get_block(px, py, pz)
        if existing not in (AIR, WATER, LAVA):
            return
        
        # Check if it's a placeable block (not a food/tool)
        if block_type in FOOD_PROPERTIES or block_type in ARMOR_PROPERTIES:
            return
        
        self.world.set_block(px, py, pz, block_type)
        self.physics.on_block_placed(px, py, pz, block_type)
        self.blocks_placed_session += 1
        # Consume item in survival
        if not self.player.creative:
            slot = self.player.inventory.hotbar[self.player.selected_slot]
            slot.count -= 1
            if slot.count <= 0:
                slot.clear()
        sound_manager.play('place_stone')
        self.last_place = now
        cx, cz = self.world.world_to_chunk(px, pz)
        key = self.world.get_chunk_key(cx, cz)
        if key in self.world.chunks:
            self.world.chunks[key].build_mesh(self.world)
            self.world.dirty_chunks.discard(key)

    def _play_break_sound(self, block):
        if block in (STONE, COBBLESTONE, IRON_ORE, GOLD_ORE, COAL_ORE, BEDROCK, DIAMOND_ORE, OBSIDIAN):
            sound_manager.play('break_stone')
        elif block in (DIRT, GRASS):
            sound_manager.play('break_dirt')
        elif block in (SAND, GRAVEL, CLAY):
            sound_manager.play('break_sand')
        elif block in (WOOD, PLANKS):
            sound_manager.play('break_wood')
        elif block == GLASS:
            sound_manager.play('break_glass')
        elif block == LEAVES:
            sound_manager.play('break_grass')
        elif block == TNT:
            sound_manager.play('break_wood')
        elif block == LAVA:
            sound_manager.play('break_stone')
        else:
            sound_manager.play('break_stone')

    def _update_game(self, dt):
        self.player.update(dt, self.keys)
        
        if multiplayer.is_connected():
            multiplayer.update(self.player.pos, self.player.yaw, self.player.pitch)
            if voice_chat.enabled:
                voice_chat.update_position(self.player.pos)
                voice_chat.update_other_players(multiplayer.get_other_players())
        
        if self.atmosphere:
            self.atmosphere.update(dt, self.player.pos, self.day_time, self.world,
                                   self.physics.wind)
        
        # Footstep sounds
        if self.player.on_ground and not self.player.flying:
            speed = abs(self.player.velocity[0]) + abs(self.player.velocity[2])
            if speed > 1.0:
                self.step_timer -= dt
                if self.step_timer <= 0:
                    self.step_timer = 0.4 if not self.player.sprinting else 0.25
                    bx = int(self.player.pos[0])
                    by = int(self.player.pos[1] - 0.1)
                    bz = int(self.player.pos[2])
                    block_below = self.world.get_block(bx, by, bz)
                    if block_below in (GRASS, LEAVES):
                        sound_manager.play('step_grass', 0.3)
                    elif block_below in (DIRT, SAND):
                        sound_manager.play('step_dirt', 0.3)
                    elif block_below in (STONE, COBBLESTONE):
                        sound_manager.play('step_stone', 0.3)
                    elif block_below in (WOOD, PLANKS):
                        sound_manager.play('step_wood', 0.3)
                    else:
                        sound_manager.play('step_stone', 0.3)
            else:
                self.step_timer = 0

        # Item drop pickup (FIXED - actually adds to inventory)
        alive_drops = []
        for drop in self.entity_manager.item_drops:
            if drop.can_pickup():
                dist = ((self.player.pos[0] - drop.pos[0])**2 +
                       (self.player.pos[1] - drop.pos[1])**2 +
                       (self.player.pos[2] - drop.pos[2])**2) ** 0.5
                if dist < 2.0:
                    leftover = self.player.inventory.add_item(drop.item_type, drop.count)
                    if leftover > 0:
                        drop.count = leftover
                        alive_drops.append(drop)
                    else:
                        sound_manager.play('entity_hurt', 0.2)
                    continue
            alive_drops.append(drop)
        self.entity_manager.item_drops = alive_drops

        # Update entities
        damage = self.entity_manager.update(dt, self.player.pos.copy(), self.day_time)
        if damage > 0:
            self.player.take_damage(damage)

        # Update furnace
        if self.furnace_ui.open:
            self.furnace_ui.update(dt)

        self.particles.update(dt)

        # V2.1: Physics update (falling blocks, fluid sim, wind, block gravity)
        rain_int = 0.0
        if self.atmosphere:
            rain_int = self.atmosphere.weather.rain_intensity
        physics_dirty = self.physics.update(
            dt, self.world, self.player.pos, self.day_time, rain_int)
        for cx, cz in physics_dirty:
            if (cx, cz) in self.world.chunks:
                self.world.chunks[(cx, cz)].mesh_dirty = True
                self.world.dirty_chunks.add((cx, cz))

        # V2.2: Disaster update
        if self.disaster_manager:
            rain_int_val = rain_int
            self.disaster_manager.update(
                dt, self.world, self.player.pos,
                self.world.seed, rain_int_val)
            self.disaster_manager.apply_chain_dirtying()

        pcx, pcz = self.world.world_to_chunk(int(self.player.pos[0]), int(self.player.pos[2]))
        self.world.update(pcx, pcz)

        self.world_time += dt
        self.day_time = (self.day_time + self.day_speed * dt) % 1.0

        # V2.0: Track days survived
        self.day_accumulator += self.day_speed * dt
        if self.day_accumulator >= 1.0:
            self.day_accumulator -= 1.0
            self.days_survived += 1

        # V2.0: IO trigger check
        if io_manager.enabled and self.current_world_name:
            game_state = {
                "health_below": self.player.health,
                "health_above": self.player.health,
                "hunger_below": self.player.hunger,
                "hunger_above": self.player.hunger,
                "daytime_below": self.day_time,
                "daytime_above": self.day_time,
                "position_above_y": self.player.pos[1],
                "position_below_y": self.player.pos[1],
                "blocks_placed_above": self.blocks_placed_session,
                "blocks_dug_above": self.blocks_dug_session,
                "days_survived_above": self.days_survived,
                "inventory_has": 0,
            }
            io_manager.update(game_state)

        self.fps_timer += dt
        self.fps_counter += 1
        if self.fps_timer >= 1.0:
            self.fps_display = self.fps_counter
            self.fps_counter = 0
            self.fps_timer = 0

    def _render_game(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Camera (first or third person)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(70, SCREEN_W / SCREEN_H, 0.1, 1000.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # V2.2: Disaster screen shake
        shake_x, shake_y = 0.0, 0.0
        if self.disaster_manager and self.disaster_manager.active_disaster:
            shake_amt = self.disaster_manager.screen_shake
            if shake_amt > 0:
                shake_x = (random.random() - 0.5) * shake_amt * 0.05
                shake_y = (random.random() - 0.5) * shake_amt * 0.05
        
        sneak_offset = 0.25 if self.player.sneaking else 0.0
        if self.player.third_person:
            # Third-person camera
            cam_dist = 4.0
            ry = math.radians(self.player.yaw)
            cam_x = self.player.pos[0] + math.sin(ry) * cam_dist + shake_x
            cam_y = self.player.pos[1] + PLAYER_HEIGHT + 1.0 - sneak_offset + shake_y
            cam_z = self.player.pos[2] + math.cos(ry) * cam_dist
            look = self.player.pos + np.array([0, PLAYER_HEIGHT * 0.8 - sneak_offset, 0])
            gluLookAt(cam_x, cam_y, cam_z, look[0], look[1], look[2], 0, 1, 0)
        else:
            eye = self.player.get_eye_pos()
            look = eye + self.player.get_forward()
            gluLookAt(eye[0] + shake_x, eye[1] + shake_y, eye[2],
                      look[0] + shake_x, look[1] + shake_y, look[2], 0, 1, 0)

        # Sky
        if self.atmosphere:
            self.atmosphere.draw_sky(self.day_time, self.player.pos)
        else:
            update_sky(self.day_time)

        # World
        pcx, pcz = self.world.world_to_chunk(int(self.player.pos[0]), int(self.player.pos[2]))
        self.world.draw(pcx, pcz)

        # Clouds
        self.clouds.draw(self.player.pos, self.world_time)

        # Player body in third person
        if self.player.third_person:
            # Build armor dict for rendering
            armor_dict = {}
            slot_names = {0: "helmet", 1: "chestplate", 2: "leggings", 3: "boots"}
            for i, item_id in enumerate(self.player.armor):
                if item_id:
                    armor_dict[slot_names[i]] = item_id
            
            draw_player_body(
                self.player.pos[0], self.player.pos[1], self.player.pos[2],
                self.player.yaw, self.player.pitch,
                self.player.arm_swing, self.player.walk_cycle,
                armor_slots=armor_dict,
                is_sneaking=self.player.sneaking,
                colors=get_character_colors()
            )

        # Entities and items
        self.entity_manager.draw()

        # V2.1: Falling blocks (explosion debris)
        draw_falling_blocks(self.physics.falling_blocks)

        # Other players
        self._draw_other_players()

        # Particles
        self.particles.draw()

        # Atmosphere effects
        if self.atmosphere:
            self.atmosphere.draw_particles(self.player.pos)
            if self.atmosphere.weather.rain_intensity > 0.1:
                self.atmosphere.draw_rain(self.player.pos, self.atmosphere.weather.rain_intensity)
            flash = self.atmosphere.get_lightning_flash()
            if flash > 0:
                glDisable(GL_LIGHTING)
                glEnable(GL_BLEND)
                glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
                glColor4f(1, 1, 1, flash * 0.5)
                glBegin(GL_QUADS)
                glVertex3f(self.player.pos[0] - 50, self.player.pos[1] + 50, self.player.pos[2] - 50)
                glVertex3f(self.player.pos[0] + 50, self.player.pos[1] + 50, self.player.pos[2] - 50)
                glVertex3f(self.player.pos[0] + 50, self.player.pos[1] + 50, self.player.pos[2] + 50)
                glVertex3f(self.player.pos[0] - 50, self.player.pos[1] + 50, self.player.pos[2] + 50)
                glEnd()
                glDisable(GL_BLEND)
                glEnable(GL_LIGHTING)

        # Target block highlight
        eye = self.player.get_eye_pos()
        hit, _, _ = raycast(self.world, eye, self.player.get_forward())
        draw_target_block(hit, FACE_VERTS)

        # First-person hand + held block
        if not self.player.third_person:
            draw_first_person_hand(self.player, SCREEN_W, SCREEN_H)

        # HUD
        stats = {
            "days": self.days_survived,
            "dug": self.blocks_dug_session,
            "placed": self.blocks_placed_session,
        }
        self.hud.draw(self.player, stats=stats)

        # V2.2: Disaster warning HUD
        if self.disaster_manager:
            dinfo = self.disaster_manager.get_disaster_info()
            if dinfo:
                self._draw_disaster_hud(dinfo)

        # Crafting UI
        self.crafting_ui.draw(self.player.inventory)
        
        # Furnace UI
        self.furnace_ui.draw(self.player.inventory)
        
        # Dev mode overlay
        if self.dev_mode:
            self._draw_debug_overlay()

    def _draw_debug_overlay(self):
        """Developer debug overlay (Alt+F2)."""
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        
        y = 10
        line_h = 18
        
        def line(txt, color=(1, 1, 1)):
            nonlocal y
            text_renderer.draw_text_shadow(10, y, txt, "small", color)
            y += line_h
        
        px, py, pz = self.player.pos
        cx, cz = self.world.world_to_chunk(int(px), int(pz))
        
        line("=== DEBUG (Alt+F2 to close) ===", (0.2, 1, 0.2))
        line(f"FPS: {self.fps_display}")
        line(f"Player: ({px:.2f}, {py:.2f}, {pz:.2f})")
        line(f"Chunk: ({cx}, {cz})")
        line(f"Velocity: ({self.player.velocity[0]:.2f}, {self.player.velocity[1]:.2f}, {self.player.velocity[2]:.2f})")
        line(f"On ground: {self.player.on_ground} | Flying: {self.player.flying}")
        line(f"Health: {self.player.health:.0f}/{self.player.max_health:.0f} | Hunger: {self.player.hunger:.0f}/{self.player.max_hunger:.0f}")
        line(f"Saturation: {self.player.saturation:.1f}")
        armor_def = self.player.get_armor_defense()
        line(f"Armor: {self.player.armor} (defense: {armor_def})")
        line(f"Creative: {self.player.creative} | Dead: {self.player.dead}")
        
        # Chunk stats
        loaded = len(self.world.chunks)
        dirty = len(self.world.dirty_chunks)
        pending = len(self.world.pending_chunks)
        line(f"Chunks: {loaded} loaded, {dirty} dirty, {pending} pending")
        line(f"Render distance: {RENDER_DISTANCE}")
        
        # Block at crosshair
        eye = self.player.get_eye_pos()
        hit, place_pos, face = raycast(self.world, eye, self.player.get_forward())
        if hit:
            bx, by, bz = hit
            block = self.world.get_block(bx, by, bz)
            bname = BLOCK_NAMES.get(block, f"Unknown({block})")
            line(f"Target: [{bx}, {by}, {bz}] = {bname} (id={block})", (1, 1, 0.3))
            if place_pos:
                line(f"Place: [{place_pos[0]}, {place_pos[1]}, {place_pos[2]}]")
            if face is not None:
                face_names = ["+Y (top)", "-Y (bottom)", "+X (right)", "-X (left)", "+Z (front)", "-Z (back)"]
                line(f"Face: {face_names[face] if face < len(face_names) else face}")
            
            # Show block faces/neighbors
            line("--- Block Neighbors ---", (0.5, 1, 1))
            for fn, (ndx, ndy, ndz) in zip(["+Y", "-Y", "+X", "-X", "+Z", "-Z"], FACE_DIRS):
                nx, ny, nz = bx+ndx, by+ndy, bz+ndz
                nb = self.world.get_block(nx, ny, nz)
                nbname = BLOCK_NAMES.get(nb, f"Unknown({nb})")
                solid = "SOLID" if nb in SOLID_BLOCKS else "air/transparent"
                line(f"  {fn}: [{nx},{ny},{nz}] = {nbname} ({solid})")
            
            # Block JSON
            line("--- Block Data ---", (0.5, 1, 1))
            block_data = {
                "id": block, "name": bname,
                "solid": block in SOLID_BLOCKS,
                "transparent": block in TRANSPARENT if 'TRANSPARENT' in dir() else False,
                "position": [bx, by, bz],
                "faces": {fn: BLOCK_NAMES.get(self.world.get_block(bx+ndx, by+ndy, bz+ndz), "AIR")
                          for fn, (ndx, ndy, ndz) in zip(["+Y","-Y","+X","-X","+Z","-Z"], FACE_DIRS)},
            }
            for k, v in block_data.items():
                line(f"  {k}: {v}")
        
        # Day time
        line(f"Day time: {self.day_time:.3f} (speed: {self.day_speed})")
        
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)

    def _draw_disaster_hud(self, info):
        """Draw disaster warning HUD at top-center of screen."""
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)

        name = info["name"]
        intensity = info["intensity"]
        timer = info["timer"]

        # Pulsing red tint based on intensity
        pulse = 0.6 + 0.4 * math.sin(time.time() * 4)
        r = min(1.0, 0.8 + intensity * 0.2)
        g = max(0.0, 0.2 - intensity * 0.15)
        b = 0.1

        # Warning bar at top
        bar_h = 30
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(r, g, b, 0.5 * pulse)
        glBegin(GL_QUADS)
        glVertex2f(0, SCREEN_H)
        glVertex2f(SCREEN_W, SCREEN_H)
        glVertex2f(SCREEN_W, SCREEN_H - bar_h)
        glVertex2f(0, SCREEN_H - bar_h)
        glEnd()
        glDisable(GL_BLEND)

        # Disaster name
        text_renderer.draw_text_shadow(
            SCREEN_W // 2 - 60, SCREEN_H - 22,
            f"!! {name} !!", "small", (1, 0.9, 0.2))

        # Timer
        text_renderer.draw_text_shadow(
            SCREEN_W // 2 - 30, SCREEN_H - 40,
            f"{timer:.1f}s", "small", (1, 1, 1))

        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)

    def _draw_other_players(self):
        if not multiplayer.is_connected():
            return
        
        other_players = multiplayer.get_other_players()
        for pid, pdata in other_players.items():
            pos = pdata.get("pos", [0, 0, 0])
            yaw = pdata.get("yaw", 0)
            name = pdata.get("name", "Player")
            
            from renderer import draw_player_body
            draw_player_body(pos[0], pos[1], pos[2], yaw, 0, 0, 0)
            self._draw_name_tag(pos[0], pos[1] + 2.0, pos[2], name)

    def _draw_name_tag(self, x, y, z, name):
        glPushMatrix()
        glTranslatef(x, y, z)
        
        glDisable(GL_LIGHTING)
        glDisable(GL_FOG)
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Billboard: always face camera
        modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
        glLoadIdentity()
        glTranslatef(0, 0, -0.1)
        for i in range(16):
            if i % 4 < 3:
                modelview[i] = 0.0
        modelview[0] = modelview[5] = modelview[10] = 1.0
        glLoadMatrixf(modelview)
        glTranslatef(x, y, z)
        
        # Background
        tw = text_renderer.get_text_width(name, "medium")
        glColor4f(0, 0, 0, 0.5)
        glBegin(GL_QUADS)
        glVertex2f(-tw // 2 - 4, -4)
        glVertex2f(tw // 2 + 4, -4)
        glVertex2f(tw // 2 + 4, 16)
        glVertex2f(-tw // 2 - 4, 16)
        glEnd()
        
        text_renderer.draw_text(-tw // 2, 0, name, "medium", (1, 1, 1))
        
        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_FOG)
        glEnable(GL_LIGHTING)
        glPopMatrix()

    def _output_to_screen(self, msg):
        print(msg)

    def run(self):
        print("=" * 50)
        print("  Pythmc - Minecraft Clone")
        print("  V2.4 - The Better Quality Update")
        print("=" * 50)
        print("  WASD - Move | Space - Jump | Ctrl - Sprint")
        print("  F - Fly (Creative) | / - Terminal (if cheats enabled)")
        print("  Mouse - Look | LClick - Break/Attack | RClick - Use/Place")
        print("  1-9 - Hotbar | E - Crafting/Furnace | R - Respawn")
        print("  F5 - Third Person | G - Freeze Time | F11 - Fullscreen")
        print("  Esc - Pause Menu")
        print("=" * 50)

        dt = 0
        while self.running:
            if self.state == GameState.MENU:
                self._handle_menu_events()
                self.main_menu.update(dt, pygame.mouse.get_pos())
                self.main_menu.draw()
                pygame.display.flip()

            elif self.state == GameState.PLAYING:
                self._handle_game_events()
                if self.state == GameState.PLAYING:
                    self._update_game(dt)
                    self._render_game()
                    pygame.display.flip()

                    mode = "Creative" if self.player.creative else "Survival"
                    fly = "[Fly]" if self.player.flying else ""
                    sprint = "[Sprint]" if self.player.sprinting else ""
                    sneak = "[Sneak]" if self.player.sneaking else ""
                    water = "[Swim]" if self.player.in_water else ""
                    dead = "[DEAD]" if self.player.dead else ""
                    tp = "[TP]" if self.player.third_person else ""
                    mobs = f"Mobs:{len(self.entity_manager.entities)}"
                    px, py, pz = self.player.pos
                    caption = f"Pythmc V2.4 | {mode} {fly}{sprint}{sneak}{water}{dead}{tp} | {self.fps_display} FPS | {mobs} | {px:.1f},{py:.1f},{pz:.1f}"
                    pygame.display.set_caption(caption)

            elif self.state == GameState.PAUSED:
                self._handle_menu_events()
                self.pause_menu.update(dt, pygame.mouse.get_pos())
                self._render_game()
                self.pause_menu.draw()
                pygame.display.flip()

            elif self.state == GameState.SETTINGS:
                self._handle_menu_events()
                self.settings_menu.update(dt, pygame.mouse.get_pos())
                self.settings_menu.draw()
                pygame.display.flip()

            elif self.state == GameState.WORLD_SELECT:
                self._handle_menu_events()
                self.world_select.update(dt, pygame.mouse.get_pos())
                self.world_select.draw()
                pygame.display.flip()

            elif self.state == GameState.WORLD_CREATE:
                self._handle_menu_events()
                self.world_create.update(dt, pygame.mouse.get_pos())
                self.world_create.draw()
                pygame.display.flip()

            elif self.state == GameState.CREDITS:
                self._handle_menu_events()
                self.credits_screen.update(dt, pygame.mouse.get_pos())
                self.credits_screen.draw()
                pygame.display.flip()

            elif self.state == GameState.HOST_GAME:
                self._handle_menu_events()
                self.host_screen.update(dt, pygame.mouse.get_pos())
                self.host_screen.draw()
                pygame.display.flip()

            elif self.state == GameState.JOIN_GAME:
                self._handle_menu_events()
                self.join_screen.update(dt, pygame.mouse.get_pos())
                self.join_screen.draw()
                pygame.display.flip()

            elif self.state == GameState.CHARACTER:
                self._handle_menu_events()
                self.character_screen.update(dt, pygame.mouse.get_pos())
                self.character_screen.draw()
                pygame.display.flip()

            dt = self.clock.tick(FPS) / 1000.0

        pygame.quit()


if __name__ == "__main__":
    Game().run()

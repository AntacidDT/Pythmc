"""Pythmc - Player - V1.9"""

import numpy as np
import math
from pygame.locals import *
from constants import *
from world import raycast
from inventory_ui import Inventory


class Player:
    def __init__(self, world):
        self.world = world
        self._spawn()

    def _spawn(self):
        spawn_x, spawn_z = 0, 0
        
        pcx, pcz = self.world.world_to_chunk(spawn_x, spawn_z)
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                self.world.get_chunk(pcx + dx, pcz + dz)
        
        self.pos = np.array([spawn_x + 0.5, 100.0, spawn_z + 0.5], dtype=np.float64)
        self.velocity = np.array([0.0, 0.0, 0.0], dtype=np.float64)
        self.yaw = 0.0
        self.pitch = 0.0
        self.on_ground = False
        self.flying = False
        self.health = 20.0
        self.max_health = 20.0
        self.hunger = 20.0
        self.max_hunger = 20.0
        self.saturation = 5.0
        self.max_saturation = 20.0
        self.creative = False
        self.inventory = Inventory(creative=self.creative)
        self.selected_slot = 0
        self.fall_distance = 0.0
        self.crafting_open = False
        self.sprinting = False
        self.in_water = False
        self.in_lava = False
        self.lava_damage_timer = 0.0
        self.dead = False
        self.respawn_timer = 0.0
        self.attack_cooldown = 0.0
        self.hurt_timer = 0.0
        self.spawn_immunity = 3.0
        
        # Walking animation
        self.walk_cycle = 0.0
        self.arm_swing = 0.0
        
        # Sneaking
        self.sneaking = False
        
        # Eating
        self.eating = False
        self.eat_timer = 0.0
        self.eat_duration = 1.6
        self.eat_item = None
        
        # Third person
        self.third_person = False
        
        # Armor (4 slots: helmet=0, chestplate=1, leggings=2, boots=3)
        self.armor = [0, 0, 0, 0]  # item IDs, 0 = empty
        
        # Regen cooldown
        self.regen_cooldown = 0.0

    @property
    def hotbar(self):
        return [slot.item for slot in self.inventory.hotbar]

    def get_forward(self):
        ry = math.radians(self.yaw)
        rp = math.radians(self.pitch)
        return np.array([-math.sin(ry)*math.cos(rp), -math.sin(rp), -math.cos(ry)*math.cos(rp)])

    def get_right(self):
        ry = math.radians(self.yaw)
        return np.array([-math.cos(ry), 0, math.sin(ry)])

    def get_eye_pos(self):
        height = PLAYER_HEIGHT - (0.25 if self.sneaking else 0)
        return self.pos + np.array([0, height, 0])

    def _check_in_water(self):
        eye = self.get_eye_pos()
        bx, by, bz = int(math.floor(eye[0])), int(math.floor(eye[1])), int(math.floor(eye[2]))
        return self.world.get_block(bx, by, bz) == WATER

    def _check_in_lava(self):
        eye = self.get_eye_pos()
        bx, by, bz = int(math.floor(eye[0])), int(math.floor(eye[1])), int(math.floor(eye[2]))
        return self.world.get_block(bx, by, bz) == LAVA

    def get_armor_defense(self):
        """Calculate total armor defense points."""
        total = 0
        for item_id in self.armor:
            if item_id and item_id in ARMOR_PROPERTIES:
                total += ARMOR_PROPERTIES[item_id][0]
        return total

    def eat(self, item_type):
        """Try to eat a food item. Returns True if successful."""
        if item_type not in FOOD_PROPERTIES:
            return False
        if self.hunger >= self.max_hunger:
            return False
        
        self.eating = True
        self.eat_timer = 0.0
        self.eat_item = item_type
        return True

    def _finish_eating(self):
        """Complete eating the current item."""
        if self.eat_item is None:
            return
        
        hunger_restore, saturation, is_cooked = FOOD_PROPERTIES[self.eat_item]
        self.hunger = min(self.max_hunger, self.hunger + hunger_restore)
        self.saturation = min(self.hunger, self.saturation + saturation)
        
        # Remove one item from held slot
        slot = self.inventory.hotbar[self.selected_slot]
        if not slot.is_empty():
            slot.count -= 1
            if slot.count <= 0:
                slot.clear()
        
        self.eating = False
        self.eat_timer = 0.0
        self.eat_item = None

    def equip_armor(self, item_type):
        """Try to equip armor from held item. Returns True if equipped."""
        if item_type not in ARMOR_PROPERTIES:
            return False
        
        _, slot_type = ARMOR_PROPERTIES[item_type]
        slot_index = {"helmet": 0, "chestplate": 1, "leggings": 2, "boots": 3}[slot_type]
        
        # Swap current armor with held
        old_armor = self.armor[slot_index]
        self.armor[slot_index] = item_type
        
        # Replace held item with old armor (or clear if empty)
        held = self.inventory.hotbar[self.selected_slot]
        if old_armor:
            held.item = old_armor
        else:
            held.count -= 1
            if held.count <= 0:
                held.clear()
        
        return True

    def update(self, dt, keys):
        if self.dead:
            self.respawn_timer -= dt
            if self.respawn_timer <= 0:
                self.dead = False
                self._spawn()
            return

        if self.crafting_open:
            return

        if self.spawn_immunity > 0:
            self.spawn_immunity -= dt

        self.in_water = self._check_in_water()
        self.in_lava = self._check_in_lava()
        self.sprinting = keys.get(K_LCTRL, False) and not self.in_water and not self.in_lava
        
        # Sneaking: Shift on ground when not flying
        self.sneaking = (keys.get(K_LSHIFT, False) and self.on_ground
                         and not self.flying and not self.in_water and not self.in_lava)
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt
        if self.hurt_timer > 0:
            self.hurt_timer -= dt
        
        # Regen cooldown
        if self.regen_cooldown > 0:
            self.regen_cooldown -= dt

        # V2.1: Lava damage
        if self.in_lava and not self.creative:
            self.lava_damage_timer -= dt
            if self.lava_damage_timer <= 0:
                self.take_damage(4)
                self.lava_damage_timer = 0.5
        
        # Eating update
        if self.eating:
            self.eat_timer += dt
            if self.eat_timer >= self.eat_duration:
                self._finish_eating()
            return

        forward = self.get_forward()
        right = self.get_right()
        forward[1] = 0
        n = np.linalg.norm(forward)
        if n > 0: forward /= n
        right[1] = 0
        n = np.linalg.norm(right)
        if n > 0: right /= n

        move = np.array([0.0, 0.0, 0.0])
        if self.flying:
            speed = FLY_SPEED
        elif self.in_water:
            speed = SWIM_SPEED
        elif self.sprinting:
            speed = SPRINT_SPEED
        elif self.sneaking:
            speed = WALK_SPEED * 0.4
        else:
            speed = WALK_SPEED

        if keys.get(K_w): move += forward
        if keys.get(K_s): move -= forward
        if keys.get(K_a): move += right
        if keys.get(K_d): move -= right
        
        moving = np.linalg.norm(move) > 0
        if moving:
            move = move / np.linalg.norm(move) * speed

        self.velocity[0] = move[0]
        self.velocity[2] = move[2]

        # Walk animation
        if moving and self.on_ground and not self.flying:
            anim_speed = 6.0 if not self.sprinting else 9.0
            self.walk_cycle += dt * anim_speed
            self.arm_swing = math.sin(self.walk_cycle) * 45
        elif not self.on_ground and not self.flying:
            self.arm_swing = 30
        else:
            self.arm_swing *= 0.85

        if self.flying:
            if keys.get(K_SPACE): self.velocity[1] = speed
            elif keys.get(K_LSHIFT): self.velocity[1] = -speed
            else: self.velocity[1] = 0
        elif self.in_lava:
            if keys.get(K_SPACE):
                self.velocity[1] = 2.0
            self.velocity[1] += 0.8 * dt
            self.velocity[1] *= WATER_DRAG * 0.8
            self.velocity[0] *= WATER_DRAG * 0.8
            self.velocity[2] *= WATER_DRAG * 0.8
        elif self.in_water:
            if keys.get(K_SPACE):
                self.velocity[1] = 3.5
            self.velocity[1] += 1.5 * dt
            self.velocity[1] *= WATER_DRAG
            self.velocity[0] *= WATER_DRAG
            self.velocity[2] *= WATER_DRAG
        else:
            if keys.get(K_SPACE) and self.on_ground:
                self.velocity[1] = JUMP_SPEED
                self.on_ground = False
            self.velocity[1] += GRAVITY * dt
            self.velocity[1] = max(self.velocity[1], -50.0)

        new_pos = self.pos + self.velocity * dt
        new_pos = self._check_collision(new_pos)

        # Sneaking edge protection: prevent walking off blocks
        if self.sneaking and new_pos[1] <= self.pos[1] + 0.01:
            hw = PLAYER_WIDTH / 2
            has_support = False
            for dx in [-hw, 0, hw]:
                for dz in [-hw, 0, hw]:
                    bx = int(math.floor(new_pos[0] + dx))
                    bz = int(math.floor(new_pos[2] + dz))
                    by = int(math.floor(self.pos[1] - 0.1))
                    if self.world.get_block(bx, by, bz) in SOLID_BLOCKS:
                        has_support = True
                        break
                if has_support:
                    break
            if not has_support:
                new_pos[0] = self.pos[0]
                new_pos[2] = self.pos[2]

        if new_pos[1] < self.pos[1] and not self.flying and not self.in_water and not self.in_lava:
            self.fall_distance += self.pos[1] - new_pos[1]
        elif self.on_ground or self.in_water or self.in_lava:
            if self.fall_distance > 3.0 and not self.creative and self.spawn_immunity <= 0:
                damage = self.fall_distance - 3.0
                armor_def = self.get_armor_defense()
                if armor_def > 0:
                    damage *= max(0.2, 1.0 - armor_def / 25.0)
                self.health -= damage
                self.health = max(0, self.health)
                if self.health <= 0:
                    self.die()
            self.fall_distance = 0.0

        self.pos = new_pos

        if self.pos[1] < -10:
            self.health = 0
            self.die()

        # Hunger system (survival only)
        if not self.creative:
            # Drain hunger based on activity
            drain = dt * 0.01  # Base drain
            if self.sprinting:
                drain *= 4.0  # Sprinting drains 4x
            elif moving:
                drain *= 2.0  # Walking drains 2x
            
            # Drain saturation first, then hunger
            if self.saturation > 0:
                self.saturation -= drain * 5
                self.saturation = max(0, self.saturation)
            else:
                self.hunger -= drain * 3
                self.hunger = max(0, self.hunger)
            
            # Starvation damage
            if self.hunger <= 0:
                self.regen_cooldown -= dt
                if self.regen_cooldown <= 0:
                    self.take_damage(1.0)
                    self.regen_cooldown = 4.0
            
            # Natural regen when well-fed (hunger >= 17, not moving, saturation > 0)
            elif self.hunger >= 17 and self.saturation > 0 and not moving:
                if self.health < self.max_health:
                    self.regen_cooldown -= dt
                    if self.regen_cooldown <= 0:
                        self.health = min(self.max_health, self.health + 1.0)
                        self.saturation -= 1.0
                        self.regen_cooldown = 0.5

    def take_damage(self, amount):
        if self.creative or self.dead or self.spawn_immunity > 0:
            return
        
        # Apply armor reduction
        armor_def = self.get_armor_defense()
        if armor_def > 0:
            amount *= max(0.2, 1.0 - armor_def / 25.0)
        
        self.health -= amount
        self.hurt_timer = 0.5
        self.regen_cooldown = 0.5
        if self.health <= 0:
            self.die()

    def die(self):
        if not self.dead:
            self.dead = True
            self.respawn_timer = 3.0
            self.velocity = np.array([0, 0, 0])

    def _check_collision(self, new_pos):
        hw = PLAYER_WIDTH / 2
        result = new_pos.copy()
        
        for axis in range(3):
            test_pos = self.pos.copy()
            test_pos[axis] = new_pos[axis]
            
            if axis == 1 and not self.flying:
                # Swept collision for Y axis - step through to prevent tunneling
                dy = new_pos[1] - self.pos[1]
                steps = max(1, int(abs(dy) * 2) + 1)
                step_dy = dy / steps
                collision = False
                for s in range(steps):
                    test_y = self.pos[1] + step_dy * (s + 1)
                    test_pos[1] = test_y
                    for dx in [-hw, 0, hw]:
                        for dz in [-hw, 0, hw]:
                            for ddy in [0.05, PLAYER_HEIGHT * 0.5, PLAYER_HEIGHT - 0.05]:
                                bx = int(math.floor(test_pos[0] + dx))
                                by = int(math.floor(test_y + ddy))
                                bz = int(math.floor(test_pos[2] + dz))
                                block = self.world.get_block(bx, by, bz)
                                if block in SOLID_BLOCKS:
                                    collision = True
                                    break
                            if collision: break
                        if collision: break
                    if collision:
                        break
            else:
                collision = False
                for dx in [-hw, 0, hw]:
                    for dz in [-hw, 0, hw]:
                        for dy in [0.05, PLAYER_HEIGHT * 0.5, PLAYER_HEIGHT - 0.05]:
                            cx = test_pos[0] + dx
                            cy = test_pos[1] + dy
                            cz = test_pos[2] + dz
                            bx, by, bz = int(math.floor(cx)), int(math.floor(cy)), int(math.floor(cz))
                            block = self.world.get_block(bx, by, bz)
                            if block in SOLID_BLOCKS:
                                collision = True
                                break
                        if collision: break
                    if collision: break
            
            if collision:
                if axis == 1 and self.velocity[1] < 0:
                    # Snap to top of the block we hit
                    result[axis] = self.pos[axis]
                    self.on_ground = True
                elif axis == 1 and self.velocity[1] > 0:
                    result[axis] = self.pos[axis]
                else:
                    result[axis] = self.pos[axis]
                self.velocity[axis] = 0
            else:
                if axis == 1: self.on_ground = False
        return result

    def _pos_occupied(self, x, y, z):
        hw = PLAYER_WIDTH / 2
        for dx in [-hw, hw]:
            for dz in [-hw, hw]:
                for dy in [0.05, PLAYER_HEIGHT * 0.5, PLAYER_HEIGHT - 0.05]:
                    px, py, pz = self.pos[0]+dx, self.pos[1]+dy, self.pos[2]+dz
                    if int(math.floor(px))==x and int(math.floor(py))==y and int(math.floor(pz))==z:
                        return True
        return False

    def get_attack_target(self):
        eye = self.get_eye_pos()
        direction = self.get_forward()
        hit, _, _ = raycast(self.world, eye, direction, max_dist=4.0)
        return hit

"""Pythmc - Entity System with Mobs"""

import numpy as np
import math
import random
import os
from sounds import sound_manager
from OpenGL.GL import *
from constants import *
from obj_loader import mob_renderer


class Entity:
    def __init__(self, entity_type, pos, world):
        self.entity_type = entity_type
        self.pos = np.array(pos, dtype=np.float64)
        self.velocity = np.array([0.0, 0.0, 0.0], dtype=np.float64)
        self.rotation = random.uniform(0, 360)
        self.world = world
        
        stats = ENTITY_STATS.get(entity_type, (10, 2.0, 0, False, 0))
        self.max_health = stats[0]
        self.health = float(stats[0])
        self.speed = stats[1]
        self.damage = stats[2]
        self.hostile = stats[3]
        self.attack_range = stats[4]
        
        self.on_ground = False
        self.dead = False
        self.death_timer = 0.0
        self.hurt_timer = 0.0
        
        self.ai_state = "idle"
        self.ai_timer = random.uniform(2, 6)
        self.target_pos = None
        self.attack_cooldown = 0.0
        self.aggro_range = 16.0
        self.wander_range = 10.0
        self.home_pos = np.array(pos, dtype=np.float64)
        
        self.walk_cycle = 0.0
        self.hit_flash = 0.0
        self.flee_timer = 0.0
        self.sound_timer = random.uniform(5, 15)

    def update(self, dt, player_pos):
        if self.dead:
            self.death_timer -= dt
            return self.death_timer > 0

        if self.hurt_timer > 0:
            self.hurt_timer -= dt
        if self.hit_flash > 0:
            self.hit_flash -= dt
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt

        self._update_ai(dt, player_pos)
        
        self.sound_timer -= dt
        if self.sound_timer <= 0:
            self.sound_timer = random.uniform(8, 20)
            dist = np.linalg.norm(player_pos - self.pos)
            if dist < 20:
                sound_manager.play(self.entity_type, 0.2)

        self.velocity[1] += GRAVITY * dt
        self.velocity[1] = max(self.velocity[1], -50.0)

        dt_move = dt
        new_x = self.pos[0] + self.velocity[0] * dt_move
        new_y = self.pos[1] + self.velocity[1] * dt_move
        new_z = self.pos[2] + self.velocity[2] * dt_move

        bx = int(math.floor(new_x))
        by = int(math.floor(new_y))
        bz = int(math.floor(new_z))
        
        block_below = self.world.get_block(bx, by, bz)
        block_at_feet = self.world.get_block(int(math.floor(self.pos[0])), 
                                              int(math.floor(self.pos[1])), 
                                              int(math.floor(self.pos[2])))
        
        if block_below in SOLID_BLOCKS and self.velocity[1] <= 0:
            new_y = by + 1.0
            self.velocity[1] = 0
            self.on_ground = True
        elif block_at_feet in SOLID_BLOCKS:
            new_y = self.pos[1] + 1.0
            self.velocity[1] = 2.0
            self.on_ground = False
        else:
            self.on_ground = False

        check_x = int(math.floor(new_x))
        check_z = int(math.floor(new_z))
        check_y = int(math.floor(self.pos[1]))
        
        block_ahead = self.world.get_block(check_x, check_y, check_z)
        if block_ahead in SOLID_BLOCKS:
            new_x = self.pos[0]
            new_z = self.pos[2]
            if self.ai_state == "wander":
                self.ai_timer = 0

        self.pos[0] = new_x
        self.pos[1] = new_y
        self.pos[2] = new_z

        if self.pos[1] < -20:
            self.dead = True
            self.death_timer = 0.0
            return False

        speed_xz = math.sqrt(self.velocity[0]**2 + self.velocity[2]**2)
        if speed_xz > 0.1:
            self.walk_cycle += dt * speed_xz * 3

        return True

    def _update_ai(self, dt, player_pos):
        dist_to_player = np.linalg.norm(player_pos - self.pos)
        
        if self.hostile:
            self._update_hostile_ai(dt, player_pos, dist_to_player)
        else:
            self._update_passive_ai(dt, player_pos)

    def _update_hostile_ai(self, dt, player_pos, dist_to_player):
        if dist_to_player < self.aggro_range and dist_to_player > self.attack_range:
            direction = player_pos - self.pos
            direction[1] = 0
            n = np.linalg.norm(direction)
            if n > 0:
                direction /= n
            self.velocity[0] = direction[0] * self.speed
            self.velocity[2] = direction[2] * self.speed
            self.rotation = math.degrees(math.atan2(-direction[0], -direction[2]))
            self.ai_state = "chase"
        elif dist_to_player <= self.attack_range and self.attack_cooldown <= 0:
            self.velocity[0] = 0
            self.velocity[2] = 0
            self.ai_state = "attack"
            self.attack_cooldown = 1.0
            return "attack"
        else:
            self._wander(dt)

    def _update_passive_ai(self, dt, player_pos):
        dist_to_player = np.linalg.norm(player_pos - self.pos)
        
        should_flee = False
        
        if dist_to_player < 2.0:
            should_flee = True
        elif self.hurt_timer > 0:
            should_flee = True
            self.flee_timer = 3.0
        
        if hasattr(self, 'flee_timer') and self.flee_timer > 0:
            self.flee_timer -= dt
            should_flee = True
        
        if should_flee:
            direction = self.pos - player_pos
            direction[1] = 0
            n = np.linalg.norm(direction)
            if n > 0:
                direction /= n
            self.velocity[0] = direction[0] * self.speed * 1.2
            self.velocity[2] = direction[2] * self.speed * 1.2
            self.rotation = math.degrees(math.atan2(-direction[0], -direction[2]))
            self.ai_state = "flee"
        else:
            self._wander(dt)

    def _wander(self, dt):
        self.ai_timer -= dt
        if self.ai_timer <= 0:
            self.ai_timer = random.uniform(3, 8)
            if random.random() < 0.4:
                self.velocity[0] = 0
                self.velocity[2] = 0
                self.ai_state = "idle"
            else:
                angle = random.uniform(0, math.pi * 2)
                self.velocity[0] = math.sin(angle) * self.speed * 0.5
                self.velocity[2] = math.cos(angle) * self.speed * 0.5
                self.rotation = math.degrees(angle)
                self.ai_state = "wander"

        dist_from_home = np.linalg.norm(self.pos - self.home_pos)
        if dist_from_home > self.wander_range:
            direction = self.home_pos - self.pos
            direction[1] = 0
            n = np.linalg.norm(direction)
            if n > 0:
                direction /= n
            self.velocity[0] = direction[0] * self.speed * 0.5
            self.velocity[2] = direction[2] * self.speed * 0.5
            self.rotation = math.degrees(math.atan2(-direction[0], -direction[2]))

    def _get_height(self):
        if self.entity_type == ENTITY_CHICKEN:
            return 0.6
        elif self.entity_type in (ENTITY_SHEEP):
            return 0.8
        elif self.entity_type == ENTITY_COW:
            return 1.2
        elif self.entity_type == ENTITY_ZOMBIE:
            return 1.8
        elif self.entity_type == ENTITY_SKELETON:
            return 1.8
        return 1.0

    def take_damage(self, amount):
        if self.dead:
            return
        self.health -= amount
        self.hurt_timer = 0.3
        self.hit_flash = 0.2
        sound_manager.play(f'entity_hurt', 0.3)
        if not self.hostile:
            self.flee_timer = 4.0
        if self.health <= 0:
            self.die()

    def die(self):
        if not self.dead:
            self.dead = True
            self.death_timer = 1.0
            sound_manager.play('entity_death', 0.3)

    def get_drops(self):
        drop_list = ENTITY_DROPS.get(self.entity_type, [])
        result = []
        for item, min_count, max_count in drop_list:
            count = random.randint(min_count, max_count)
            if count > 0:
                result.append((item, count))
        return result

    def draw(self):
        if self.dead and self.death_timer <= 0:
            return

        if mob_renderer.has_model(self.entity_type):
            glPushMatrix()
            glTranslatef(self.pos[0], self.pos[1], self.pos[2])
            
            if self.dead:
                progress = 1.0 - self.death_timer
                scale = max(0.01, 1.0 - progress)
                glScalef(scale, scale, scale)
                glRotatef(progress * 90, 1, 0, 0)
            
            mob_renderer.draw_mob(
                self.entity_type,
                (0, 0, 0),
                self.rotation,
                self.walk_cycle if hasattr(self, 'walk_cycle') else 0,
                self.hit_flash if hasattr(self, 'hit_flash') else 0
            )
            glPopMatrix()
            return
        
        colors = ENTITY_COLORS.get(self.entity_type)
        if not colors:
            return

        body_color = colors[0]
        accent_color = colors[1]

        glPushMatrix()
        glTranslatef(self.pos[0], self.pos[1], self.pos[2])
        glRotatef(self.rotation, 0, 1, 0)

        if self.hit_flash > 0 and int(self.hit_flash * 20) % 2 == 0:
            glColor3f(1, 0.3, 0.3)
        else:
            glColor3f(*body_color)

        h = self._get_height()

        if self.dead:
            progress = 1.0 - self.death_timer
            scale = max(0.01, 1.0 - progress)
            glScalef(scale, scale, scale)
            glRotatef(progress * 90, 1, 0, 0)

        if self.ai_state in ("wander", "chase", "flee"):
            bob = math.sin(self.walk_cycle) * 0.05
            glTranslatef(0, bob, 0)

        self._draw_body(h, body_color, accent_color)

        glPopMatrix()

    def _draw_body(self, h, body_color, accent_color):
        hw = 0.3
        
        if self.entity_type == ENTITY_COW:
            self._draw_cow(h, body_color, accent_color)
        elif self.entity_type == ENTITY_SHEEP:
            self._draw_sheep(h, body_color, accent_color)
        elif self.entity_type == ENTITY_CHICKEN:
            self._draw_chicken(h, body_color, accent_color)
        elif self.entity_type == ENTITY_ZOMBIE:
            self._draw_zombie(h, body_color, accent_color)
        elif self.entity_type == ENTITY_SKELETON:
            self._draw_skeleton(h, body_color, accent_color)
        else:
            self._draw_box(-hw, 0, -hw, hw, h, hw, body_color)

    def _draw_cow(self, h, body, accent):
        self._draw_box(-0.35, 0.3, -0.5, 0.35, 0.9, 0.5, body)
        self._draw_box(-0.2, 0.5, -0.7, 0.2, 0.9, -0.45, body)
        self._draw_box(-0.22, 0.9, -0.6, -0.15, 1.1, -0.55, accent)
        self._draw_box(0.15, 0.9, -0.6, 0.22, 1.1, -0.55, accent)
        for x in [-0.25, 0.25]:
            for z in [-0.35, 0.35]:
                self._draw_box(x-0.06, 0, z-0.06, x+0.06, 0.3, z+0.06, accent)

    def _draw_sheep(self, h, body, accent):
        self._draw_box(-0.35, 0.2, -0.45, 0.35, 0.8, 0.45, body)
        self._draw_box(-0.18, 0.35, -0.6, 0.18, 0.7, -0.4, accent)
        for x in [-0.2, 0.2]:
            for z in [-0.3, 0.3]:
                self._draw_box(x-0.05, 0, z-0.05, x+0.05, 0.2, z+0.05, accent)

    def _draw_chicken(self, h, body, accent):
        self._draw_box(-0.15, 0.15, -0.2, 0.15, 0.5, 0.2, body)
        self._draw_box(-0.1, 0.5, -0.25, 0.1, 0.7, -0.1, body)
        self._draw_box(-0.04, 0.55, -0.32, 0.04, 0.6, -0.25, accent)
        self._draw_box(-0.04, 0.7, -0.2, 0.04, 0.8, -0.15, accent)
        self._draw_box(-0.08, 0, -0.05, -0.02, 0.15, 0.05, accent)
        self._draw_box(0.02, 0, -0.05, 0.08, 0.15, 0.05, accent)

    def _draw_zombie(self, h, body, accent):
        self._draw_box(-0.2, 0.6, -0.15, 0.2, 1.3, 0.15, body)
        self._draw_box(-0.2, 1.3, -0.2, 0.2, 1.8, 0.2, accent)
        glColor3f(0.1, 0.4, 0.1)
        self._draw_box(-0.15, 1.5, -0.21, -0.05, 1.6, -0.2, (0.1, 0.4, 0.1))
        self._draw_box(0.05, 1.5, -0.21, 0.15, 1.6, -0.2, (0.1, 0.4, 0.1))
        arm_swing = math.sin(self.walk_cycle) * 20 if self.ai_state != "idle" else 0
        glPushMatrix()
        glTranslatef(-0.3, 1.1, 0)
        glRotatef(arm_swing + 80, 1, 0, 0)
        glTranslatef(0.1, -0.4, 0)
        self._draw_box(-0.06, 0, -0.06, 0.06, 0.5, 0.06, accent)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0.3, 1.1, 0)
        glRotatef(-arm_swing + 80, 1, 0, 0)
        glTranslatef(-0.1, -0.4, 0)
        self._draw_box(-0.06, 0, -0.06, 0.06, 0.5, 0.06, accent)
        glPopMatrix()
        leg_swing = math.sin(self.walk_cycle) * 15 if self.ai_state != "idle" else 0
        glPushMatrix()
        glTranslatef(-0.1, 0.6, 0)
        glRotatef(leg_swing, 1, 0, 0)
        glTranslatef(0, -0.3, 0)
        self._draw_box(-0.08, 0, -0.08, 0.08, 0.6, 0.08, accent)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0.1, 0.6, 0)
        glRotatef(-leg_swing, 1, 0, 0)
        glTranslatef(0, -0.3, 0)
        self._draw_box(-0.08, 0, -0.08, 0.08, 0.6, 0.08, accent)
        glPopMatrix()

    def _draw_skeleton(self, h, body, accent):
        self._draw_box(-0.15, 0.6, -0.1, 0.15, 1.3, 0.1, body)
        self._draw_box(-0.18, 1.3, -0.18, 0.18, 1.75, 0.18, body)
        self._draw_box(-0.12, 1.5, -0.19, -0.04, 1.6, -0.18, (0.1, 0.1, 0.1))
        self._draw_box(0.04, 1.5, -0.19, 0.12, 1.6, -0.18, (0.1, 0.1, 0.1))
        self._draw_box(-0.12, 1.3, -0.15, 0.12, 1.4, -0.18, accent)
        arm_swing = math.sin(self.walk_cycle) * 20 if self.ai_state != "idle" else 0
        glPushMatrix()
        glTranslatef(-0.2, 1.1, 0)
        glRotatef(arm_swing, 1, 0, 0)
        glTranslatef(0, -0.4, 0)
        self._draw_box(-0.03, 0, -0.03, 0.03, 0.5, 0.03, accent)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0.2, 1.1, 0)
        glRotatef(-arm_swing, 1, 0, 0)
        glTranslatef(0, -0.4, 0)
        self._draw_box(-0.03, 0, -0.03, 0.03, 0.5, 0.03, accent)
        glPopMatrix()
        leg_swing = math.sin(self.walk_cycle) * 15 if self.ai_state != "idle" else 0
        glPushMatrix()
        glTranslatef(-0.08, 0.6, 0)
        glRotatef(leg_swing, 1, 0, 0)
        glTranslatef(0, -0.3, 0)
        self._draw_box(-0.04, 0, -0.04, 0.04, 0.6, 0.04, accent)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0.08, 0.6, 0)
        glRotatef(-leg_swing, 1, 0, 0)
        glTranslatef(0, -0.3, 0)
        self._draw_box(-0.04, 0, -0.04, 0.04, 0.6, 0.04, accent)
        glPopMatrix()

    def _draw_box(self, x1, y1, z1, x2, y2, z2, color):
        glColor3f(*color)
        glBegin(GL_QUADS)
        glVertex3f(x1, y1, z1)
        glVertex3f(x2, y1, z1)
        glVertex3f(x2, y2, z1)
        glVertex3f(x1, y2, z1)
        glVertex3f(x2, y1, z2)
        glVertex3f(x1, y1, z2)
        glVertex3f(x1, y2, z2)
        glVertex3f(x2, y2, z2)
        glVertex3f(x1, y2, z1)
        glVertex3f(x2, y2, z1)
        glVertex3f(x2, y2, z2)
        glVertex3f(x1, y2, z2)
        glVertex3f(x1, y1, z2)
        glVertex3f(x2, y1, z2)
        glVertex3f(x2, y1, z1)
        glVertex3f(x1, y1, z1)
        glVertex3f(x2, y1, z1)
        glVertex3f(x2, y1, z2)
        glVertex3f(x2, y2, z2)
        glVertex3f(x2, y2, z1)
        glVertex3f(x1, y1, z2)
        glVertex3f(x1, y1, z1)
        glVertex3f(x1, y2, z1)
        glVertex3f(x1, y2, z2)
        glEnd()


class ItemDrop:
    def __init__(self, pos, item_type, count=1):
        self.pos = np.array(pos, dtype=np.float64)
        self.velocity = np.array([
            random.uniform(-2, 2),
            random.uniform(2, 5),
            random.uniform(-2, 2)
        ], dtype=np.float64)
        self.item_type = item_type
        self.count = count
        self.life = 60.0
        self.bob_cycle = random.uniform(0, math.pi * 2)
        self.on_ground = False
        self.pickup_delay = 0.5

    def update(self, dt, world):
        self.life -= dt
        if self.life <= 0:
            return False

        self.pickup_delay -= dt
        self.bob_cycle += dt * 3

        self.velocity[1] += GRAVITY * dt
        self.velocity[1] = max(self.velocity[1], -50)

        new_pos = self.pos + self.velocity * dt
        
        bx = int(math.floor(new_pos[0]))
        by = int(math.floor(new_pos[1]))
        bz = int(math.floor(new_pos[2]))
        
        block_below = world.get_block(bx, by, bz)
        if block_below in SOLID_BLOCKS:
            new_pos[1] = by + 1.0
            self.velocity[1] = 0
            self.on_ground = True
            self.velocity[0] *= 0.8
            self.velocity[2] *= 0.8
        
        self.pos = new_pos

        if self.pos[1] < -20:
            return False

        return True

    def can_pickup(self):
        return self.pickup_delay <= 0 and self.on_ground

    def draw(self):
        colors = ITEM_COLORS.get(self.item_type)
        if not colors:
            return

        glPushMatrix()
        
        bob = math.sin(self.bob_cycle) * 0.1
        glTranslatef(self.pos[0], self.pos[1] + 0.2 + bob, self.pos[2])
        
        glRotatef(self.bob_cycle * 50, 0, 1, 0)
        
        s = 0.15
        color = colors[1]
        glColor3f(*color)
        
        glBegin(GL_QUADS)
        glVertex3f(-s, -s, -s)
        glVertex3f(s, -s, -s)
        glVertex3f(s, s, -s)
        glVertex3f(-s, s, -s)
        glVertex3f(s, -s, s)
        glVertex3f(-s, -s, s)
        glVertex3f(-s, s, s)
        glVertex3f(s, s, s)
        glVertex3f(-s, s, -s)
        glVertex3f(s, s, -s)
        glVertex3f(s, s, s)
        glVertex3f(-s, s, s)
        glVertex3f(-s, -s, s)
        glVertex3f(s, -s, s)
        glVertex3f(s, -s, -s)
        glVertex3f(-s, -s, -s)
        glVertex3f(s, -s, -s)
        glVertex3f(s, -s, s)
        glVertex3f(s, s, s)
        glVertex3f(s, s, -s)
        glVertex3f(-s, -s, s)
        glVertex3f(-s, -s, -s)
        glVertex3f(-s, s, -s)
        glVertex3f(-s, s, s)
        glEnd()
        
        glPopMatrix()


class EntityManager:
    def __init__(self, world):
        self.world = world
        self.entities = []
        self.item_drops = []
        self.spawn_timer = 0
        self.max_entities = 30
        self.spawn_radius = 40
        self.despawn_radius = 60

    def update(self, dt, player_pos, day_time):
        alive = []
        damage_total = 0
        for entity in self.entities:
            if entity.update(dt, player_pos):
                alive.append(entity)
                
                if entity.hostile and entity.ai_state == "attack" and entity.attack_cooldown >= 0.95:
                    dist = np.linalg.norm(player_pos - entity.pos)
                    if dist <= entity.attack_range:
                        damage_total += entity.damage
            else:
                if entity.dead and entity.death_timer <= 0:
                    drops = entity.get_drops()
                    for item_type, count in drops:
                        drop = ItemDrop(entity.pos.copy(), item_type, count)
                        self.item_drops.append(drop)
        self.entities = alive

        alive_drops = []
        for drop in self.item_drops:
            if drop.update(dt, self.world):
                alive_drops.append(drop)
        self.item_drops = alive_drops

        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_timer = 2.0
            self._try_spawn(player_pos, day_time)

        self.entities = [e for e in self.entities 
                        if np.linalg.norm(e.pos - player_pos) < self.despawn_radius]

        return damage_total

    def _try_spawn(self, player_pos, day_time):
        if len(self.entities) >= self.max_entities:
            return

        angle = random.uniform(0, math.pi * 2)
        dist = random.uniform(15, self.spawn_radius)
        spawn_x = player_pos[0] + math.cos(angle) * dist
        spawn_z = player_pos[2] + math.sin(angle) * dist

        cx, cz = self.world.world_to_chunk(int(spawn_x), int(spawn_z))
        self.world.get_chunk(cx, cz)

        spawn_y = self.world.get_height(int(spawn_x), int(spawn_z))
        if spawn_y < 1:
            return

        spawn_pos = [spawn_x + 0.5, float(spawn_y + 1), spawn_z + 0.5]

        brightness = max(0.0, math.sin(day_time * 2 * math.pi))
        
        if brightness > 0.3:
            mob_type = random.choice([ENTITY_COW, ENTITY_SHEEP, ENTITY_CHICKEN])
        else:
            mob_type = random.choice([ENTITY_ZOMBIE, ENTITY_SKELETON])

        entity = Entity(mob_type, spawn_pos, self.world)
        self.entities.append(entity)

    def attack_entity(self, player_pos, player_forward, damage):
        best_dist = 4.0
        best_entity = None
        
        for entity in self.entities:
            if entity.dead:
                continue
            to_entity = entity.pos - player_pos
            to_entity[1] = 0
            dist = np.linalg.norm(to_entity)
            if dist > 4.0:
                continue
            forward_2d = player_forward.copy()
            forward_2d[1] = 0
            forward_2d /= np.linalg.norm(forward_2d)
            to_entity_norm = to_entity / dist
            dot = np.dot(forward_2d, to_entity_norm)
            if dot > 0.5 and dist < best_dist:
                best_dist = dist
                best_entity = entity

        if best_entity:
            best_entity.take_damage(damage)
            knockback = best_entity.pos - player_pos
            knockback[1] = 0
            n = np.linalg.norm(knockback)
            if n > 0:
                knockback /= n
            best_entity.velocity[0] += knockback[0] * 5
            best_entity.velocity[1] += 3
            best_entity.velocity[2] += knockback[2] * 5
            return True
        return False

    def draw(self):
        for entity in self.entities:
            entity.draw()
        for drop in self.item_drops:
            drop.draw()

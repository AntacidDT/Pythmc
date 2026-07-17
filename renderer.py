"""Pythmc - Renderer, HUD, and Visual Effects - V2.6"""

import math
import random
from OpenGL.GL import *
from text_renderer import text_renderer
from textures import texture_manager
from OpenGL.GLU import *
from constants import *


def get_character_colors():
    """Load character body part colors from settings."""
    from settings_manager import settings_manager
    def _c(rk, gk, bk):
        return (settings_manager.get("appearance", rk) / 255.0,
                settings_manager.get("appearance", gk) / 255.0,
                settings_manager.get("appearance", bk) / 255.0)
    return {
        "skin": _c("skin_r", "skin_g", "skin_b"),
        "shirt": _c("shirt_r", "shirt_g", "shirt_b"),
        "pants": _c("pants_r", "pants_g", "pants_b"),
        "eyes": _c("eyes_r", "eyes_g", "eyes_b"),
    }


def reset_gl_state():
    """Reset GL state to known defaults. Call after errors."""
    glDisable(GL_BLEND)
    glDisable(GL_LIGHTING)
    glDisable(GL_FOG)
    glDisable(GL_DEPTH_TEST)
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    glPopMatrix() if _gl_stack_depth() > 0 else None


def _gl_stack_depth():
    try:
        return len(glGetInteger(GL_MODELVIEW_MATRIX))
    except Exception:
        return 0


class Particle:
    __slots__ = ('pos','vel','color','life','max_life')
    def __init__(self, pos, vel, color, life=1.0):
        self.pos = list(pos)
        self.vel = list(vel)
        self.color = color
        self.life = life
        self.max_life = life

class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit(self, pos, block_type, count=12):
        colors = BLOCK_COLORS.get(block_type)
        if not colors: return
        for _ in range(count):
            vel = [random.uniform(-3,3), random.uniform(1,6), random.uniform(-3,3)]
            c = colors[1]
            shade = random.uniform(0.7, 1.0)
            color = (c[0]*shade, c[1]*shade, c[2]*shade)
            p = Particle(
                [pos[0]+random.uniform(0,1), pos[1]+random.uniform(0,1), pos[2]+random.uniform(0,1)],
                vel, color, random.uniform(0.3, 0.8)
            )
            self.particles.append(p)

    def emit_hit(self, pos, count=8):
        for _ in range(count):
            vel = [random.uniform(-2,2), random.uniform(1,4), random.uniform(-2,2)]
            color = (1.0, random.uniform(0.8, 1.0), random.uniform(0.8, 1.0))
            p = Particle(pos, vel, color, random.uniform(0.2, 0.4))
            self.particles.append(p)

    def update(self, dt):
        from cuda_manager import gpu_update_particles
        self.particles = gpu_update_particles(self.particles, dt)

    def draw(self):
        if not self.particles: return
        glDisable(GL_LIGHTING)
        glDisable(GL_FOG)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glPointSize(4)
        glBegin(GL_POINTS)
        for p in self.particles:
            alpha = p.life / p.max_life
            glColor4f(p.color[0], p.color[1], p.color[2], alpha)
            glVertex3f(p.pos[0], p.pos[1], p.pos[2])
        glEnd()
        glDisable(GL_BLEND)
        glEnable(GL_FOG)
        glEnable(GL_LIGHTING)


class CloudRenderer:
    def __init__(self, seed):
        self.cloud_map = {}
        self.seed = seed

    def get_cloud(self, cx, cz):
        key = (cx, cz)
        if key not in self.cloud_map:
            rng = random.Random(self.seed + cx * 31 + cz * 37)
            self.cloud_map[key] = rng.random() < 0.35
        return self.cloud_map[key]

    def draw(self, player_pos, time_val):
        glDisable(GL_LIGHTING)
        glDisable(GL_FOG)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        cloud_y = 55.0
        px = int(math.floor(player_pos[0] / 12))
        pz = int(math.floor(player_pos[2] / 12))
        offset_x = (time_val * 2.0) % 12.0
        glColor4f(1.0, 1.0, 1.0, 0.65)
        glBegin(GL_QUADS)
        for dx in range(-15, 16):
            for dz in range(-15, 16):
                if self.get_cloud(px + dx, pz + dz):
                    bx = (px + dx) * 12 - offset_x
                    bz = (pz + dz) * 12
                    glVertex3f(bx, cloud_y, bz)
                    glVertex3f(bx + 10, cloud_y, bz)
                    glVertex3f(bx + 10, cloud_y, bz + 10)
                    glVertex3f(bx, cloud_y, bz + 10)
        glEnd()
        glDisable(GL_BLEND)
        glEnable(GL_FOG)
        glEnable(GL_LIGHTING)


class HUD:
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h

    def draw(self, player, stats=None):
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glDisable(GL_FOG)
        glDisable(GL_BLEND)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.screen_w, 0, self.screen_h, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        cx, cy = self.screen_w // 2, self.screen_h // 2

        # Crosshair
        glColor3f(1, 1, 1)
        glLineWidth(2)
        glBegin(GL_LINES)
        glVertex2f(cx - 12, cy); glVertex2f(cx + 12, cy)
        glVertex2f(cx, cy - 12); glVertex2f(cx, cy + 12)
        glEnd()

        # Hotbar
        bar_w = 9 * 44
        sx = (self.screen_w - bar_w) // 2
        sy = 10
        for i in range(9):
            bx = sx + i * 45
            if i == player.selected_slot:
                glColor3f(1, 1, 1)
                glLineWidth(3)
            else:
                glColor3f(0.35, 0.35, 0.35)
                glLineWidth(1)
            glBegin(GL_LINE_LOOP)
            glVertex2f(bx, sy); glVertex2f(bx + 40, sy)
            glVertex2f(bx + 40, sy + 40); glVertex2f(bx, sy + 40)
            glEnd()
            slot = player.inventory.hotbar[i]
            if not slot.is_empty() and slot.item in ITEM_COLORS:
                c = ITEM_COLORS[slot.item][1]
                glColor3f(c[0], c[1], c[2])
                glBegin(GL_QUADS)
                glVertex2f(bx + 3, sy + 3); glVertex2f(bx + 37, sy + 3)
                glVertex2f(bx + 37, sy + 37); glVertex2f(bx + 3, sy + 37)
                glEnd()
                if slot.count > 1:
                    text_renderer.draw_text(bx + 24, sy + 4, str(slot.count), size="medium", color=(1.0, 1.0, 1.0))

        # Survival HUD (health, armor, hunger) - above hotbar
        if not player.creative:
            armor = player.get_armor_defense()
            self._draw_health_bar(sx, sy + 60, player)
            if armor > 0:
                self._draw_armor_bar(sx, sy + 76, armor)
            self._draw_hunger_bar(sx + 200, sy + 60, player)

        # Selected item name - above survival HUD
        selected_slot = player.inventory.hotbar[player.selected_slot]
        if not selected_slot.is_empty():
            name = ITEM_NAMES.get(selected_slot.item, "")
            name_y = sy + 95 if not player.creative else sy + 45
            text_renderer.draw_text(sx, name_y, name, size="medium", color=(1.0, 1.0, 1.0))

        # V2.0: Stats display (top right)
        if stats:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            sx_r = self.screen_w - 10
            text_renderer.draw_text(sx_r - 120, self.screen_h - 20, f"Day: {stats.get('days', 0)}", "small", (0.7, 0.7, 0.75))
            text_renderer.draw_text(sx_r - 120, self.screen_h - 36, f"Dug: {stats.get('dug', 0)}", "small", (0.7, 0.7, 0.75))
            text_renderer.draw_text(sx_r - 120, self.screen_h - 52, f"Placed: {stats.get('placed', 0)}", "small", (0.7, 0.7, 0.75))
            glDisable(GL_BLEND)

        # Eating animation
        if player.eating:
            self._draw_eating_overlay(cx, cy, player)

        # Hurt overlay
        if player.hurt_timer > 0:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glColor4f(0.8, 0, 0, player.hurt_timer * 0.5)
            glBegin(GL_QUADS)
            glVertex2f(0, 0); glVertex2f(self.screen_w, 0)
            glVertex2f(self.screen_w, self.screen_h); glVertex2f(0, self.screen_h)
            glEnd()
            glDisable(GL_BLEND)

        # Death screen
        if player.dead:
            self._draw_death_screen(cx, cy, player)

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_FOG)

    def _draw_health_bar(self, x, y, player):
        for i in range(10):
            if player.health >= (i + 1) * 2:
                glColor3f(0.85, 0.1, 0.1)
            elif player.health >= i * 2 + 1:
                glColor3f(0.85, 0.35, 0.3)
            else:
                glColor3f(0.25, 0.25, 0.25)
            glBegin(GL_QUADS)
            glVertex2f(x + i * 18, y); glVertex2f(x + i * 18 + 14, y)
            glVertex2f(x + i * 18 + 14, y + 14); glVertex2f(x + i * 18, y + 14)
            glEnd()

    def _draw_armor_bar(self, x, y, armor_points):
        """Draw armor icons (shield shapes)."""
        num_shields = min(10, armor_points)
        for i in range(num_shields):
            bx = x + i * 18
            # Shield shape
            glColor3f(0.7, 0.7, 0.7)
            glBegin(GL_QUADS)
            glVertex2f(bx, y + 14)
            glVertex2f(bx + 14, y + 14)
            glVertex2f(bx + 14, y + 4)
            glVertex2f(bx, y + 4)
            glEnd()
            # Shield bottom point
            glBegin(GL_TRIANGLES)
            glVertex2f(bx, y + 4)
            glVertex2f(bx + 14, y + 4)
            glVertex2f(bx + 7, y)
            glEnd()

    def _draw_hunger_bar(self, x, y, player):
        for i in range(10):
            if player.hunger >= (i + 1) * 2:
                glColor3f(0.75, 0.55, 0.15)
            elif player.hunger >= i * 2 + 1:
                glColor3f(0.65, 0.5, 0.2)
            else:
                glColor3f(0.25, 0.25, 0.25)
            glBegin(GL_QUADS)
            glVertex2f(x + i * 18, y); glVertex2f(x + i * 18 + 14, y)
            glVertex2f(x + i * 18 + 14, y + 14); glVertex2f(x + i * 18, y + 14)
            glEnd()

    def _draw_eating_overlay(self, cx, cy, player):
        """Show eating progress bar."""
        if player.eat_item and player.eat_item in FOOD_PROPERTIES:
            name = ITEM_NAMES.get(player.eat_item, "Food")
            progress = min(1.0, player.eat_timer / player.eat_duration)
            
            bar_w = 150
            bar_x = cx - bar_w // 2
            bar_y = cy - 80
            
            # Background
            glColor4f(0, 0, 0, 0.6)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glBegin(GL_QUADS)
            glVertex2f(bar_x - 10, bar_y - 20)
            glVertex2f(bar_x + bar_w + 10, bar_y - 20)
            glVertex2f(bar_x + bar_w + 10, bar_y + 12)
            glVertex2f(bar_x - 10, bar_y + 12)
            glEnd()
            glDisable(GL_BLEND)
            
            # Progress bar
            glColor3f(0.2, 0.7, 0.2)
            glBegin(GL_QUADS)
            glVertex2f(bar_x, bar_y)
            glVertex2f(bar_x + bar_w * progress, bar_y)
            glVertex2f(bar_x + bar_w * progress, bar_y + 8)
            glVertex2f(bar_x, bar_y + 8)
            glEnd()
            
            # Label
            glColor3f(1, 1, 1)
            text_renderer.draw_text_centered(cx, bar_y + 15, f"Eating {name}", size="medium", color=(1.0, 1.0, 1.0))

    def _draw_death_screen(self, cx, cy, player):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(0.5, 0.0, 0.0, 0.4)
        glBegin(GL_QUADS)
        glVertex2f(0, 0); glVertex2f(self.screen_w, 0)
        glVertex2f(self.screen_w, self.screen_h); glVertex2f(0, self.screen_h)
        glEnd()

        text_renderer.draw_text_centered_shadow(cx, cy + 10, "YOU DIED", size="title",
                                                color=(0.9, 0.1, 0.1),
                                                shadow=(0.3, 0.0, 0.0))

        bar_w = 200
        bar_x = cx - bar_w // 2
        bar_y = cy - 40
        glColor3f(0.2, 0.2, 0.2)
        glBegin(GL_QUADS)
        glVertex2f(bar_x, bar_y); glVertex2f(bar_x + bar_w, bar_y)
        glVertex2f(bar_x + bar_w, bar_y + 12); glVertex2f(bar_x, bar_y + 12)
        glEnd()

        progress = 1.0 - (max(0, player.respawn_timer) / 3.0)
        glColor3f(0.2, 0.8, 0.2)
        glBegin(GL_QUADS)
        glVertex2f(bar_x, bar_y); glVertex2f(bar_x + bar_w * progress, bar_y)
        glVertex2f(bar_x + bar_w * progress, bar_y + 12); glVertex2f(bar_x, bar_y + 12)
        glEnd()

        if player.respawn_timer > 0:
            text_renderer.draw_text_centered(cx, bar_y - 20, f"RESPAWNING IN {player.respawn_timer:.1F}...", size="medium",
                                            color=(0.7, 0.7, 0.7))
        text_renderer.draw_text_centered(cx, bar_y - 38, "PRESS R TO RESPAWN", size="medium",
                                        color=(0.6, 0.6, 0.6))

        glDisable(GL_BLEND)


def draw_player_body(x, y, z, yaw, pitch, arm_swing, walk_cycle, armor_slots=None, is_sneaking=False, colors=None, first_person=False, held_item=None):
    """Draw player body with head, body, arms, legs and armor overlay.
    If first_person=True, head/eyes are hidden (camera IS the head) and
    a held_item cube is drawn at the right hand tip."""
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(yaw, 0, 1, 0)
    
    # Body dimensions
    head_w, head_h = 0.5, 0.5
    body_w, body_h, body_d = 0.5, 0.75, 0.25
    arm_w, arm_h = 0.25, 0.75
    leg_w, leg_h = 0.25, 0.75
    
    # Skin colors (from settings or defaults)
    if colors:
        skin = colors.get("skin", (0.90, 0.75, 0.60))
        shirt = colors.get("shirt", (0.20, 0.50, 0.80))
        pants = colors.get("pants", (0.30, 0.30, 0.60))
        eye_color = colors.get("eyes", (0.1, 0.3, 0.6))
    else:
        skin = (0.90, 0.75, 0.60)
        shirt = (0.20, 0.50, 0.80)
        pants = (0.30, 0.30, 0.60)
        eye_color = (0.1, 0.3, 0.6)
    
    def _draw_cube(x1, y1, z1, x2, y2, z2, color):
        glColor3f(*color)
        glBegin(GL_QUADS)
        # Front
        glVertex3f(x1, y1, z1)
        glVertex3f(x2, y1, z1)
        glVertex3f(x2, y2, z1)
        glVertex3f(x1, y2, z1)
        # Back
        glVertex3f(x2, y1, z2)
        glVertex3f(x1, y1, z2)
        glVertex3f(x1, y2, z2)
        glVertex3f(x2, y2, z2)
        # Top
        glVertex3f(x1, y2, z1)
        glVertex3f(x2, y2, z1)
        glVertex3f(x2, y2, z2)
        glVertex3f(x1, y2, z2)
        # Bottom
        glVertex3f(x1, y1, z2)
        glVertex3f(x2, y1, z2)
        glVertex3f(x2, y1, z1)
        glVertex3f(x1, y1, z1)
        # Right
        glVertex3f(x2, y1, z1)
        glVertex3f(x2, y1, z2)
        glVertex3f(x2, y2, z2)
        glVertex3f(x2, y2, z1)
        # Left
        glVertex3f(x1, y1, z2)
        glVertex3f(x1, y1, z1)
        glVertex3f(x1, y2, z1)
        glVertex3f(x1, y2, z2)
        glEnd()
    
    def _draw_armor_overlay(x1, y1, z1, x2, y2, z2, armor_type):
        if not armor_slots or armor_type not in armor_slots:
            return
        item_id = armor_slots[armor_type]
        if not item_id or item_id not in ARMOR_COLORS:
            return
        color = ARMOR_COLORS[item_id]
        s = 1.06
        cx, cy, cz = (x1+x2)/2, (y1+y2)/2, (z1+z2)/2
        w2, h2, d2 = (x2-x1)*s/2, (y2-y1)*s/2, (z2-z1)*s/2
        _draw_cube(cx-w2, cy-h2, cz-d2, cx+w2, cy+h2, cz+d2, color)
    
    # Sneak offset: lower entire body slightly
    sneak_y = -0.2 if is_sneaking else 0.0
    
    head_y = 1.62 + sneak_y
    body_y = 0.87 + sneak_y
    arm_y = 1.12 + sneak_y
    leg_y = 0.0
    
    # Left leg
    glPushMatrix()
    leg_swing = math.sin(walk_cycle) * 30 if walk_cycle else 0
    glTranslatef(-0.125, leg_y + leg_h, 0)
    glRotatef(leg_swing, 1, 0, 0)
    glTranslatef(0, -leg_h, 0)
    _draw_cube(-leg_w/2, 0, -leg_w/2, leg_w/2, leg_h, leg_w/2, pants)
    _draw_armor_overlay(-leg_w/2, 0, -leg_w/2, leg_w/2, leg_h, leg_w/2, 2)
    glPopMatrix()
    
    # Right leg
    glPushMatrix()
    glTranslatef(0.125, leg_y + leg_h, 0)
    glRotatef(-leg_swing, 1, 0, 0)
    glTranslatef(0, -leg_h, 0)
    _draw_cube(-leg_w/2, 0, -leg_w/2, leg_w/2, leg_h, leg_w/2, pants)
    _draw_armor_overlay(-leg_w/2, 0, -leg_w/2, leg_w/2, leg_h, leg_w/2, 2)
    glPopMatrix()
    
    # Body
    _draw_cube(-body_w/2, body_y, -body_d/2, body_w/2, body_y + body_h, body_d/2, shirt)
    _draw_armor_overlay(-body_w/2, body_y, -body_d/2, body_w/2, body_y + body_h, body_d/2, 1)
    
    # Left arm
    glPushMatrix()
    glTranslatef(-body_w/2 - arm_w/2, arm_y + arm_h, 0)
    glRotatef(arm_swing, 1, 0, 0)
    glTranslatef(0, -arm_h, 0)
    _draw_cube(-arm_w/2, 0, -arm_w/2, arm_w/2, arm_h, arm_w/2, skin)
    glPopMatrix()
    
    # Right arm (with held item in first-person)
    glPushMatrix()
    glTranslatef(body_w/2 + arm_w/2, arm_y + arm_h, 0)
    glRotatef(-arm_swing, 1, 0, 0)
    glTranslatef(0, -arm_h, 0)
    _draw_cube(-arm_w/2, 0, -arm_w/2, arm_w/2, arm_h, arm_w/2, skin)
    
    # In first-person, draw held block on the hand
    if first_person and held_item and held_item in ITEM_COLORS:
        c = ITEM_COLORS[held_item][1]
        bs = 0.3
        bx = -bs / 2
        by = arm_h + 0.05
        bz = -bs / 2
        _draw_cube(bx, by, bz, bx + bs, by + bs, bz + bs, c)
    
    glPopMatrix()
    
    # Head and eyes (skip in first-person — camera IS the head)
    if not first_person:
        head_y_pos = head_y
        _draw_cube(-head_w/2, head_y_pos, -head_w/2, head_w/2, head_y_pos + head_h, head_w/2, skin)
        _draw_armor_overlay(-head_w/2, head_y_pos, -head_w/2, head_w/2, head_y_pos + head_h, head_w/2, 0)
        
        # Eyes
        eye_y = head_y_pos + head_h * 0.55
        eye_z = -head_w/2 - 0.001
        glColor3f(1, 1, 1)
        glBegin(GL_QUADS)
        glVertex3f(-0.15, eye_y, eye_z)
        glVertex3f(-0.05, eye_y, eye_z)
        glVertex3f(-0.05, eye_y + 0.08, eye_z)
        glVertex3f(-0.15, eye_y + 0.08, eye_z)
        glVertex3f(0.05, eye_y, eye_z)
        glVertex3f(0.15, eye_y, eye_z)
        glVertex3f(0.15, eye_y + 0.08, eye_z)
        glVertex3f(0.05, eye_y + 0.08, eye_z)
        glEnd()
        
        # Pupils
        glColor3f(*eye_color)
        pupil_z = eye_z - 0.001
        glBegin(GL_QUADS)
        glVertex3f(-0.13, eye_y + 0.01, pupil_z)
        glVertex3f(-0.07, eye_y + 0.01, pupil_z)
        glVertex3f(-0.07, eye_y + 0.06, pupil_z)
        glVertex3f(-0.13, eye_y + 0.06, pupil_z)
        glVertex3f(0.07, eye_y + 0.01, pupil_z)
        glVertex3f(0.13, eye_y + 0.01, pupil_z)
        glVertex3f(0.13, eye_y + 0.06, pupil_z)
        glVertex3f(0.07, eye_y + 0.06, pupil_z)
        glEnd()
    
    glPopMatrix()


def draw_first_person_hand(player, screen_w, screen_h):
    """Draw the player's blocky Minecraft-style arm and held item in first-person."""
    glDisable(GL_LIGHTING)
    glDisable(GL_FOG)
    glDisable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, screen_w, 0, screen_h, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    colors = get_character_colors()
    skin = colors.get("skin", (0.90, 0.75, 0.60))
    shirt = colors.get("shirt", (0.20, 0.40, 0.70))

    # Swing angle from arm_swing (0-45 when attacking, oscillates when walking)
    swing = getattr(player, 'arm_swing', 0)

    # Walk bob
    bob = 0
    if player.on_ground and not player.flying:
        speed = abs(player.velocity[0]) + abs(player.velocity[2])
        if speed > 0.5:
            bob = math.sin(player.walk_cycle * 2) * 8
    elif player.in_water:
        bob = math.sin(player.walk_cycle * 1.5) * 5

    # Eat animation — lift arm up
    eat_lift = 0
    if player.eating:
        eat_progress = min(1.0, player.eat_timer / player.eat_duration)
        eat_lift = math.sin(eat_progress * math.pi) * 80

    # Position (bottom-right of screen, like Minecraft)
    base_x = screen_w - 85
    base_y = -30 + bob * 0.5 + eat_lift

    # Swing offset — arm swings forward (up on screen) when attacking
    swing_y = swing * 0.8
    swing_x = -swing * 0.3

    arm_x = base_x + swing_x
    arm_y = base_y + swing_y

    # ── Arm dimensions ──
    arm_w = 22    # width
    upper_h = 55  # upper arm (with sleeve)
    hand_h = 35   # hand (skin)

    # ── Upper arm (shirt sleeve) — front face ──
    glColor4f(shirt[0] * 0.85, shirt[1] * 0.85, shirt[2] * 0.85, 0.98)
    glBegin(GL_QUADS)
    glVertex2f(arm_x, arm_y)
    glVertex2f(arm_x + arm_w, arm_y)
    glVertex2f(arm_x + arm_w, arm_y + upper_h)
    glVertex2f(arm_x, arm_y + upper_h)
    glEnd()

    # ── Upper arm — right side (darker) ──
    side_w = 6
    glColor4f(shirt[0] * 0.6, shirt[1] * 0.6, shirt[2] * 0.6, 0.98)
    glBegin(GL_QUADS)
    glVertex2f(arm_x + arm_w, arm_y)
    glVertex2f(arm_x + arm_w + side_w, arm_y + 3)
    glVertex2f(arm_x + arm_w + side_w, arm_y + upper_h + 3)
    glVertex2f(arm_x + arm_w, arm_y + upper_h)
    glEnd()

    # ── Upper arm — top face (lighter) ──
    glColor4f(shirt[0] * 1.1, shirt[1] * 1.1, shirt[2] * 1.1, 0.98)
    glBegin(GL_QUADS)
    glVertex2f(arm_x - 2, arm_y + upper_h)
    glVertex2f(arm_x + arm_w - 2, arm_y + upper_h)
    glVertex2f(arm_x + arm_w + side_w - 2, arm_y + upper_h + 3)
    glVertex2f(arm_x - 2 + side_w, arm_y + upper_h + 3)
    glEnd()

    # ── Hand (skin) — front face ──
    hx = arm_x + 1
    hw = arm_w - 2
    hy = arm_y + upper_h
    glColor4f(skin[0], skin[1], skin[2], 0.98)
    glBegin(GL_QUADS)
    glVertex2f(hx, hy)
    glVertex2f(hx + hw, hy)
    glVertex2f(hx + hw, hy + hand_h)
    glVertex2f(hx, hy + hand_h)
    glEnd()

    # ── Hand — right side (darker) ──
    glColor4f(skin[0] * 0.78, skin[1] * 0.78, skin[2] * 0.78, 0.98)
    glBegin(GL_QUADS)
    glVertex2f(hx + hw, hy)
    glVertex2f(hx + hw + side_w - 1, hy + 3)
    glVertex2f(hx + hw + side_w - 1, hy + hand_h + 3)
    glVertex2f(hx + hw, hy + hand_h)
    glEnd()

    # ── Hand — top face (lighter) ──
    glColor4f(skin[0] * 1.05, skin[1] * 1.05, skin[2] * 1.05, 0.98)
    glBegin(GL_QUADS)
    glVertex2f(hx - 1, hy + hand_h)
    glVertex2f(hx + hw - 1, hy + hand_h)
    glVertex2f(hx + hw + side_w - 2, hy + hand_h + 3)
    glVertex2f(hx - 1 + side_w, hy + hand_h + 3)
    glEnd()

    # ── Held block/item on top of hand ──
    held_item = player.hotbar[player.selected_slot]
    if held_item and held_item in ITEM_COLORS:
        c = ITEM_COLORS[held_item][1]
        bx = hx + 2
        by = hy + hand_h + 4
        bs = 20

        # Front face
        glColor4f(c[0] * 0.8, c[1] * 0.8, c[2] * 0.8, 0.98)
        glBegin(GL_QUADS)
        glVertex2f(bx, by)
        glVertex2f(bx + bs, by)
        glVertex2f(bx + bs, by + bs)
        glVertex2f(bx, by + bs)
        glEnd()
        # Top face (lighter)
        glColor4f(c[0] * 1.1, c[1] * 1.1, c[2] * 1.1, 0.98)
        glBegin(GL_QUADS)
        glVertex2f(bx - 3, by + bs)
        glVertex2f(bx + bs - 3, by + bs)
        glVertex2f(bx + bs + side_w - 5, by + bs + 5)
        glVertex2f(bx - 3 + side_w, by + bs + 5)
        glEnd()
        # Right face (darker)
        glColor4f(c[0] * 0.55, c[1] * 0.55, c[2] * 0.55, 0.98)
        glBegin(GL_QUADS)
        glVertex2f(bx + bs, by)
        glVertex2f(bx + bs + side_w - 2, by + 3)
        glVertex2f(bx + bs + side_w - 2, by + bs + 5)
        glVertex2f(bx + bs, by + bs)
        glEnd()

    glDisable(GL_BLEND)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_DEPTH_TEST)


def draw_target_block(hit, face_verts):
    if not hit: return
    x, y, z = hit
    glDisable(GL_LIGHTING)
    glDisable(GL_FOG)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glLineWidth(2)
    glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
    glColor4f(0, 0, 0, 0.5)
    for fi in range(6):
        glBegin(GL_QUADS)
        for vx, vy, vz in face_verts[fi]:
            glVertex3f(x + vx, y + vy, z + vz)
        glEnd()
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    glColor4f(1, 1, 1, 0.08)
    for fi in range(6):
        glBegin(GL_QUADS)
        for vx, vy, vz in face_verts[fi]:
            glVertex3f(x + vx, y + vy, z + vz)
        glEnd()
    glDisable(GL_BLEND)
    glEnable(GL_FOG)
    glEnable(GL_LIGHTING)


def update_sky(day_time):
    sun_angle = day_time * 2 * math.pi
    brightness = max(0.0, math.sin(sun_angle))
    
    if brightness > 0.3:
        r = 0.4 + 0.2 * brightness
        g = 0.55 + 0.2 * brightness
        b = 0.8 + 0.15 * brightness
    elif brightness > 0.0:
        t = brightness / 0.3
        r = 0.3 + 0.4 * t
        g = 0.2 + 0.35 * t
        b = 0.3 + 0.5 * t
    else:
        r = 0.02
        g = 0.02
        b = 0.08
    
    glClearColor(r, g, b, 1.0)
    glFogfv(GL_FOG_COLOR, (r, g, b, 1.0))
    
    ambient = 0.15 + 0.25 * brightness
    diffuse = 0.3 + 0.7 * brightness
    
    if 0.0 < brightness < 0.4:
        diffuse_r = diffuse * 1.2
        diffuse_g = diffuse * 0.9
        diffuse_b = diffuse * 0.7
    else:
        diffuse_r = diffuse
        diffuse_g = diffuse * 0.95
        diffuse_b = diffuse * 0.85
    
    glLightfv(GL_LIGHT0, GL_AMBIENT, (ambient, ambient, ambient + 0.05, 1.0))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (diffuse_r, diffuse_g, diffuse_b, 1.0))
    glLightfv(GL_LIGHT0, GL_POSITION, (math.cos(sun_angle), math.sin(sun_angle), 0.3, 0.0))
    
    _draw_celestial(sun_angle, brightness)
    
    return brightness


def _draw_celestial(sun_angle, brightness):
    glDisable(GL_LIGHTING)
    glDisable(GL_FOG)
    glDisable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    if brightness > 0.0:
        sun_x = math.cos(sun_angle) * 400
        sun_y = math.sin(sun_angle) * 400
        sun_z = -100
        
        glColor4f(1.0, 0.95, 0.8, brightness)
        glPointSize(30)
        glBegin(GL_POINTS)
        glVertex3f(sun_x, sun_y, sun_z)
        glEnd()
        
        glColor4f(1.0, 0.9, 0.7, brightness * 0.3)
        glPointSize(60)
        glBegin(GL_POINTS)
        glVertex3f(sun_x, sun_y, sun_z)
        glEnd()
    
    if brightness < 0.5:
        moon_brightness = max(0, 0.5 - brightness) * 2
        moon_angle = sun_angle + math.pi
        moon_x = math.cos(moon_angle) * 400
        moon_y = math.sin(moon_angle) * 400
        moon_z = -100
        
        glColor4f(0.9, 0.9, 1.0, moon_brightness * 0.8)
        glPointSize(20)
        glBegin(GL_POINTS)
        glVertex3f(moon_x, moon_y, moon_z)
        glEnd()
    
    glDisable(GL_BLEND)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_FOG)
    glEnable(GL_LIGHTING)


def draw_falling_blocks(falling_blocks):
    """Draw falling block entities (explosion debris)."""
    if not falling_blocks:
        return
    glDisable(GL_LIGHTING)
    glDisable(GL_FOG)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    texture_manager.bind()

    for fb in falling_blocks:
        bx, by, bz = fb.pos[0], fb.pos[1], fb.pos[2]
        hs = 0.45
        colors = BLOCK_COLORS.get(fb.block_type, ((0.6, 0.6, 0.6), (0.5, 0.5, 0.5), (0.4, 0.4, 0.4)))
        c = colors[0]

        glPushMatrix()
        glTranslatef(bx, by, bz)
        glRotatef(fb.rotation, 1, 0.5, 0.3)
        glColor4f(c[0], c[1], c[2], fb.alpha)

        glBegin(GL_QUADS)
        glVertex3f(-hs, -hs, hs)
        glVertex3f(hs, -hs, hs)
        glVertex3f(hs, hs, hs)
        glVertex3f(-hs, hs, hs)
        glVertex3f(hs, -hs, -hs)
        glVertex3f(-hs, -hs, -hs)
        glVertex3f(-hs, hs, -hs)
        glVertex3f(hs, hs, -hs)
        glVertex3f(-hs, hs, hs)
        glVertex3f(hs, hs, hs)
        glVertex3f(hs, hs, -hs)
        glVertex3f(-hs, hs, -hs)
        glVertex3f(-hs, -hs, -hs)
        glVertex3f(hs, -hs, -hs)
        glVertex3f(hs, -hs, hs)
        glVertex3f(-hs, -hs, hs)
        glVertex3f(hs, -hs, hs)
        glVertex3f(hs, -hs, -hs)
        glVertex3f(hs, hs, -hs)
        glVertex3f(hs, hs, hs)
        glVertex3f(-hs, -hs, -hs)
        glVertex3f(-hs, -hs, hs)
        glVertex3f(-hs, hs, hs)
        glVertex3f(-hs, hs, -hs)
        glEnd()
        glPopMatrix()

    texture_manager.unbind()
    glDisable(GL_BLEND)
    glEnable(GL_FOG)
    glEnable(GL_LIGHTING)


def init_gl():
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LEQUAL)
    glDisable(GL_CULL_FACE)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glShadeModel(GL_SMOOTH)
    glClearColor(0.5, 0.7, 1.0, 1.0)
    glLightfv(GL_LIGHT0, GL_AMBIENT, (0.3, 0.3, 0.35, 1.0))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 0.95, 0.85, 1.0))
    glLightfv(GL_LIGHT0, GL_POSITION, (0.5, 1.0, 0.3, 0.0))
    glEnable(GL_FOG)
    glFogi(GL_FOG_MODE, GL_LINEAR)
    glFogfv(GL_FOG_COLOR, (0.5, 0.7, 1.0, 1.0))
    glFogf(GL_FOG_START, CHUNK_SIZE * (RENDER_DISTANCE - 1))
    glFogf(GL_FOG_END, CHUNK_SIZE * RENDER_DISTANCE)

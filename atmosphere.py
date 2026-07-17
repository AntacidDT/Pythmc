"""Pythmc - Atmosphere and Visual Effects System

Features:
- Exponential fog with height variation
- Ambient particles (dust, fireflies, pollen)
- Weather system (rain, thunder)
- Better sky gradient with stars
- Torch glow effects
- Water reflections
"""

import math
import random
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from constants import *


class AtmosphereParticle:
    """Single atmospheric particle."""
    __slots__ = ('pos', 'vel', 'color', 'life', 'max_life', 'size', 'type')
    
    def __init__(self, pos, vel, color, life, size, ptype):
        self.pos = list(pos)
        self.vel = list(vel)
        self.color = color
        self.life = life
        self.max_life = life
        self.size = size
        self.type = ptype


class WeatherSystem:
    """Handles rain, thunder, and weather transitions."""
    
    def __init__(self):
        self.weather = "clear"  # clear, rain, thunder
        self.target_weather = "clear"
        self.transition = 0.0
        self.rain_intensity = 0.0
        self.thunder_timer = 0.0
        self.lightning_flash = 0.0
        self.weather_timer = random.uniform(60, 180)  # Time until weather change
    
    def update(self, dt):
        """Update weather state."""
        self.weather_timer -= dt
        if self.weather_timer <= 0:
            self.weather_timer = random.uniform(60, 180)
            self.target_weather = random.choice(["clear", "clear", "clear", "rain", "thunder"])
        
        # Smooth transition
        if self.weather != self.target_weather:
            self.transition += dt * 0.1
            if self.transition >= 1.0:
                self.weather = self.target_weather
                self.transition = 0.0
        
        # Rain intensity
        if self.weather == "rain":
            self.rain_intensity = min(1.0, self.rain_intensity + dt * 0.5)
        elif self.weather == "thunder":
            self.rain_intensity = min(1.0, self.rain_intensity + dt * 0.8)
            self.thunder_timer -= dt
            if self.thunder_timer <= 0:
                self.thunder_timer = random.uniform(3, 15)
                self.lightning_flash = 0.3
        else:
            self.rain_intensity = max(0.0, self.rain_intensity - dt * 0.3)
        
        # Lightning fade
        if self.lightning_flash > 0:
            self.lightning_flash -= dt * 2
    
    def get_fog_mod(self):
        """Get fog modifier based on weather."""
        base = 1.0
        if self.weather == "rain":
            base = 0.7
        elif self.weather == "thunder":
            base = 0.5
        return base - (1.0 - base) * self.transition * 0.3
    
    def get_light_mod(self):
        """Get light modifier for lightning."""
        return 1.0 + self.lightning_flash * 3.0


class AtmosphereRenderer:
    """Renders atmospheric effects."""
    
    def __init__(self, seed):
        self.seed = seed
        self.weather = WeatherSystem()
        self._wind = None
        
        # Ambient particles
        self.particles = []
        self.max_particles = 200
        
        # Firefly state
        self.fireflies = []
        self.max_fireflies = 50
        
        # Stars
        self.stars = []
        self._generate_stars()
    
    def _generate_stars(self):
        """Generate star positions."""
        rng = random.Random(self.seed + 999)
        for _ in range(200):
            theta = rng.uniform(0, math.pi * 2)
            phi = rng.uniform(0.2, math.pi * 0.45)
            r = 400
            x = r * math.sin(phi) * math.cos(theta)
            y = r * math.cos(phi)
            z = r * math.sin(phi) * math.sin(theta)
            brightness = rng.uniform(0.5, 1.0)
            self.stars.append((x, y, z, brightness))
    
    def update(self, dt, player_pos, day_time, world, wind=None):
        """Update atmosphere effects."""
        self.weather.update(dt)
        self._wind = wind
        
        # Spawn ambient particles
        self._update_ambient_particles(dt, player_pos, day_time)
        
        # Update fireflies (night only)
        brightness = max(0.0, math.sin(day_time * 2 * math.pi))
        if brightness < 0.3:
            self._update_fireflies(dt, player_pos)
        else:
            self.fireflies.clear()
    
    def _update_ambient_particles(self, dt, player_pos, day_time):
        """Update ambient particles (dust, pollen)."""
        # Remove dead particles
        self.particles = [p for p in self.particles if p.life > 0]
        
        # Spawn new particles
        while len(self.particles) < self.max_particles:
            angle = random.uniform(0, math.pi * 2)
            dist = random.uniform(5, 20)
            x = player_pos[0] + math.cos(angle) * dist
            z = player_pos[2] + math.sin(angle) * dist
            y = player_pos[1] + random.uniform(-5, 10)
            
            # Different particle types based on time
            brightness = max(0.0, math.sin(day_time * 2 * math.pi))
            
            if brightness > 0.5:
                # Daytime - dust/pollen
                color = (0.9, 0.9, 0.8, random.uniform(0.1, 0.3))
                vel = [random.uniform(-0.2, 0.2), random.uniform(-0.1, 0.1), random.uniform(-0.2, 0.2)]
                life = random.uniform(3, 8)
                size = random.uniform(1, 3)
                ptype = "dust"
            else:
                # Nighttime - mist
                color = (0.6, 0.7, 0.8, random.uniform(0.05, 0.15))
                vel = [random.uniform(-0.05, 0.05), random.uniform(-0.02, 0.02), random.uniform(-0.05, 0.05)]
                life = random.uniform(5, 15)
                size = random.uniform(3, 8)
                ptype = "mist"
            
            self.particles.append(AtmosphereParticle([x, y, z], vel, color, life, size, ptype))
        
        # Update particles
        for p in self.particles:
            if self._wind:
                self._wind.apply_to_particle(p.vel, dt)
            p.pos[0] += p.vel[0] * dt
            p.pos[1] += p.vel[1] * dt
            p.pos[2] += p.vel[2] * dt
            p.life -= dt
    
    def _update_fireflies(self, dt, player_pos):
        """Update firefly particles at night."""
        # Remove dead fireflies
        self.fireflies = [f for f in self.fireflies if f.life > 0]
        
        # Spawn new fireflies
        while len(self.fireflies) < self.max_fireflies:
            angle = random.uniform(0, math.pi * 2)
            dist = random.uniform(5, 25)
            x = player_pos[0] + math.cos(angle) * dist
            z = player_pos[2] + math.sin(angle) * dist
            y = player_pos[1] + random.uniform(0, 5)
            
            color = (random.uniform(0.7, 1.0), random.uniform(0.8, 1.0), random.uniform(0.1, 0.3), 1.0)
            vel = [random.uniform(-0.5, 0.5), random.uniform(-0.3, 0.3), random.uniform(-0.5, 0.5)]
            life = random.uniform(5, 15)
            
            self.fireflies.append(AtmosphereParticle([x, y, z], vel, color, life, 2.0, "firefly"))
        
        # Update fireflies
        for f in self.fireflies:
            # Random direction changes
            if random.random() < 0.02:
                f.vel = [random.uniform(-0.5, 0.5), random.uniform(-0.3, 0.3), random.uniform(-0.5, 0.5)]
            
            f.pos[0] += f.vel[0] * dt
            f.pos[1] += f.vel[1] * dt
            f.pos[2] += f.vel[2] * dt
            f.life -= dt
    
    def draw_sky(self, day_time, player_pos):
        """Draw enhanced sky with stars."""
        sun_angle = day_time * 2 * math.pi
        brightness = max(0.0, math.sin(sun_angle))
        
        # Draw stars at night
        if brightness < 0.3:
            glDisable(GL_LIGHTING)
            glDisable(GL_FOG)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            
            star_alpha = (0.3 - brightness) / 0.3
            
            glPointSize(2)
            glBegin(GL_POINTS)
            for x, y, z, b in self.stars:
                alpha = b * star_alpha * (0.8 + 0.2 * math.sin(self.weather.weather_timer * 3 + x))
                glColor4f(1.0, 1.0, 0.9, alpha)
                glVertex3f(x + player_pos[0], y, z + player_pos[2])
            glEnd()
            
            # Moon
            moon_angle = sun_angle + math.pi
            moon_x = math.cos(moon_angle) * 350
            moon_y = math.sin(moon_angle) * 350
            glColor4f(0.9, 0.9, 1.0, star_alpha * 0.9)
            glPointSize(30)
            glBegin(GL_POINTS)
            glVertex3f(moon_x + player_pos[0], moon_y, player_pos[2] - 100)
            glEnd()
            # Moon glow
            glColor4f(0.7, 0.7, 0.9, star_alpha * 0.2)
            glPointSize(60)
            glBegin(GL_POINTS)
            glVertex3f(moon_x + player_pos[0], moon_y, player_pos[2] - 100)
            glEnd()
            
            glDisable(GL_BLEND)
            glEnable(GL_FOG)
            glEnable(GL_LIGHTING)
    
    def draw_particles(self, player_pos):
        """Draw atmospheric particles."""
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glPointSize(3)
        
        glBegin(GL_POINTS)
        for p in self.particles:
            alpha = p.color[3] * (p.life / p.max_life)
            glColor4f(p.color[0], p.color[1], p.color[2], alpha)
            glVertex3f(p.pos[0], p.pos[1], p.pos[2])
        glEnd()
        
        # Fireflies (larger, glowing)
        glPointSize(4)
        glBegin(GL_POINTS)
        for f in self.fireflies:
            glow = 0.5 + 0.5 * math.sin(f.life * 5)
            alpha = glow * (f.life / f.max_life)
            glColor4f(f.color[0], f.color[1], f.color[2], alpha)
            glVertex3f(f.pos[0], f.pos[1], f.pos[2])
        glEnd()
        
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)
    
    def draw_rain(self, player_pos, rain_intensity):
        """Draw rain particles, wind-affected."""
        if rain_intensity < 0.1:
            return
        
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        wind_x, wind_z = 0.0, 0.0
        if self._wind:
            wf = self._wind.get_force()
            wind_x, wind_z = wf[0] * 0.3, wf[2] * 0.3

        # Rain drops
        num_drops = int(rain_intensity * 500)
        glLineWidth(1)
        glBegin(GL_LINES)
        
        rng = random.Random(int(time.time() * 10))
        for _ in range(num_drops):
            x = player_pos[0] + rng.uniform(-20, 20)
            z = player_pos[2] + rng.uniform(-20, 20)
            y = player_pos[1] + rng.uniform(5, 15)
            
            glColor4f(0.6, 0.7, 0.9, 0.3 * rain_intensity)
            glVertex3f(x, y, z)
            glVertex3f(x - 0.1 + wind_x, y - 1.5, z - 0.1 + wind_z)
        
        glEnd()
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)
    
    def get_lightning_flash(self):
        """Get lightning flash intensity."""
        return self.weather.lightning_flash


# Import time for rain
import time

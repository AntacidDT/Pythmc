"""Pythmc - Procedural Sound System

Generates all sound effects using numpy waveforms.
No external audio files needed!
"""

import numpy as np
import pygame
import random
import math


# Audio settings
SAMPLE_RATE = 22050
CHANNELS = 1
BUFFER_SIZE = 512


class SoundGenerator:
    """Generates procedural sound effects."""
    
    def __init__(self):
        self.sounds = {}
        self.initialized = False
        self.volume = 0.5
    
    def init(self):
        """Initialize pygame mixer and generate all sounds."""
        if self.initialized:
            return
        
        try:
            pygame.mixer.pre_init(SAMPLE_RATE, -16, CHANNELS, BUFFER_SIZE)
            pygame.mixer.init()
            self.initialized = True
            self._generate_all_sounds()
        except Exception as e:
            print(f"Sound init failed: {e}")
            self.initialized = False
    
    def _generate_all_sounds(self):
        """Generate all game sound effects."""
        # Block sounds
        self.sounds['break_stone'] = self._make_crunch(0.15, freq=150, noise_amt=0.6)
        self.sounds['break_dirt'] = self._make_crunch(0.12, freq=100, noise_amt=0.8)
        self.sounds['break_wood'] = self._make_crunch(0.15, freq=200, noise_amt=0.4)
        self.sounds['break_grass'] = self._make_crunch(0.1, freq=120, noise_amt=0.7)
        self.sounds['break_glass'] = self._make_shatter(0.2)
        self.sounds['break_sand'] = self._make_crunch(0.1, freq=80, noise_amt=0.9)
        
        self.sounds['place_stone'] = self._make_thud(0.1, freq=180)
        self.sounds['place_dirt'] = self._make_thud(0.08, freq=120)
        self.sounds['place_wood'] = self._make_thud(0.1, freq=220)
        self.sounds['place_glass'] = self._make_tink(0.1)
        
        # Player sounds
        self.sounds['step_stone'] = self._make_step(0.06, freq=200)
        self.sounds['step_dirt'] = self._make_step(0.06, freq=120)
        self.sounds['step_wood'] = self._make_step(0.06, freq=250)
        self.sounds['step_grass'] = self._make_step(0.06, freq=100)
        self.sounds['step_sand'] = self._make_step(0.06, freq=80)
        self.sounds['jump'] = self._make_jump(0.15)
        self.sounds['land'] = self._make_thud(0.08, freq=100)
        self.sounds['hurt'] = self._make_hurt(0.2)
        self.sounds['death'] = self._make_death(0.4)
        
        # UI sounds
        self.sounds['click'] = self._make_click(0.05)
        self.sounds['place_fail'] = self._make_buzz(0.08)
        
        # Entity sounds
        self.sounds['cow'] = self._make_moo(0.4)
        self.sounds['chicken'] = self._make_cluck(0.2)
        self.sounds['sheep'] = self._make_baa(0.3)
        self.sounds['zombie'] = self._make_groan(0.4)
        self.sounds['skeleton'] = self._make_rattle(0.3)
        self.sounds['entity_hurt'] = self._make_hit(0.1)
        self.sounds['entity_death'] = self._make_pop(0.15)
    
    def _make_wave(self, duration, freq, wave_type='sine', volume=0.5):
        """Generate a basic waveform."""
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
        if wave_type == 'sine':
            wave = np.sin(2 * np.pi * freq * t)
        elif wave_type == 'square':
            wave = np.sign(np.sin(2 * np.pi * freq * t))
        elif wave_type == 'saw':
            wave = 2 * (freq * t % 1) - 1
        elif wave_type == 'noise':
            wave = np.random.uniform(-1, 1, len(t))
        else:
            wave = np.sin(2 * np.pi * freq * t)
        return wave * volume
    
    def _apply_envelope(self, wave, attack=0.01, decay=0.05, sustain=0.5, release=0.1):
        """Apply ADSR envelope to wave."""
        n = len(wave)
        env = np.ones(n)
        
        # Attack
        a_samples = int(attack * SAMPLE_RATE)
        if a_samples > 0:
            env[:a_samples] = np.linspace(0, 1, a_samples)
        
        # Decay
        d_start = a_samples
        d_samples = int(decay * SAMPLE_RATE)
        d_end = min(d_start + d_samples, n)
        if d_end > d_start:
            env[d_start:d_end] = np.linspace(1, sustain, d_end - d_start)
        
        # Sustain
        if d_end < n:
            env[d_end:n-int(release*SAMPLE_RATE)] = sustain
        
        # Release
        r_samples = int(release * SAMPLE_RATE)
        if r_samples > 0 and n > r_samples:
            env[-r_samples:] = np.linspace(env[-r_samples], 0, r_samples)
        
        return wave * env
    
    def _make_sound(self, wave):
        """Convert numpy array to pygame Sound."""
        wave = np.clip(wave, -1, 1)
        samples = (wave * 32767).astype(np.int16)
        # Make stereo (2 channels)
        stereo = np.column_stack((samples, samples))
        sound = pygame.sndarray.make_sound(stereo)
        sound.set_volume(self.volume)
        return sound
    
    def _make_crunch(self, duration, freq=150, noise_amt=0.5):
        """Block breaking crunch sound."""
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
        # Mix of noise and tone
        noise = np.random.uniform(-1, 1, len(t))
        tone = np.sin(2 * np.pi * freq * t)
        wave = noise * noise_amt + tone * (1 - noise_amt)
        # Quick decay
        env = np.exp(-t * 20)
        wave = wave * env * 0.6
        return self._make_sound(wave)
    
    def _make_thud(self, duration, freq=180):
        """Block placing thud."""
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
        wave = np.sin(2 * np.pi * freq * t) * 0.5
        noise = np.random.uniform(-0.3, 0.3, len(t))
        wave = wave + noise
        env = np.exp(-t * 30)
        return self._make_sound(wave * env * 0.5)
    
    def _make_shatter(self, duration):
        """Glass breaking sound."""
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
        # High frequency noise
        noise = np.random.uniform(-1, 1, len(t))
        # High-pass effect
        freqs = np.random.uniform(2000, 8000, len(t))
        tones = np.sin(2 * np.pi * freqs * t) * 0.3
        wave = noise * 0.5 + tones
        env = np.exp(-t * 15)
        return self._make_sound(wave * env * 0.5)
    
    def _make_tink(self, duration):
        """Glass/stone tink sound."""
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
        wave = np.sin(2 * np.pi * 1200 * t) * 0.5
        wave += np.sin(2 * np.pi * 1800 * t) * 0.3
        env = np.exp(-t * 40)
        return self._make_sound(wave * env * 0.4)
    
    def _make_step(self, duration, freq=150):
        """Footstep sound."""
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
        noise = np.random.uniform(-1, 1, len(t))
        wave = noise * 0.7 + np.sin(2 * np.pi * freq * t) * 0.3
        env = np.exp(-t * 50)
        return self._make_sound(wave * env * 0.3)
    
    def _make_jump(self, duration):
        """Jump sound - rising tone."""
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
        freq = 200 + t * 2000
        wave = np.sin(2 * np.pi * freq * t / SAMPLE_RATE * np.cumsum(np.ones(len(t))))
        env = np.exp(-t * 8)
        return self._make_sound(wave * env * 0.3)
    
    def _make_hurt(self, duration):
        """Player hurt sound."""
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
        freq = 300 + np.sin(2 * np.pi * 20 * t) * 100
        wave = np.sin(2 * np.pi * freq * t / SAMPLE_RATE * np.cumsum(np.ones(len(t))))
        noise = np.random.uniform(-0.3, 0.3, len(t))
        wave = wave * 0.6 + noise * 0.4
        env = np.exp(-t * 5)
        return self._make_sound(wave * env * 0.5)
    
    def _make_death(self, duration):
        """Player death sound."""
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
        freq = 400 - t * 800
        wave = np.sin(2 * np.pi * np.abs(freq) * t / SAMPLE_RATE * np.cumsum(np.ones(len(t))))
        noise = np.random.uniform(-0.5, 0.5, len(t))
        wave = wave * 0.5 + noise * 0.5
        env = np.exp(-t * 3)
        return self._make_sound(wave * env * 0.6)
    
    def _make_click(self, duration):
        """UI click sound."""
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
        wave = np.sin(2 * np.pi * 800 * t)
        env = np.exp(-t * 60)
        return self._make_sound(wave * env * 0.3)
    
    def _make_buzz(self, duration):
        """Fail/buzz sound."""
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
        wave = np.sin(2 * np.pi * 150 * t)
        wave += np.sin(2 * np.pi * 155 * t)  # Slight detune for buzz
        env = np.exp(-t * 10)
        return self._make_sound(wave * env * 0.3)
    
    def _make_oink(self, duration):
        """Pig sound."""
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
        freq = 250 + np.sin(2 * np.pi * 8 * t) * 50
        wave = np.sin(2 * np.pi * freq * t / SAMPLE_RATE * np.cumsum(np.ones(len(t))))
        wave += np.sin(2 * np.pi * freq * 2 * t / SAMPLE_RATE * np.cumsum(np.ones(len(t)))) * 0.3
        env = np.exp(-t * 4)
        return self._make_sound(wave * env * 0.4)
    
    def _make_moo(self, duration):
        """Cow sound."""
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
        freq = 120 + np.sin(2 * np.pi * 3 * t) * 20
        wave = np.sin(2 * np.pi * freq * t / SAMPLE_RATE * np.cumsum(np.ones(len(t))))
        wave += np.sin(2 * np.pi * freq * 1.5 * t / SAMPLE_RATE * np.cumsum(np.ones(len(t)))) * 0.4
        env = np.exp(-t * 2)
        return self._make_sound(wave * env * 0.5)
    
    def _make_cluck(self, duration):
        """Chicken sound."""
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
        freq = 600 + np.random.uniform(-100, 100, len(t))
        wave = np.sin(2 * np.pi * freq * t / SAMPLE_RATE * np.cumsum(np.ones(len(t))))
        env = np.zeros(len(t))
        # Quick pecks
        for i in range(3):
            start = int(i * len(t) / 4)
            end = min(start + len(t) // 6, len(t))
            env[start:end] = np.exp(-np.linspace(0, 5, end - start))
        return self._make_sound(wave * env * 0.3)
    
    def _make_baa(self, duration):
        """Sheep sound."""
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
        freq = 200 + np.sin(2 * np.pi * 5 * t) * 80
        wave = np.sin(2 * np.pi * freq * t / SAMPLE_RATE * np.cumsum(np.ones(len(t))))
        noise = np.random.uniform(-0.2, 0.2, len(t))
        wave = wave * 0.7 + noise * 0.3
        env = np.exp(-t * 3)
        return self._make_sound(wave * env * 0.4)
    
    def _make_groan(self, duration):
        """Zombie groan."""
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
        freq = 80 + np.sin(2 * np.pi * 2 * t) * 30
        wave = np.sin(2 * np.pi * freq * t / SAMPLE_RATE * np.cumsum(np.ones(len(t))))
        wave += np.sin(2 * np.pi * freq * 0.5 * t / SAMPLE_RATE * np.cumsum(np.ones(len(t)))) * 0.5
        noise = np.random.uniform(-0.4, 0.4, len(t))
        wave = wave * 0.6 + noise * 0.4
        env = np.exp(-t * 2)
        return self._make_sound(wave * env * 0.5)
    
    def _make_rattle(self, duration):
        """Skeleton rattle."""
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
        # Multiple high-freq tones
        wave = np.zeros(len(t))
        for f in [800, 1200, 1600, 2000]:
            wave += np.sin(2 * np.pi * f * t) * 0.15
        # Rattle modulation
        mod = np.abs(np.sin(2 * np.pi * 30 * t))
        wave = wave * mod
        env = np.exp(-t * 4)
        return self._make_sound(wave * env * 0.3)
    
    def _make_hit(self, duration):
        """Entity hit sound."""
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
        noise = np.random.uniform(-1, 1, len(t))
        tone = np.sin(2 * np.pi * 300 * t)
        wave = noise * 0.5 + tone * 0.5
        env = np.exp(-t * 20)
        return self._make_sound(wave * env * 0.4)
    
    def _make_pop(self, duration):
        """Entity death pop."""
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
        freq = 500 - t * 1500
        wave = np.sin(2 * np.pi * np.abs(freq) * t / SAMPLE_RATE * np.cumsum(np.ones(len(t))))
        env = np.exp(-t * 10)
        return self._make_sound(wave * env * 0.4)
    
    def play(self, sound_name, volume_mult=1.0):
        """Play a sound effect."""
        if not self.initialized:
            return
        sound = self.sounds.get(sound_name)
        if sound:
            sound.set_volume(self.volume * volume_mult)
            sound.play()
    
    def play_random(self, sound_names, volume_mult=1.0):
        """Play a random sound from a list."""
        if sound_names:
            self.play(random.choice(sound_names), volume_mult)
    
    def set_volume(self, volume):
        """Set master volume (0.0 to 1.0)."""
        self.volume = max(0.0, min(1.0, volume))


# Global sound manager
sound_manager = SoundGenerator()

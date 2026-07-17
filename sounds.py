"""Pythmc - Procedural Sound System

Generates all sound effects and background music using numpy waveforms.
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
        try:
            sound = self.sounds.get(sound_name)
            if sound:
                sound.set_volume(self.volume * volume_mult)
                sound.play()
        except Exception:
            pass
    
    def play_random(self, sound_names, volume_mult=1.0):
        """Play a random sound from a list."""
        if sound_names:
            self.play(random.choice(sound_names), volume_mult)
    
    def set_volume(self, volume):
        """Set master volume (0.0 to 1.0)."""
        self.volume = max(0.0, min(1.0, volume))


# Global sound manager
sound_manager = SoundGenerator()


class MusicManager:
    """Background music manager — MIDI files with procedural fallback."""

    def __init__(self):
        self.playing = False
        self.volume = 0.30
        self._midi_player = None
        self._fallback_sound = None
        self._channel = None
        self._using_midi = False

    def init(self):
        """Load MIDI songs and/or generate fallback track."""
        try:
            from midi_player import MidiPlayer
            self._midi_player = MidiPlayer()
            self._midi_player.load()
        except Exception as e:
            print(f"  Music: MIDI player init failed: {e}")
            self._midi_player = None

        if not self._midi_player or not self._midi_player.songs:
            self._fallback_sound = self._generate_fallback()
            self._using_midi = False
        else:
            self._using_midi = True

    def start(self):
        """Start playing music."""
        if self.playing:
            return
        self.playing = True

        if self._using_midi and self._midi_player:
            self._midi_player.set_volume(self.volume)
            self._midi_player.start()
        else:
            self._start_fallback()

    def stop(self):
        """Stop music."""
        self.playing = False
        if self._using_midi and self._midi_player:
            self._midi_player.stop()
        elif self._channel:
            try:
                self._channel.stop()
            except Exception:
                pass

    def set_volume(self, v):
        self.volume = max(0.0, min(1.0, v))
        if self._using_midi and self._midi_player:
            self._midi_player.set_volume(self.volume)
        elif self._channel:
            try:
                self._channel.set_volume(self.volume)
            except Exception:
                pass

    def update(self):
        """Call from game loop to keep music going."""
        if not self.playing:
            return
        if self._using_midi and self._midi_player:
            self._midi_player.update()
        elif self._channel and not self._channel.get_busy():
            self._loop_fallback()

    def _start_fallback(self):
        if not self._fallback_sound:
            return
        try:
            self._channel = pygame.mixer.Channel(7)
            self._channel.set_volume(self.volume)
            self._channel.play(self._fallback_sound)
        except Exception:
            self.playing = False

    def _loop_fallback(self):
        if not self._fallback_sound or not self._channel:
            return
        try:
            self._channel.play(self._fallback_sound)
        except Exception:
            self.playing = False

    def _generate_fallback(self):
        """Generate a ~20 second ambient pad loop as fallback."""
        duration = 20.0
        n = int(SAMPLE_RATE * duration)
        t = np.linspace(0, duration, n, False)

        chord_freqs = [
            [110.0, 130.81, 164.81, 220.0, 329.63],
            [87.31, 130.81, 174.61, 261.63, 349.23],
            [130.81, 164.81, 196.0, 261.63, 392.0],
            [98.0, 146.83, 196.0, 293.66, 392.0],
        ]

        pad = np.zeros(n)
        chord_len = n // 4

        for ci, freqs in enumerate(chord_freqs):
            start = ci * chord_len
            end = min((ci + 1) * chord_len, n)
            seg_t = t[start:end]
            for f in freqs:
                vibrato = 1.0 + 0.003 * np.sin(2 * np.pi * 0.3 * seg_t)
                tone = np.sin(2 * np.pi * f * vibrato * seg_t) * 0.08
                tone += np.sin(2 * np.pi * f * 2 * seg_t) * 0.03
                pad[start:end] += tone
            fade_len = min(2000, chord_len // 4)
            if ci > 0 and start + fade_len < n:
                fade_in = np.linspace(0, 1, fade_len)
                pad[start:start+fade_len] *= fade_in

        arp_notes = [261.63, 329.63, 392.0, 523.25, 392.0, 329.63]
        arp = np.zeros(n)
        note_dur = 0.8
        for i in range(int(duration / note_dur)):
            freq = arp_notes[i % len(arp_notes)]
            note_start = int(i * note_dur * SAMPLE_RATE)
            note_end = min(note_start + int(note_dur * SAMPLE_RATE), n)
            if note_start >= n:
                break
            seg_t = np.linspace(0, note_dur, note_end - note_start, False)
            env = np.exp(-seg_t * 3.0) * 0.04
            arp[note_start:note_end] += np.sin(2 * np.pi * freq * seg_t) * env

        bass_freqs = [55.0, 43.65, 65.41, 49.0]
        bass = np.zeros(n)
        for ci, bf in enumerate(bass_freqs):
            start = ci * chord_len
            end = min((ci + 1) * chord_len, n)
            seg_t = t[start:end]
            bass[start:end] += np.sin(2 * np.pi * bf * seg_t) * 0.06

        mix = pad + arp + bass

        fade_s = int(2.0 * SAMPLE_RATE)
        mix[:fade_s] *= np.linspace(0, 1, fade_s)
        mix[-fade_s:] *= np.linspace(1, 0, fade_s)

        peak = np.max(np.abs(mix))
        if peak > 0:
            mix = mix / peak * 0.7

        mix = np.clip(mix, -1, 1)
        samples = (mix * 32767).astype(np.int16)
        stereo = np.column_stack((samples, samples))
        return pygame.sndarray.make_sound(stereo)


# Global music manager
music = MusicManager()

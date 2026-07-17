"""Pythmc - MIDI File Player (V2.6)

Parses standard MIDI files, synthesizes them into audio,
and plays them as background music. Drop .mid files into
the music/ folder and they auto-load.

No external MIDI library needed — pure Python parser.
"""

import numpy as np
import pygame
import os
import struct
import random

SAMPLE_RATE = 22050


# ─── MIDI Parser ─────────────────────────────────────────────────────────────

def _read_var_len(data, pos):
    """Read a MIDI variable-length quantity."""
    result = 0
    while pos < len(data):
        byte = data[pos]
        pos += 1
        result = (result << 7) | (byte & 0x7F)
        if byte < 0x80:
            break
    return result, pos


def parse_midi(filepath):
    """Parse a MIDI file and return list of note events.

    Returns:
        list of (time_sec, note, velocity, channel)
        where note is MIDI note number (0-127)
    """
    with open(filepath, 'rb') as f:
        data = f.read()

    if data[:4] != b'MThd':
        raise ValueError("Not a MIDI file")

    header_len = struct.unpack('>I', data[4:8])[0]
    fmt = struct.unpack('>H', data[8:10])[0]
    num_tracks = struct.unpack('>H', data[10:12])[0]
    time_div = struct.unpack('>H', data[12:14])[0]

    # Time division: ticks per quarter note (assuming no SMPTE)
    tpb = time_div & 0x7FFF

    # Default tempo: 120 BPM = 500000 microseconds per quarter note
    default_tempo = 500000
    tempo = default_tempo

    events = []
    pos = 14  # skip header

    for _ in range(num_tracks):
        if pos >= len(data):
            break
        if data[pos:pos+4] != b'MTrk':
            break
        track_len = struct.unpack('>I', data[pos+4:pos+8])[0]
        track_data = data[pos+8:pos+8+track_len]
        pos += 8 + track_len

        tick = 0
        running_status = 0
        event_pos = 0

        while event_pos < len(track_data):
            delta, event_pos = _read_var_len(track_data, event_pos)
            tick += delta

            byte = track_data[event_pos]
            event_pos += 1

            if byte == 0xFF:
                # Meta event
                meta_type = track_data[event_pos]
                event_pos += 1
                meta_len, event_pos = _read_var_len(track_data, event_pos)
                meta_data = track_data[event_pos:event_pos+meta_len]
                event_pos += meta_len

                if meta_type == 0x51:
                    # Set tempo
                    if len(meta_data) >= 3:
                        tempo = (meta_data[0] << 16) | (meta_data[1] << 8) | meta_data[2]
                elif meta_type == 0x2F:
                    # End of track
                    break
                # Ignore other meta events (time sig, key sig, etc.)

            elif byte == 0xF0 or byte == 0xF7:
                # SysEx - skip
                sysex_len, event_pos = _read_var_len(track_data, event_pos)
                event_pos += sysex_len

            elif byte & 0x80:
                # New status byte
                running_status = byte
                event_pos = _handle_midi_event(
                    track_data, event_pos, byte, tick, tempo, tpb, events)

            else:
                # Data byte — use running status
                event_pos = _handle_midi_event(
                    track_data, event_pos, running_status, tick, tempo, tpb, events)

    # Sort by time
    events.sort(key=lambda e: e[0])
    return events


def _handle_midi_event(data, pos, status, tick, tempo, tpb, events):
    """Handle a MIDI event and append to events list."""
    hi = status & 0xF0
    channel = status & 0x0F

    if hi == 0x90:
        # Note On
        if pos + 1 < len(data):
            note = data[pos]
            velocity = data[pos + 1]
            time_sec = tick * tempo / (tpb * 1000000.0)
            if velocity > 0:
                events.append((time_sec, note, velocity, channel))
            else:
                # velocity 0 = note off
                events.append((time_sec, note, 0, channel))
            return pos + 2

    elif hi == 0x80:
        # Note Off
        if pos + 1 < len(data):
            note = data[pos]
            time_sec = tick * tempo / (tpb * 1000000.0)
            events.append((time_sec, note, 0, channel))
            return pos + 2

    elif hi == 0xA0:
        # Polyphonic aftertouch — skip 2 bytes
        return pos + 2

    elif hi == 0xB0:
        # Control change — skip 2 bytes
        return pos + 2

    elif hi == 0xC0:
        # Program change — skip 1 byte
        return pos + 1

    elif hi == 0xD0:
        # Channel aftertouch — skip 1 byte
        return pos + 1

    elif hi == 0xE0:
        # Pitch bend — skip 2 bytes
        return pos + 2

    return pos


# ─── Synthesizer ─────────────────────────────────────────────────────────────

def _midi_to_freq(note):
    """Convert MIDI note number to frequency in Hz."""
    return 440.0 * (2.0 ** ((note - 69) / 12.0))


def _make_envelope(n, attack=0.01, decay=0.05, sustain=0.6, release=0.15, sr=SAMPLE_RATE):
    """Create an ADSR envelope."""
    env = np.ones(n, dtype=np.float64)

    a = int(attack * sr)
    if a > 0 and a < n:
        env[:a] = np.linspace(0, 1, a)

    d = int(decay * sr)
    d_start = a
    d_end = min(a + d, n)
    if d_end > d_start:
        env[d_start:d_end] = np.linspace(1, sustain, d_end - d_start)

    if d_end < n:
        env[d_end:] = sustain

    r = int(release * sr)
    if r > 0 and r < n:
        env[-r:] = np.linspace(sustain, 0, r)

    return env


def _make_note(freq, duration, velocity, waveform='piano'):
    """Synthesize a single note."""
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, False)

    v = velocity / 127.0

    if waveform == 'piano':
        # Rich piano-like tone: fundamental + harmonics with detuned partials
        wave = np.sin(2 * np.pi * freq * t) * 0.50
        wave += np.sin(2 * np.pi * freq * 2.003 * t) * 0.20
        wave += np.sin(2 * np.pi * freq * 3.0 * t) * 0.10
        wave += np.sin(2 * np.pi * freq * 4.001 * t) * 0.06
        wave += np.sin(2 * np.pi * freq * 5.998 * t) * 0.03
        # Slight brightness from saw
        wave += (2 * (freq * t % 1) - 1) * 0.04
        env = _make_envelope(n, attack=0.005, decay=0.08, sustain=0.45, release=0.2)
        wave *= env * v

    elif waveform == 'harp':
        # Plucked string
        wave = np.sin(2 * np.pi * freq * t) * 0.55
        wave += np.sin(2 * np.pi * freq * 1.998 * t) * 0.25
        wave += np.sin(2 * np.pi * freq * 3.002 * t) * 0.12
        env = _make_envelope(n, attack=0.002, decay=0.15, sustain=0.25, release=0.3)
        wave *= env * v

    elif waveform == 'pad':
        # Soft pad
        wave = np.sin(2 * np.pi * freq * t) * 0.45
        wave += np.sin(2 * np.pi * freq * 2.0 * t) * 0.25
        wave += np.sin(2 * np.pi * freq * 0.5 * t) * 0.20
        vibrato = 1.0 + 0.005 * np.sin(2 * np.pi * 4.5 * t)
        wave *= vibrato
        env = _make_envelope(n, attack=0.08, decay=0.1, sustain=0.7, release=0.3)
        wave *= env * v

    elif waveform == 'bass':
        # Deep bass
        wave = np.sin(2 * np.pi * freq * t) * 0.6
        wave += np.sin(2 * np.pi * freq * 2.0 * t) * 0.2
        wave += (2 * (freq * t % 1) - 1) * 0.15
        env = _make_envelope(n, attack=0.008, decay=0.1, sustain=0.5, release=0.15)
        wave *= env * v

    elif waveform == 'flute':
        # Soft flute
        wave = np.sin(2 * np.pi * freq * t) * 0.5
        wave += np.sin(2 * np.pi * freq * 2.0 * t) * 0.08
        vibrato = 1.0 + 0.008 * np.sin(2 * np.pi * 5.0 * t)
        wave *= vibrato
        env = _make_envelope(n, attack=0.04, decay=0.05, sustain=0.7, release=0.15)
        wave *= env * v

    else:
        # Default sine
        wave = np.sin(2 * np.pi * freq * t)
        env = _make_envelope(n, attack=0.01, decay=0.05, sustain=0.5, release=0.1)
        wave *= env * v

    return wave


# Channel-to-instrument mapping (General MIDI programs)
# We pick a synth waveform based on MIDI program number
_PROGRAM_WAVEFORM = {
    0: 'piano',     # Acoustic Grand Piano
    1: 'piano',     # Bright Acoustic Piano
    2: 'piano',     # Electric Grand Piano
    3: 'piano',     # Honky-tonk Piano
    4: 'piano',     # Electric Piano 1
    5: 'piano',     # Electric Piano 2
    6: 'harp',      # Harpsichord
    7: 'harp',      # Clavinet
    9: 'piano',     # Celesta
    10: 'harp',     # Glockenspiel
    11: 'harp',     # Music Box
    12: 'harp',     # Vibraphone
    13: 'harp',     # Marimba
    14: 'harp',     # Xylophone
    15: 'harp',     # Tubular Bells
    16: 'pad',      # Drawbar Organ
    17: 'pad',      # Percussive Organ
    18: 'pad',      # Rock Organ
    19: 'pad',      # Church Organ
    20: 'pad',      # Reed Organ
    24: 'harp',     # Nylon Guitar
    25: 'harp',     # Steel Guitar
    26: 'harp',     # Jazz Guitar
    27: 'harp',     # Clean Guitar
    28: 'harp',     # Muted Guitar
    30: 'pad',      # Overdriven Guitar
    31: 'pad',      # Distortion Guitar
    32: 'pad',      # Guitar Harmonics
    33: 'bass',     # Acoustic Bass
    34: 'bass',     # Electric Bass (finger)
    35: 'bass',     # Electric Bass (pick)
    36: 'bass',     # Fretless Bass
    37: 'bass',     # Slap Bass 1
    38: 'bass',     # Slap Bass 2
    39: 'bass',     # Synth Bass 1
    40: 'bass',     # Synth Bass 2
    41: 'pad',      # Violin
    42: 'pad',      # Viola
    43: 'pad',      # Cello
    44: 'pad',      # Contrabass
    45: 'pad',      # Tremolo Strings
    46: 'pad',      # Pizzicato Strings
    48: 'pad',      # String Ensemble 1
    49: 'pad',      # String Ensemble 2
    50: 'pad',      # Synth Strings 1
    51: 'pad',      # Synth Strings 2
    56: 'flute',    # Trumpet
    57: 'flute',    # Trombone
    58: 'flute',    # Tuba
    59: 'flute',    # Muted Trumpet
    60: 'flute',    # French Horn
    61: 'flute',    # Brass Section
    65: 'flute',    # Soprano Sax
    66: 'flute',    # Alto Sax
    67: 'flute',    # Tenor Sax
    68: 'flute',    # Baritone Sax
    70: 'flute',    # Bassoon
    71: 'flute',    # Clarinet
    72: 'flute',    # Piccolo
    73: 'flute',    # Flute
    74: 'flute',    # Recorder
    75: 'flute',    # Pan Flute
    76: 'flute',    # Blown Bottle
    77: 'flute',    # Shakuhachi
    78: 'flute',    # Whistle
    79: 'flute',    # Ocarina
    80: 'pad',      # Lead 1 (square)
    81: 'pad',      # Lead 2 (sawtooth)
    85: 'pad',      # Pad 1 (new age)
    86: 'pad',      # Pad 2 (warm)
    87: 'pad',      # Pad 3 (polysynth)
    88: 'pad',      # Pad 4 (choir)
    89: 'pad',      # Pad 5 (bowed)
    90: 'pad',      # Pad 6 (metallic)
    91: 'pad',      # Pad 7 (halo)
    92: 'pad',      # Pad 8 (sweep)
    93: 'pad',      # FX 1 (rain)
    94: 'pad',      # FX 2 (soundtrack)
    95: 'pad',      # FX 3 (crystal)
    96: 'pad',      # FX 4 (atmosphere)
}

# Which MIDI channels are typically percussion (channel 9 = GM drums)
_PERCUSSION_CHANNEL = 9

# Approximate note ranges for waveform selection (fallback)
_LOW_NOTE = 36   # C2
_MID_NOTE = 60   # C4
_HIGH_NOTE = 84  # C6


def _get_waveform_for_channel(channel, program=0):
    """Pick a synth waveform based on channel and program."""
    if channel == _PERCUSSION_CHANNEL:
        return 'harp'  # Percussion → pluck
    return _PROGRAM_WAVEFORM.get(program, 'piano')


def synthesize_midi(events, extra_time=2.0, volume=0.35):
    """Synthesize MIDI events into a stereo numpy array.

    Args:
        events: list of (time_sec, note, velocity, channel)
        extra_time: seconds of silence after last event
        volume: master volume 0.0-1.0

    Returns:
        (numpy_array, sample_rate) — stereo int16
    """
    if not events:
        n = int(SAMPLE_RATE * 2)
        return np.zeros((n, 2), dtype=np.int16), SAMPLE_RATE

    # Track active notes per channel with program numbers
    # Default program 0 (piano) for all channels
    channel_programs = {}
    for _, _, _, ch in events:
        if ch not in channel_programs:
            channel_programs[ch] = 0

    # Find total duration
    last_time = max(t for t, _, _, _ in events)
    total_duration = last_time + extra_time
    total_samples = int(SAMPLE_RATE * total_duration)

    # Accumulator
    mix = np.zeros(total_samples, dtype=np.float64)

    # Track note-on state per channel+note
    active = {}  # (channel, note) -> (start_sample, velocity, waveform)

    for time_sec, note, velocity, channel in events:
        start_sample = int(time_sec * SAMPLE_RATE)
        key = (channel, note)

        if velocity > 0:
            # Note On
            waveform = _get_waveform_for_channel(channel, channel_programs.get(channel, 0))
            active[key] = (start_sample, velocity, waveform)
        else:
            # Note Off
            if key in active:
                on_sample, vel, wf = active.pop(key)
                freq = _midi_to_freq(note)

                # Note duration
                dur_samples = start_sample - on_sample
                if dur_samples < 1:
                    dur_samples = int(SAMPLE_RATE * 0.1)

                duration = dur_samples / SAMPLE_RATE

                # Generate note
                wave = _make_note(freq, duration, vel, wf)

                # Add to mix
                end = min(on_sample + len(wave), total_samples)
                actual_len = end - on_sample
                if actual_len > 0:
                    mix[on_sample:end] += wave[:actual_len]

    # Close any remaining active notes
    for key, (on_sample, vel, wf) in active.items():
        channel, note = key
        freq = _midi_to_freq(note)
        dur = 0.5  # Default sustain for unclosed notes
        wave = _make_note(freq, dur, vel, wf)
        end = min(on_sample + len(wave), total_samples)
        actual_len = end - on_sample
        if actual_len > 0:
            mix[on_sample:end] += wave[:actual_len]

    # Normalize
    peak = np.max(np.abs(mix))
    if peak > 0:
        mix = mix / peak * 0.8

    # Global fade in/out
    fade_samples = int(1.5 * SAMPLE_RATE)
    if fade_samples > 0 and fade_samples * 2 < total_samples:
        mix[:fade_samples] *= np.linspace(0, 1, fade_samples)
        mix[-fade_samples:] *= np.linspace(1, 0, fade_samples)

    # Apply volume
    mix *= volume

    # To stereo int16
    mix = np.clip(mix, -1, 1)
    samples = (mix * 32767).astype(np.int16)
    stereo = np.column_stack((samples, samples))

    return stereo, SAMPLE_RATE


def load_midi_file(filepath, volume=0.35):
    """Load a MIDI file and return a pygame Sound."""
    events = parse_midi(filepath)
    if not events:
        return None
    stereo, sr = synthesize_midi(events, volume=volume)
    sound = pygame.sndarray.make_sound(stereo)
    return sound


# ─── Music Player ────────────────────────────────────────────────────────────

class MidiPlayer:
    """Plays MIDI files from a directory as background music."""

    def __init__(self, music_dir=None):
        if music_dir is None:
            music_dir = os.path.join(os.path.dirname(__file__), "music")
        self.music_dir = music_dir
        self.songs = []
        self.current_index = 0
        self.playing = False
        self._channel = None
        self._volume = 0.30
        self._current_sound = None
        self._fade_timer = 0.0
        self._fade_duration = 2.0
        self._fading_out = False
        self._silence_timer = 0.0
        self._silence_duration = 3.0

    def load(self):
        """Scan music directory for .mid files (no synthesis yet — lazy)."""
        self.songs = []
        if not os.path.isdir(self.music_dir):
            os.makedirs(self.music_dir, exist_ok=True)
            return

        for fname in sorted(os.listdir(self.music_dir)):
            if fname.lower().endswith(('.mid', '.midi')):
                path = os.path.join(self.music_dir, fname)
                self.songs.append((fname, path, None))

        if self.songs:
            random.shuffle(self.songs)
            print(f"  Music: {len(self.songs)} MIDI files found")
        else:
            print("  Music: No .mid files found in music/")

    def start(self):
        """Start playing music."""
        if not self.songs:
            return
        self.playing = True
        self.current_index = 0
        self._channel = pygame.mixer.Channel(7)
        self._play_current()

    def stop(self):
        """Stop playing."""
        self.playing = False
        if self._channel:
            try:
                self._channel.stop()
            except Exception:
                pass

    def set_volume(self, v):
        self._volume = max(0.0, min(1.0, v))

    def update(self):
        """Call each frame to handle song transitions."""
        if not self.playing or not self._channel:
            return

        if self._fading_out:
            self._fade_timer += 1.0 / 60.0  # Approximate dt
            if self._fade_timer >= self._fade_duration:
                self._fading_out = False
                self._silence_timer = 0.0
                self._channel.stop()
            return

        if self._silence_timer > 0:
            self._silence_timer += 1.0 / 60.0
            if self._silence_timer >= self._silence_duration:
                self._silence_timer = 0.0
                self._advance_song()
            return

        if not self._channel.get_busy():
            # Song ended naturally — brief silence then next
            self._silence_timer = 0.001  # Start silence timer

    def _play_current(self):
        if not self.songs or not self._channel:
            return
        idx = self.current_index % len(self.songs)
        name, path, cached_sound = self.songs[idx]

        if cached_sound is None:
            try:
                print(f"  Music: Synthesizing {name}...")
                cached_sound = load_midi_file(path, volume=self._volume)
                self.songs[idx] = (name, path, cached_sound)
            except Exception as e:
                print(f"  Music: Failed to synthesize {name}: {e}")
                self._advance_song()
                return

        if cached_sound is None:
            self._advance_song()
            return

        self._current_sound = cached_sound
        try:
            self._channel.set_volume(self._volume)
            self._channel.play(cached_sound)
            print(f"  Music: Now playing: {name}")
        except Exception:
            pass

    def _advance_song(self):
        if not self.songs:
            return
        self.current_index = (self.current_index + 1) % len(self.songs)
        self._play_current()

    def next_song(self):
        """Skip to next song."""
        self._silence_timer = 0.0
        self._fading_out = False
        if self._channel:
            self._channel.stop()
        self._advance_song()

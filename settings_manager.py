"""Pythmc - Settings Manager (V2.0) - Global and per-world configurable constants"""

import os
import json

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")

# Defaults from constants.py
DEFAULTS = {
    "physics": {
        "gravity": -25.0,
        "jump_speed": 9.0,
        "player_height": 1.62,
        "player_width": 0.3,
        "walk_speed": 4.3,
        "sprint_speed": 6.5,
        "swim_speed": 3.0,
        "fly_speed": 12.0,
        "break_cooldown": 0.2,
        "place_cooldown": 0.2,
        "max_reach": 6.0,
        "water_drag": 0.6,
    },
    "world": {
        "chunk_size": 16,
        "chunk_height": 64,
        "render_distance": 4,
        "day_speed": 0.005,
    },
    "screen": {
        "screen_w": 1280,
        "screen_h": 720,
        "fps": 60,
        "fov": 70,
        "sensitivity": 0.15,
        "volume": 0.5,
    },
    "gpu": {
        "cuda_enabled": False,
    },
    "appearance": {
        "skin_r": 230, "skin_g": 191, "skin_b": 153,
        "shirt_r": 51, "shirt_g": 128, "shirt_b": 204,
        "pants_r": 77, "pants_g": 77, "pants_b": 153,
        "eyes_r": 26, "eyes_g": 77, "eyes_b": 153,
    },
}

# Ranges for clamping values
RANGES = {
    "physics": {
        "gravity": (-100.0, -1.0),
        "jump_speed": (1.0, 30.0),
        "player_height": (0.5, 3.0),
        "player_width": (0.1, 1.0),
        "walk_speed": (1.0, 20.0),
        "sprint_speed": (1.0, 30.0),
        "swim_speed": (1.0, 15.0),
        "fly_speed": (1.0, 50.0),
        "break_cooldown": (0.01, 2.0),
        "place_cooldown": (0.01, 2.0),
        "max_reach": (1.0, 20.0),
        "water_drag": (0.1, 1.0),
    },
    "world": {
        "chunk_size": (8, 32),
        "chunk_height": (32, 256),
        "render_distance": (2, 12),
        "day_speed": (0.0, 0.05),
    },
    "screen": {
        "screen_w": (640, 3840),
        "screen_h": (480, 2160),
        "fps": (30, 240),
        "fov": (30, 120),
        "sensitivity": (0.01, 1.0),
        "volume": (0.0, 1.0),
    },
    "gpu": {
        "cuda_enabled": (0, 1),
    },
    "appearance": {
        "skin_r": (0, 255), "skin_g": (0, 255), "skin_b": (0, 255),
        "shirt_r": (0, 255), "shirt_g": (0, 255), "shirt_b": (0, 255),
        "pants_r": (0, 255), "pants_g": (0, 255), "pants_b": (0, 255),
        "eyes_r": (0, 255), "eyes_g": (0, 255), "eyes_b": (0, 255),
    },
}

# Display names for UI
DISPLAY_NAMES = {
    "physics": {
        "gravity": "Gravity",
        "jump_speed": "Jump Speed",
        "player_height": "Player Height",
        "player_width": "Player Width",
        "walk_speed": "Walk Speed",
        "sprint_speed": "Sprint Speed",
        "swim_speed": "Swim Speed",
        "fly_speed": "Fly Speed",
        "break_cooldown": "Break Cooldown",
        "place_cooldown": "Place Cooldown",
        "max_reach": "Max Reach",
        "water_drag": "Water Drag",
    },
    "world": {
        "chunk_size": "Chunk Size",
        "chunk_height": "Chunk Height",
        "render_distance": "Render Distance",
        "day_speed": "Day Speed",
    },
    "screen": {
        "screen_w": "Screen Width",
        "screen_h": "Screen Height",
        "fps": "Target FPS",
        "fov": "Field of View",
        "sensitivity": "Mouse Sensitivity",
        "volume": "Master Volume",
    },
    "gpu": {
        "cuda_enabled": "NVIDIA CUDA",
    },
    "appearance": {
        "skin_r": "Skin Red", "skin_g": "Skin Green", "skin_b": "Skin Blue",
        "shirt_r": "Shirt Red", "shirt_g": "Shirt Green", "shirt_b": "Shirt Blue",
        "pants_r": "Pants Red", "pants_g": "Pants Green", "pants_b": "Pants Blue",
        "eyes_r": "Eyes Red", "eyes_g": "Eyes Green", "eyes_b": "Eyes Blue",
    },
}


def _clamp(value, lo, hi):
    return max(lo, min(hi, value))


class SettingsManager:
    def __init__(self):
        self.settings = {}
        self.load()

    def load(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r") as f:
                    self.settings = json.load(f)
            except Exception:
                self.settings = {}
        # Fill in any missing keys from defaults
        for category, values in DEFAULTS.items():
            if category not in self.settings:
                self.settings[category] = {}
            for key, default_val in values.items():
                if key not in self.settings[category]:
                    self.settings[category][key] = default_val
        self._clamp_all()

    def save(self):
        self._clamp_all()
        with open(SETTINGS_FILE, "w") as f:
            json.dump(self.settings, f, indent=2)

    def _clamp_all(self):
        for category, values in self.settings.items():
            if category in RANGES:
                for key, val in values.items():
                    if key in RANGES[category]:
                        lo, hi = RANGES[category][key]
                        values[key] = _clamp(val, lo, hi)

    def get(self, category, key):
        return self.settings.get(category, {}).get(key, DEFAULTS.get(category, {}).get(key))

    def set(self, category, key, value):
        if category in RANGES and key in RANGES[category]:
            lo, hi = RANGES[category][key]
            value = _clamp(value, lo, hi)
        if category not in self.settings:
            self.settings[category] = {}
        self.settings[category][key] = value

    def get_category(self, category):
        return dict(self.settings.get(category, DEFAULTS.get(category, {})))

    def reset_category(self, category):
        self.settings[category] = dict(DEFAULTS.get(category, {}))

    def reset_all(self):
        self.settings = {}
        for category, values in DEFAULTS.items():
            self.settings[category] = dict(values)
        self.save()

    def as_dict(self):
        """Return a flat dict of all settings for applying to game."""
        result = {}
        for category, values in self.settings.items():
            for key, val in values.items():
                result[key] = val
        return result


settings_manager = SettingsManager()

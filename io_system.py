"""Pythmc - IO System (V2.0) - Event-based triggers that execute OS commands"""

import os
import json
import subprocess

# Available conditions
IO_CONDITIONS = {
    "health_below": {"display": "Health Below", "type": "float", "min": 0, "max": 20},
    "health_above": {"display": "Health Above", "type": "float", "min": 0, "max": 20},
    "hunger_below": {"display": "Hunger Below", "type": "float", "min": 0, "max": 20},
    "hunger_above": {"display": "Hunger Above", "type": "float", "min": 0, "max": 20},
    "daytime_below": {"display": "Day Time Below", "type": "float", "min": 0, "max": 1},
    "daytime_above": {"display": "Day Time Above", "type": "float", "min": 0, "max": 1},
    "position_above_y": {"display": "Player Y Above", "type": "float", "min": -100, "max": 300},
    "position_below_y": {"display": "Player Y Below", "type": "float", "min": -100, "max": 300},
    "blocks_placed_above": {"display": "Blocks Placed Above", "type": "int", "min": 0, "max": 999999},
    "blocks_dug_above": {"display": "Blocks Dug Above", "type": "int", "min": 0, "max": 999999},
    "days_survived_above": {"display": "Days Survived Above", "type": "int", "min": 0, "max": 999999},
    "inventory_has": {"display": "Inventory Has Item ID", "type": "int", "min": 0, "max": 999},
}


class IOTigger:
    """A single IO trigger: condition + value -> command."""

    def __init__(self, condition_key="health_below", threshold=5.0, command="", enabled=True):
        self.condition_key = condition_key
        self.threshold = threshold
        self.command = command
        self.enabled = enabled
        self._last_fired = False

    def evaluate(self, game_state):
        """Check if condition is met. game_state is a dict with player/world stats."""
        if not self.enabled or not self.command:
            return False

        val = game_state.get(self.condition_key)
        if val is None:
            return False

        cond = IO_CONDITIONS.get(self.condition_key)
        if not cond:
            return False

        triggered = False
        if "below" in self.condition_key:
            triggered = val < self.threshold
        elif "above" in self.condition_key:
            triggered = val > self.threshold
        elif "has" in self.condition_key:
            triggered = val == self.threshold

        # Only fire once per trigger (rising edge)
        if triggered and not self._last_fired:
            self._last_fired = True
            return True
        elif not triggered:
            self._last_fired = False

        return False

    def fire(self):
        """Execute the OS command."""
        if not self.command:
            return False
        try:
            subprocess.Popen(
                self.command,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            return False

    def to_dict(self):
        return {
            "condition_key": self.condition_key,
            "threshold": self.threshold,
            "command": self.command,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            condition_key=data.get("condition_key", "health_below"),
            threshold=data.get("threshold", 5.0),
            command=data.get("command", ""),
            enabled=data.get("enabled", True),
        )


class IOManager:
    """Manages all IO triggers for a world."""

    def __init__(self):
        self.enabled = False
        self.triggers = []

    def add_trigger(self, trigger):
        self.triggers.append(trigger)

    def remove_trigger(self, index):
        if 0 <= index < len(self.triggers):
            self.triggers.pop(index)

    def update(self, game_state):
        """Check all triggers and fire any that match."""
        for trigger in self.triggers:
            if trigger.evaluate(game_state):
                trigger.fire()

    def to_list(self):
        return [t.to_dict() for t in self.triggers]

    def from_list(self, data):
        self.triggers = [IOTigger.from_dict(d) for d in data]

    def save_to_world(self, world_name):
        """Save IO config to world metadata."""
        import world_manager
        meta = world_manager.load_world_meta(world_name)
        if meta:
            meta["io_enabled"] = self.enabled
            meta["io_triggers"] = self.to_list()
            world_manager.save_world_meta(world_name, meta)

    def load_from_world(self, world_name):
        """Load IO config from world metadata."""
        import world_manager
        meta = world_manager.load_world_meta(world_name)
        if meta:
            self.enabled = meta.get("io_enabled", False)
            self.from_list(meta.get("io_triggers", []))


io_manager = IOManager()

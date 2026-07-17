"""Pythmc - Electronic Circuit Simulation System

Realistic electronics with:
- Voltage, current, resistance (Ohm's law)
- Series and parallel circuits
- Capacitor charging/discharging
- Transistor switching
- IC behavior (NE555, logic gates)
- Polarity protection (explodes if wrong!)
"""

import math
import random
import time
from constants import *


class CircuitNode:
    """A node in the circuit (wire connection point)."""
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.voltage = 0.0
        self.connected_components = []
        self.is_powered = False

    def __hash__(self):
        return hash((self.x, self.y, self.z))

    def __eq__(self, other):
        return (self.x, self.y, self.z) == (other.x, other.y, other.z)


class ElectronicComponent:
    """Base class for electronic components."""
    def __init__(self, comp_type, pos, polarity=0):
        self.type = comp_type
        self.pos = pos  # (x, y, z)
        self.polarity = polarity  # 0=none, 1=normal, -1=reversed
        self.voltage_across = 0.0
        self.current_through = 0.0
        self.is_active = False
        self.is_destroyed = False
        self.charge = 0.0  # For capacitors
        self.state = False  # For switches, relays

        props = COMPONENT_PROPERTIES.get(comp_type, ("unknown", 0, False, 0))
        self.category = props[0]
        self.value = props[1]
        self.polarity_required = props[2]
        self.max_voltage = props[3]

    def apply_voltage(self, voltage, polarity_correct=True):
        """Apply voltage to component. Returns True if OK, False if destroyed."""
        self.voltage_across = voltage

        # Check polarity
        if self.polarity_required and not polarity_correct:
            self.is_destroyed = True
            return False

        # Check max voltage
        if abs(voltage) > self.max_voltage:
            self.is_destroyed = True
            return False

        # Component-specific behavior
        if self.category == "resistor":
            # V = IR, so I = V/R
            if self.value > 0:
                self.current_through = voltage / self.value
            else:
                self.current_through = 0

        elif self.category == "capacitor":
            # Charging: V = V0 * (1 - e^(-t/RC))
            # For simulation, just track charge
            self.charge += voltage * 0.01  # Simplified charging
            self.charge = min(self.charge, self.max_voltage)

        elif self.category == "led":
            # LED has forward voltage drop
            if voltage >= self.value:
                self.is_active = True
                self.current_through = (voltage - self.value) / 100  # With current limiting resistor
            else:
                self.is_active = False

        elif self.category == "diode":
            # Forward voltage drop
            if voltage >= self.value:
                self.current_through = (voltage - self.value) / 1000
            else:
                self.current_through = 0

        elif self.category == "transistor":
            # NPN: Base current controls Collector-Emitter
            # PNP: Reversed
            if self.value == "NPN":
                self.is_active = voltage > 0.7  # Vbe threshold
            else:  # PNP
                self.is_active = voltage < -0.7

        return True

    def get_resistance(self):
        """Get component resistance."""
        if self.category == "resistor":
            return self.value
        elif self.category == "led":
            return 100  # Internal resistance
        elif self.category == "diode":
            return 1000 if not self.is_active else 10
        elif self.category == "capacitor":
            return 1000000 if self.charge < 0.1 else 100  # High when discharged
        return 1000000  # Very high for open circuits


class CircuitSimulator:
    """Simulates electronic circuits."""
    
    def __init__(self):
        self.components = {}  # pos -> ElectronicComponent
        self.wires = set()    # set of (x,y,z) positions
        self.power_sources = {}  # pos -> voltage
        self.update_timer = 0
        self.update_interval = 0.05  # 20 updates per second

    def add_component(self, comp_type, x, y, z, polarity=0):
        """Add a component to the circuit."""
        pos = (x, y, z)
        comp = ElectronicComponent(comp_type, pos, polarity)
        self.components[pos] = comp
        return comp

    def remove_component(self, x, y, z):
        """Remove a component."""
        pos = (x, y, z)
        if pos in self.components:
            del self.components[pos]

    def add_wire(self, x, y, z):
        """Add a wire segment."""
        self.wires.add((x, y, z))

    def remove_wire(self, x, y, z):
        """Remove a wire segment."""
        self.wires.discard((x, y, z))

    def add_power_source(self, x, y, z, voltage):
        """Add a battery/power source."""
        self.power_sources[(x, y, z)] = voltage

    def update(self, dt):
        """Update circuit simulation."""
        self.update_timer += dt
        if self.update_timer < self.update_interval:
            return []
        self.update_timer = 0

        events = []

        # Find connected circuits
        circuits = self._find_circuits()

        # Simulate each circuit
        for circuit in circuits:
            circuit_events = self._simulate_circuit(circuit)
            events.extend(circuit_events)

        return events

    def _find_circuits(self):
        """Find connected groups of components and wires."""
        visited = set()
        circuits = []

        # Start from each power source
        for pos in self.power_sources:
            if pos not in visited:
                circuit = self._flood_fill(pos, visited)
                if circuit:
                    circuits.append(circuit)

        return circuits

    def _flood_fill(self, start, visited):
        """Flood fill to find connected circuit."""
        queue = [start]
        circuit = {"wires": set(), "components": [], "power": []}

        while queue:
            pos = queue.pop(0)
            if pos in visited:
                continue
            visited.add(pos)

            x, y, z = pos

            # Check if it's a wire
            if pos in self.wires:
                circuit["wires"].add(pos)

            # Check if it's a component
            if pos in self.components:
                circuit["components"].append(self.components[pos])

            # Check if it's a power source
            if pos in self.power_sources:
                circuit["power"].append((pos, self.power_sources[pos]))

            # Check neighbors (6 directions)
            for dx, dy, dz in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]:
                neighbor = (x+dx, y+dy, z+dz)
                if neighbor not in visited:
                    if neighbor in self.wires or neighbor in self.components or neighbor in self.power_sources:
                        queue.append(neighbor)

        return circuit if (circuit["components"] or circuit["power"]) else None

    def _simulate_circuit(self, circuit):
        """Simulate a single circuit."""
        events = []

        if not circuit["power"]:
            return events

        # Calculate total voltage from power sources
        total_voltage = sum(v for _, v in circuit["power"])

        # Find all components in the circuit
        components = circuit["components"]
        if not components:
            return events

        # Calculate total resistance
        total_resistance = 0
        for comp in components:
            r = comp.get_resistance()
            if r > 0:
                total_resistance += r  # Series connection (simplified)

        if total_resistance <= 0:
            total_resistance = 1  # Prevent division by zero

        # Calculate current (I = V/R)
        total_current = total_voltage / total_resistance

        # Apply voltage to each component
        for comp in components:
            # Check polarity
            polarity_correct = True
            if comp.polarity_required:
                # Simplified polarity check
                if comp.type == CAPACITOR_ELECTRO or comp.type == CAPACITOR_TANTALUM:
                    # Electrolytic caps explode if reversed!
                    if comp.polarity == -1:
                        polarity_correct = False
                elif comp.type in (LED_RED_ITEM, LED_GREEN_ITEM, LED_BLUE_ITEM, LED_WHITE_ITEM):
                    # LEDs don't work reversed
                    if comp.polarity == -1:
                        polarity_correct = False

            # Apply voltage
            voltage = total_voltage * (comp.get_resistance() / total_resistance)
            ok = comp.apply_voltage(voltage, polarity_correct)

            if not ok:
                # Component destroyed!
                if comp.category == "capacitor" and comp.polarity_required:
                    events.append({
                        "type": "explosion",
                        "pos": comp.pos,
                        "reason": "wrong_polarity",
                        "message": "Electrolytic capacitor exploded! Wrong polarity!"
                    })
                else:
                    events.append({
                        "type": "component_destroyed",
                        "pos": comp.pos,
                        "reason": "overvoltage",
                        "message": f"{ITEM_NAMES.get(comp.type, 'Component')} destroyed by overvoltage!"
                    })

            # LED lighting
            if comp.category == "led" and comp.is_active:
                events.append({
                    "type": "led_on",
                    "pos": comp.pos,
                    "color": comp.type,
                })

        return events

    def get_component_at(self, x, y, z):
        """Get component at position."""
        return self.components.get((x, y, z))

    def is_wire_at(self, x, y, z):
        """Check if there's a wire at position."""
        return (x, y, z) in self.wires

    def clear(self):
        """Clear all circuit data."""
        self.components.clear()
        self.wires.clear()
        self.power_sources.clear()


# Global circuit simulator
circuit = CircuitSimulator()

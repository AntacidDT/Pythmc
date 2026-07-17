#!/usr/bin/env python3
"""
Pythmc - Minecraft Clone in Python
Launcher script - adds bundled dependencies to path

Just run: python3 run.py
No installation required!
"""

import sys
import os

# Add bundled lib to Python path (after system paths for numpy compat)
script_dir = os.path.dirname(os.path.abspath(__file__))
lib_dir = os.path.join(script_dir, 'lib')
sys.path.append(lib_dir)

# Now import and run the game
if __name__ == "__main__":
    from main import Game
    Game().run()

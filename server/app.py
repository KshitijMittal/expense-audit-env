# This file exists to satisfy the openenv validate server entry point requirement.
# The actual app is defined in main.py at the project root.
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

__all__ = ["app"]
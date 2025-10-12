"""
Path configuration untuk解决 import issues
"""

import os
import sys

# Add app directory to Python path
APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

# Also add parent directory untuk memastikan semua imports bekerja
PARENT_DIR = os.path.dirname(APP_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

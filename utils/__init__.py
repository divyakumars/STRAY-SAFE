# utils/__init__.py
"""
SafePaws AI Utility Modules
"""

# This file makes 'utils' a Python package
# Import key modules for easier access

from . import storage
from . import auth
from . import notify
from . import geo
from . import free_maps
from . import map_picker
from . import map_themes
from . import mobile
from . import offline

__all__ = [
    'storage',
    'auth',
    'notify',
    'geo',
    'free_maps',
    'map_picker',
    'map_themes',
    'mobile',
    'offline'
]

__version__ = "1.0.0"
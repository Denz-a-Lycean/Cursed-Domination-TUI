"""
Canonical gameplay and engine imports for the ANSI edition.

Implementation matches the integration plan's "core" layer; files live under
`systems/`, `models/`, and now `core.engine` for shared terminal UI plumbing.
"""

from models.enemy import Enemy
from models.player import Player
from .engine import BaseScreen, Button, Label, SceneScreen, TextBox, WindowManager
from systems.combat import CombatSystem, start_combat
from systems.game import INTRO_SCENES, STAGE_DATA, Game

__all__ = [
    "BaseScreen",
    "Button",
    "CombatSystem",
    "Enemy",
    "Game",
    "INTRO_SCENES",
    "Label",
    "Player",
    "SceneScreen",
    "STAGE_DATA",
    "TextBox",
    "WindowManager",
    "start_combat",
]

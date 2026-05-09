"""Canonical campaign route metadata and screen registration helpers."""

from __future__ import annotations

from core.engine import SceneScreen

from . import (
    gameplay_1_scene_tutorial,
    gameplay_2_scene_disturbance,
    gameplay_3_scene_pressure,
    gameplay_4_scene_chaos,
    gameplay_5_scene_boss,
    scene_01_intro,
    scene_02_timeskip,
    scene_03_kogane,
    scene_04_tutorial,
    scene_05_disturbance,
    scene_06_pressure_rise,
    scene_07_boss_entrance,
    scene_08_boss_defeat,
    scene_09_true_twist,
    scene_10_true_form,
    scene_11_ending,
)


STORY_SCENE_DEFS = (
    ("SCENE_01_INTRO", scene_01_intro.scene_data, "Scene 1: Intro"),
    ("SCENE_02_TIMESKIP", scene_02_timeskip.scene_data, "Scene 2: Timeskip"),
    ("SCENE_03_KOGANE", scene_03_kogane.scene_data, "Scene 3: Kogane"),
    ("SCENE_04_TUTORIAL", scene_04_tutorial.scene_data, "Scene 4: Tutorial"),
    ("SCENE_05_DISTURBANCE", scene_05_disturbance.scene_data, "Scene 5: Disturbance"),
    ("SCENE_06_PRESSURE", scene_06_pressure_rise.scene_data, "Scene 6: Pressure"),
    ("SCENE_07_BOSS_ENTRY", scene_07_boss_entrance.scene_data, "Scene 7: Boss Entry"),
    ("SCENE_08_BOSS_DEFEAT", scene_08_boss_defeat.scene_data, "Scene 8: Boss Defeat"),
    ("SCENE_09_TWIST", scene_09_true_twist.scene_data, "Scene 9: Twist"),
    ("SCENE_10_TRUE_FORM", scene_10_true_form.scene_data, "Scene 10: True Form"),
    ("SCENE_11_ENDING", scene_11_ending.scene_data, "Scene 11: Ending"),
)

GAMEPLAY_SCREEN_DEFS = (
    (1, "GAMEPLAY_01_TUTORIAL", gameplay_1_scene_tutorial.GameplayTutorialScreen, "Battle 1: Tutorial Anchor"),
    (2, "GAMEPLAY_02_DISTURBANCE", gameplay_2_scene_disturbance.GameplayDisturbanceScreen, "Battle 2: Disturbance Anchor"),
    (3, "GAMEPLAY_03_PRESSURE", gameplay_3_scene_pressure.GameplayPressureScreen, "Battle 3: Pressure Anchor"),
    (4, "GAMEPLAY_04_CHAOS", gameplay_4_scene_chaos.GameplayChaosScreen, "Battle 4: Distortion Anchor"),
    (5, "GAMEPLAY_05_BOSS", gameplay_5_scene_boss.GameplayBossScreen, "Battle 5: Special Grade Anchor"),
)

STORY_SCENE_SEQUENCE = tuple(key for key, _, _ in STORY_SCENE_DEFS)
GAMEPLAY_SCREEN_KEYS = tuple(key for _, key, _, _ in GAMEPLAY_SCREEN_DEFS)
STAGE_TO_GAMEPLAY_STATE = {stage: key for stage, key, _, _ in GAMEPLAY_SCREEN_DEFS}
STORY_SCENE_MENU_ENTRIES = tuple((label, key) for key, _, label in STORY_SCENE_DEFS)

# Explicit campaign ordering: 11 story scenes supported by 5 anchor battles.
CAMPAIGN_FLOW = (
    {"kind": "scene", "key": "SCENE_01_INTRO", "chapter": "Prologue"},
    {"kind": "scene", "key": "SCENE_02_TIMESKIP", "chapter": "Prologue"},
    {"kind": "scene", "key": "SCENE_03_KOGANE", "chapter": "Prologue"},
    {"kind": "scene", "key": "SCENE_04_TUTORIAL", "chapter": "Tutorial Setup"},
    {"kind": "battle", "key": "GAMEPLAY_01_TUTORIAL", "stage": 1, "chapter": "Tutorial Anchor"},
    {"kind": "scene", "key": "SCENE_05_DISTURBANCE", "chapter": "Disturbance"},
    {"kind": "battle", "key": "GAMEPLAY_02_DISTURBANCE", "stage": 2, "chapter": "Disturbance Anchor"},
    {"kind": "scene", "key": "SCENE_06_PRESSURE", "chapter": "Pressure Rise"},
    {"kind": "battle", "key": "GAMEPLAY_03_PRESSURE", "stage": 3, "chapter": "Pressure Anchor"},
    {"kind": "battle", "key": "GAMEPLAY_04_CHAOS", "stage": 4, "chapter": "Distortion Anchor"},
    {"kind": "scene", "key": "SCENE_07_BOSS_ENTRY", "chapter": "Boss Arrival"},
    {"kind": "battle", "key": "GAMEPLAY_05_BOSS", "stage": 5, "chapter": "Special Grade Anchor"},
    {"kind": "scene", "key": "SCENE_08_BOSS_DEFEAT", "chapter": "Aftermath"},
    {"kind": "scene", "key": "SCENE_09_TWIST", "chapter": "False Victory"},
    {"kind": "scene", "key": "SCENE_10_TRUE_FORM", "chapter": "True Form"},
    {"kind": "scene", "key": "SCENE_11_ENDING", "chapter": "Ending"},
)


def gameplay_state_for_stage(stage: int) -> str:
    """Return the canonical gameplay screen key for a saved/checkpoint stage."""
    return STAGE_TO_GAMEPLAY_STATE.get(int(stage), "SCREEN_MAIN_MENU")


def build_campaign_screens(window, state) -> dict[str, object]:
    """Construct the registered story and gameplay screens for the shell."""
    screens = {
        key: SceneScreen(window, scene_data, state=state)
        for key, scene_data, _ in STORY_SCENE_DEFS
    }
    for _, key, screen_class, _ in GAMEPLAY_SCREEN_DEFS:
        screens[key] = screen_class(window, state)
    return screens

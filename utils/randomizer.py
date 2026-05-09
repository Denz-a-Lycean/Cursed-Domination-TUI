"""Centralized wrappers around `random` used by combat and visual effects."""

import random


def randint(minimum, maximum):
    """Return an integer in the inclusive range after normalizing inputs."""
    return random.randint(int(minimum), int(maximum))


def choice(options):
    """Pick one value from any iterable by converting it into a list first."""
    return random.choice(list(options))


def seeded_random(seed):
    """Create a reusable deterministic RNG for repeatable glitch frames."""
    return random.Random(seed)


def roll_chance(percent):
    """Return True when a percentage roll succeeds."""
    return randint(1, 100) <= int(percent)


def damage_roll(minimum, maximum):
    """Small semantic wrapper used by combat damage calculations."""
    return randint(minimum, maximum)


def choose_enemy_action(current_hp, max_hp):
    """Legacy helper for simple low-HP behavior weighting."""
    if current_hp <= max_hp * 0.3:
        return choice(["attack", "desperate_attack"])
    return choice(["attack", "attack", "desperate_attack"])

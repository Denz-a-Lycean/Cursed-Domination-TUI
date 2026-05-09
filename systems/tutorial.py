"""Simple guided tutorial flow that walks the player through basic actions.

The tutorial uses the presenter's screens to narrate steps and performs a
small scripted encounter with a weak curse so players can try Attack,
Defend, and see Domain Expansion in action.
"""

from models.enemy import Enemy


def run_tutorial(game):
    """Execute a short, forced tutorial connected to the provided Game.

    This function is intentionally small and avoids the full combat loop so
    the player can learn without risking a failed stage.
    """
    presenter = game.presenter
    player = game.player

    # Intro guidance from Kogane
    presenter.screen(
        "Kogane: Training",
        [
            'Kogane: "Ding-dong... Welcome, sorcerer. Let me teach you how to survive."',
            "",
            "In this short lesson you'll:",
            " - Attack the weak curse",
            " - Try defending",
            " - See what Domain Expansion does",
        ],
        status_lines=game._status_lines(),
    )
    presenter.stop(None)

    # Create a weak tutorial enemy (stage data already defines a weak one,
    # but build a local instance so we can control flavor and avoid full loop).
    enemy = Enemy("Training Curse", hp=30, attack=4, enemy_type="weak", stage=1)

    # Step 1: Attack only
    presenter.screen(
        "Kogane: Try attacking the curse.",
        ["Only option: Attack"],
        status_lines=game._status_lines(),
    )
    presenter.stop(None)

    attack_result = player.perform_attack(enemy)
    presenter.screen(
        "Attack",
        [attack_result["message"], f"{enemy.name} has {enemy.hp}/{enemy.max_hp} HP left."],
        status_lines=game._status_lines(),
    )
    presenter.stop(None)

    # Step 2: Defend
    presenter.screen(
        "Kogane: Now, defend.",
        ["Press Enter to defend and gain a small Domain charge."],
        status_lines=game._status_lines(),
    )
    presenter.stop(None)

    gained = player.defend()
    presenter.screen(
        "Defending",
        [
            f"You brace yourself. Incoming damage will be reduced.",
            f"Domain increased by {gained}%.",
        ],
        status_lines=game._status_lines(),
    )
    presenter.stop(None)

    # Step 3: Show Domain
    presenter.screen(
        "Kogane: Your Domain builds as you fight...",
        ["We'll demonstrate Domain Expansion now."],
        status_lines=game._status_lines(),
    )
    presenter.stop(None)

    # Force-full domain for demonstration, then activate it.
    player.domain_meter = 100
    domain_result = player.use_domain(enemy)
    lines = [domain_result["message"]]
    lines.extend(domain_result.get("lines", []))
    lines.append(f"{enemy.name} has {enemy.hp}/{enemy.max_hp} HP left.")
    presenter.screen("Domain Demonstration", lines, status_lines=game._status_lines())
    presenter.stop(None)

    presenter.screen(
        "Kogane: Training Complete",
        ["Kogane: \"You are ready.\"", "Start Stage 1 when you're prepared."],
        status_lines=game._status_lines(),
    )
    presenter.stop(None)

"""Turn-based combat coordinator for the player, enemy, and presenter."""

import time

from utils.effects import format_duration

# UX tuning constants
DOMAIN_SELECTION_WINDOW = 20.0  # seconds for the player selection window inside a domain
DOMAIN_POST_ATTACK_ANIMATION = 15.0  # seconds for post-attack domain animation


class CombatSystem:
    def __init__(self, player, enemy, presenter, game=None):
        """
        Initializes combat with player, enemy, and presentation adapter.
        """
        self.player = player
        self.enemy = enemy
        self.presenter = presenter
        self.game = game
        self.battle_start_time = time.monotonic()

    def _play_attack_animation(
        self,
        title,
        attacker_name,
        defender_name,
        attack_name,
        seconds=1.0,
        shake=False,
        defender_defending=False,
        indicator_label=None,
    ):
        """
        Play attack animation when supported by presenter.

        Test presenters may not implement advanced animation hooks, so this
        gracefully falls back to the existing loading transition.
        """
        if hasattr(self.presenter, "attack_animation"):
            self.presenter.attack_animation(
                title,
                attacker_name=attacker_name,
                defender_name=defender_name,
                attack_name=attack_name,
                defender_defending=defender_defending,
                indicator_label=indicator_label,
                status_lines=self._status_lines,
                status_data=self._status_data,
                seconds=seconds,
                shake=shake,

            )
            return

        self.presenter.loading(
            title,
            f"{attacker_name} attacks {defender_name} with {attack_name}.",
            status_lines=self._status_lines(),
            seconds=max(0.8, seconds),
        )

    def _show_battle_message(self, title, lines, seconds=1.0, side_title="ACTIVITY"):
        """Render short inline combat updates without swapping away from the battlefield."""
        lines = [str(line) for line in (lines or []) if line is not None]
        if hasattr(self.presenter, "battle_message"):
            message = " ".join(lines[:2]) if lines else ""
            side_lines = lines[:3] if lines else []
            self.presenter.battle_message(
                title,
                message,
                status_lines=self._status_lines(),
                seconds=seconds,
                side_lines=side_lines,
                side_title=side_title,
            )
            return

        self.presenter.screen(title, lines, status_lines=self._status_lines())

    def _play_domain_timer(
        self,
        title,
        attacker_name,
        defender_name,
        domain_name,
        technique_key,
        duration_seconds=30.0,
        interval=0.15,
    ):
        """Play domain expansion timer when supported by presenter."""
        if hasattr(self.presenter, "domain_expansion_animation"):
            self.presenter.domain_expansion_animation(
                title=title,
                attacker_name=attacker_name,
                defender_name=defender_name,
                domain_name=domain_name,
                technique_key=technique_key,
                status_lines=self._status_lines,
                status_data=self._status_data,
                duration_seconds=duration_seconds,
                interval=interval,

            )
            return

        # Fallback for test/manual presenters (avoid long waits).
        self.presenter.loading(
            title,
            "DOMAIN EXPANSION!!!",
            status_lines=self._status_lines(),
            seconds=0.6,
        )

    def _play_domain_attack_animation(
        self,
        title,
        attacker_name,
        defender_name,
        domain_name,
        technique_key,
        seconds=1.2,
    ):
        """Play domain hit animation when supported by presenter."""
        if hasattr(self.presenter, "domain_attack_animation"):
            self.presenter.domain_attack_animation(
                title=title,
                attacker_name=attacker_name,
                defender_name=defender_name,
                domain_name=domain_name,
                technique_key=technique_key,
                status_lines=self._status_lines,
                status_data=self._status_data,
                seconds=seconds,
                shake=False,

            )
            return

        # Fallback: use the regular attack animation hook if available.
        self._play_attack_animation(
            title,
            attacker_name=attacker_name,
            defender_name=defender_name,
            attack_name="DOMAIN ATTACK",
            seconds=seconds,
            shake=False,
        )

    def _apply_domain_passive_effect(self, technique_key):
        """Apply domain staying effects when player chooses Defend."""
        if technique_key == "Dancer":
            # Drains cursed energy over time: lower enemy attack.
            self.enemy.attack = max(1, self.enemy.attack - 3)
        elif technique_key == "Bouncer":
            # Sound erased: next enemy action is disrupted.
            self.enemy.skip_next_turn = True
        else:  # Seeker
            # Copies pressure: weakens enemy slightly.
            self.enemy.attack = max(1, self.enemy.attack - 2)

    def start_battle(self):
        """Main combat loop. Returns 'WIN' or 'LOSE'."""
        self.presenter.screen(
            "Battle Start",
            [f"{self.enemy.name} appeared."],
            status_lines=self._status_lines(),
        )
        self.presenter.loading(
            "Battle Start",
            f"{self.enemy.name} is entering the battlefield.",
            status_lines=self._status_lines(),
            seconds=2.0,
        )

        while self.player.is_alive() and self.enemy.is_alive():
            turn_result = self.player_turn()
            if turn_result == "ESCAPE":
                return "ESCAPE"

            if not self.enemy.is_alive():
                self.presenter.screen(
                    "Battle Won",
                    [f"You defeated {self.enemy.name}."],
                    status_lines=self._status_lines(),
                )
                self.presenter.loading(
                    "Battle Won",
                    "Preparing the next result screen.",
                    status_lines=self._status_lines(),
                    seconds=1.8,
                )
                return "WIN"

            self.enemy_turn()

            if not self.player.is_alive():
                self.presenter.screen(
                    "Battle Lost",
                    ["You were defeated."],
                    status_lines=self._status_lines(),
                )
                self.presenter.loading(
                    "Battle Lost",
                    "Processing the aftermath of battle.",
                    status_lines=self._status_lines(),
                    seconds=1.8,
                )
                return "LOSE"

    def _status_data(self):
        """Structured HUD data for the presenter (no regex parsing required)."""
        battle_time = time.monotonic() - self.battle_start_time
        stage_number = self.game.current_stage if self.game else self.enemy.stage
        return {
            "battle_time": format_duration(battle_time),
            "player_name": self.player.name,
            "player_class": self.player.player_class,
            "hp": self.player.hp,
            "hp_max": self.player.max_hp,
            "domain": self.player.domain_meter,
            "instability": self.player.mental_instability,
            "defending": bool(self.player.defending),
            "enemy_name": self.enemy.name,
            "enemy_type": self.enemy.enemy_type,
            "stage": stage_number,
            "enemy_hp": self.enemy.hp,
            "enemy_max": self.enemy.max_hp,
        }

    def _status_lines(self):
        """Backward-compatible legacy HUD lines (used only if presenter expects strings)."""
        d = self._status_data()
        defend_tag = " [DEFENDING]" if d.get("defending") else ""
        return [
            f"Battle Time: {d['battle_time']}",
            f"Player: {d['player_name']} ({d['player_class']}) | HP {d['hp']}/{d['hp_max']} | Domain {d['domain']}% | Instability {d['instability']}{defend_tag}",
            f"Enemy: {d['enemy_name']} | Type {d['enemy_type']} | Stage {d['stage']} | Enemy HP {d['enemy_hp']}/{d['enemy_max']}",
        ]


    def player_turn(self):
        """Handle player action selection until a turn is consumed."""
        while True:
            choice = self.presenter.menu(
                "Your Turn",
                ["Attack", "Defend", "Domain Expansion", "Inventory"],
                status_callback=self._status_lines,
                allow_escape=True,
                help_text="Arrows: move   Enter: confirm   Esc: quit battle",
            )
            if choice is None:
                confirm = self.presenter.menu(
                    "Pause",
                    ["Resume", "Quit Battle"],
                    status_callback=self._status_lines,
                    allow_escape=True,
                    help_text="Esc: resume",
                )
                if confirm is None or confirm == 0:
                    continue
                return "ESCAPE"

            if choice == 0 and self.attack_menu():
                return
            if choice == 1:
                self._do_defend()
                return
            if choice == 2 and self.use_domain():
                return
            if choice == 3 and self.inventory_menu():
                return

    def _do_defend(self):
        gained = self.player.defend()
        self._show_battle_message(
            "Defending",
            [
                f"{self.player.name} braces for the next attack.",
                "Incoming damage will be reduced by 50%.",
                f"You focus your cursed energy. Domain +{gained}%.",
            ],
            seconds=1.1,
            side_title="STANCE",
        )
        self.presenter.loading(
            "Defend",
            f"{self.player.name} is taking a defensive stance.",
            status_lines=self._status_lines(),
            seconds=0.7,
        )

    def attack_menu(self):
        """Skill selection under Attack. Returns True when a skill is used."""
        while True:
            options = [f"{skill.name} - {skill.description}" for skill in self.player.skills]
            options.append("Back")
            choice = self.presenter.menu(
                "Attack Menu",
                options,
                status_callback=self._status_lines,
                allow_escape=True,
                help_text="Esc: back",
            )
            if choice is None:
                return False

            if choice == len(self.player.skills):
                return False

            selected_skill = self.player.skills[choice]
            is_third_skill = choice == 2
            self._play_attack_animation(
                "Attack Phase",
                attacker_name=self.player.name,
                defender_name=self.enemy.name,
                attack_name=selected_skill.name,
                seconds=1.25 if is_third_skill else 0.95,
                shake=is_third_skill,
            )

            result = self.player.use_skill(choice, self.enemy)
            lines = [result["message"]]
            lines.extend(result.get("lines", []))
            if result["damage"] > 0:
                lines.append(f"{self.enemy.name} took {result['damage']} damage.")

            self._show_battle_message("Skill Used", lines, seconds=1.15, side_title="RESULT")
            return bool(result["success"])

    def inventory_menu(self):
        """Item selection menu. Returns True when the turn is consumed."""
        while True:
            if self.player.inventory.is_empty():
                self._show_battle_message(
                    "Inventory",
                    ["Inventory is empty.", "Returning to the combat menu."],
                    seconds=0.9,
                    side_title="INVENTORY",
                )
                return False

            grouped_items = self.player.inventory.grouped_entries()
            options = [entry["label"] for entry in grouped_items]
            options.append("Back")
            choice = self.presenter.menu(
                "Inventory",
                options,
                status_callback=self._status_lines,
                allow_escape=True,
                help_text="Esc: back",
            )
            if choice is None:
                return False

            if choice == len(grouped_items):
                return False

            result = self.player.inventory.use_grouped_item(choice, self.player)
            if result and result.get("success"):
                self._play_attack_animation(
                    "Item Use",
                    attacker_name=self.player.name,
                    defender_name=self.enemy.name,
                    attack_name="Item",
                    seconds=0.9,
                    shake=False,
                    indicator_label="APPLYING ITEM",
                )
                self._show_battle_message(
                    "Item Used",
                    [result["message"], "Item effect applied successfully."],
                    seconds=1.0,
                    side_title="ITEM",
                )
                return True

            self._show_battle_message(
                "Item Failed",
                [result["message"] if result else "Could not use that item right now.", "The enemy still gets a turn."],
                seconds=0.95,
                side_title="ITEM",
            )
            # Selecting an item consumes the player's turn even if it fails.
            # This keeps risk consistent: item attempts still let the enemy act.
            return True

    def use_domain(self):
        """Activate Domain Expansion when ready."""
        if self.player.domain_meter < 100:
            self._show_battle_message(
                "Domain Expansion",
                [
                    "Domain not ready.",
                    f"Current domain meter: {self.player.domain_meter}% / 100%",
                    "Use skills or defend to build more cursed energy.",
                ],
                seconds=1.0,
                side_title="DOMAIN",
            )
            return False

        # Domain actions decide your immediate stance. Clear carry-over so it
        # doesn't affect the post-domain enemy attack.
        self.player.defending = False

        technique_key = self.player.player_class  # "Dancer" | "Bouncer" | "Seeker"
        domain_name = self.player.domain_name

        # Initial domain flash before the Defend/Attack choice.
        if hasattr(self.presenter, "domain_activation_animation"):
            self.presenter.domain_activation_animation(
                title="Domain Expansion",
                attacker_name=self.player.name,
                defender_name=self.enemy.name,
                domain_name=domain_name,
                technique_key=technique_key,
                status_lines=self._status_lines,
                seconds=1.1,
                interval=0.09,
            )
        else:
            self.presenter.loading(
                "Domain Expansion",
                "DOMAIN EXPANSION!!!",
                status_lines=self._status_lines(),
                seconds=0.6,
            )

        action_index = self.presenter.menu(
            "Domain Expansion",
            ["Defend", "Attack"],
            status_callback=self._status_lines,
            allow_escape=True,
            help_text=f"Enemy acts after the {int(DOMAIN_SELECTION_WINDOW)}s domain timer ends.",
        )
        if action_index is None:
            return False

        choosing_attack = action_index == 1
        choosing_defend = not choosing_attack

        if choosing_defend:
            self.player.defending = True
            self._show_battle_message(
                "Defending",
                [
                    "You hold your stance inside the expanding domain.",
                    "The enemy can't move until the timer runs out.",
                ],
                seconds=0.9,
                side_title="DOMAIN",
            )
        else:
            # Domain attack: heavy hit with an extended domain animation.
            self._play_domain_attack_animation(
                "Domain Attack",
                attacker_name=self.player.name,
                defender_name=self.enemy.name,
                domain_name=domain_name,
                technique_key=technique_key,
                seconds=DOMAIN_POST_ATTACK_ANIMATION,
            )

            # Resolve the domain hit. We delay consuming domain_meter until
            # after the 30s timer so the HUD behaves as requested.
            result = self.player._domain_effect(self.enemy)
            lines = [result.get("message", "Domain attack initiated.")]
            lines.extend(result.get("lines", []))
            if result.get("damage", 0) > 0:
                lines.append(f"{self.enemy.name} took {result['damage']} damage.")
            self._show_battle_message("Domain Attack Resolved", lines, seconds=0.95, side_title="DOMAIN")

        # Domain selection window: enemy turn happens after it completes.
        self._play_domain_timer(
            "Domain Expansion",
            attacker_name=self.player.name,
            defender_name=self.enemy.name,
            domain_name=domain_name,
            technique_key=technique_key,
            duration_seconds=DOMAIN_SELECTION_WINDOW,
            interval=0.15,
        )

        # Domain ends after the timer.
        self.player.domain_meter = 0

        # Defensive-only 'staying' effects (no extra damage).
        if choosing_defend:
            self._apply_domain_passive_effect(technique_key)
            self._show_battle_message(
                "Domain Effect",
                [
                    "The domain collapses.",
                    "The enemy is left weakened by your sustained presence.",
                ],
                seconds=0.8,
                side_title="DOMAIN",
            )

        return True

    def enemy_turn(self):
        """Enemy action logic."""
        if self.enemy.skip_next_turn:
            self.player.defending = False
            self.enemy.skip_next_turn = False
            self._show_battle_message(
                "Enemy Turn",
                [f"{self.enemy.name} is frozen and loses the turn.", "Controls will return on your next action."],
                seconds=1.0,
                side_title="ENEMY TURN",
            )
            return

        # Capture stance BEFORE applying damage, because `perform_attack()`
        # will clear `target.defending` after mitigating.
        defender_was_defending = bool(self.player.defending)
        result = self.enemy.perform_attack(self.player)
        self._play_attack_animation(
            "Enemy Attack",
            attacker_name=self.enemy.name,
            defender_name=self.player.name,
            attack_name=result.get("action", "attack").replace("_", " ").title(),
            seconds=1.0,
            shake=False,
            defender_defending=defender_was_defending,
        )
        if result.get("action") == "boss_regen":
            lines = [result["message"], f"{self.enemy.name} HP is now {self.enemy.hp}/{self.enemy.max_hp}."]
        else:
            lines = [result["message"], f"Damage dealt: {result['damage']}."]
        self._show_battle_message("Enemy Turn", lines, seconds=1.15, side_title="ENEMY TURN")


def start_combat(player, enemy, presenter, game=None):
    """Convenience wrapper used by the game loop to launch a battle."""
    combat = CombatSystem(player, enemy, presenter, game)
    return combat.start_battle()

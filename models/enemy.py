"""Enemy model with stage-aware action selection and combat results."""

from models.character import Character
from utils.randomizer import choice, damage_roll, roll_chance


class Enemy(Character):
    """
    Enemy class with stage-aware AI.
    """

    def __init__(self, name, hp, attack, enemy_type="weak", stage=1):
        super().__init__(name, hp, attack)
        # Enemy type and stage let the AI scale behavior without creating a new
        # subclass for every single encounter in the campaign.
        self.enemy_type = enemy_type
        self.stage = max(1, int(stage))
        self.skip_next_turn = False
        self.last_action = "attack"
        self.turn_count = 0

    def decide_action(self):
        """Choose an action based on enemy type, stage, and current HP."""
        low_hp = self.hp <= self.max_hp * 0.3
        actions = self._action_pool(low_hp)
        return choice(actions)

    def _action_pool(self, low_hp):
        """
        Return the weighted action list used by the enemy AI.

        The pool changes with both HP and stage so later encounters feel more
        threatening without needing entirely separate enemy classes for every
        phase of the campaign.
        """
        if self.enemy_type == "boss":
            if self.turn_count > 0 and (self.turn_count + 1) % 3 == 0:
                return ["special_grade_burst"]
            if low_hp and roll_chance(50):
                return ["desperate_attack"]
            return ["attack", "attack", "silencing_strike"]

        if self.enemy_type == "elite":
            if low_hp:
                actions = ["desperate_attack", "pressure_strike"]
                if self.stage >= 4:
                    actions.append("pressure_strike")
                return actions
            actions = ["attack", "pressure_strike", "pressure_strike"]
            if self.stage >= 4:
                actions.append("desperate_attack")
            return actions

        if self.enemy_type == "aggressive":
            if low_hp:
                actions = ["desperate_attack", "desperate_attack", "pressure_strike"]
                if self.stage >= 3:
                    actions.append("pressure_strike")
                return actions
            actions = ["attack", "pressure_strike", "desperate_attack"]
            if self.stage >= 3:
                actions.append("pressure_strike")
            return actions

        if self.enemy_type == "fast":
            if low_hp:
                actions = ["swift_attack", "desperate_attack"]
                if self.stage >= 4:
                    actions.append("pressure_strike")
                return actions
            actions = ["attack", "swift_attack", "swift_attack"]
            if self.stage >= 4:
                actions.append("pressure_strike")
            return actions

        if low_hp:
            actions = ["attack", "desperate_attack"]
            if self.stage >= 2:
                actions.append("desperate_attack")
            return actions
        return ["attack"]

    def perform_attack(self, target, action=None):
        """Polymorphic Character attack with enemy-specific randomness."""
        # Stage 5 boss can occasionally heal instead of attacking.
        if self.enemy_type == "boss" and self.stage >= 5 and self.hp < self.max_hp and roll_chance(25):
            heal_amount = max(15, self.max_hp // 10)
            previous_hp = self.hp
            self.heal(heal_amount)
            restored = self.hp - previous_hp
            self.last_action = "boss_regen"
            self.turn_count += 1
            return {
                "success": True,
                "damage": 0,
                "healed": restored,
                "message": f"{self.name} absorbs cursed energy and heals {restored} HP.",
                "action": "boss_regen",
            }

        action = action or self.decide_action()
        self.last_action = action
        self.turn_count += 1

        damage_ranges = {
            "attack": (self.attack - 2, self.attack + 2),
            "swift_attack": (self.attack - 1, self.attack + 3),
            "pressure_strike": (self.attack + 1, self.attack + 5),
            "desperate_attack": (self.attack + 3, self.attack + 7),
            "silencing_strike": (self.attack + 2, self.attack + 6),
            "special_grade_burst": (self.attack + 6, self.attack + 10),
        }
        minimum, maximum = damage_ranges.get(action, damage_ranges["attack"])
        damage = damage_roll(max(1, minimum), max(1, maximum))

        if target.defending:
            damage = damage // 2
            target.defending = False

        target.take_damage(damage)

        message_map = {
            "attack": f"{self.name} attacks without hesitation.",
            "swift_attack": f"{self.name} darts forward in a blur.",
            "pressure_strike": f"{self.name} unleashes a crushing strike.",
            "desperate_attack": f"{self.name} lashes out in desperation.",
            "silencing_strike": f"{self.name} warps the air with a silent blow.",
            "special_grade_burst": f"{self.name} releases special grade pressure.",
        }
        return {
            "success": True,
            "damage": damage,
            "message": message_map.get(action, f"{self.name} attacks."),
            "action": action,
        }

    def __str__(self):
        """Return a concise overview of the enemy's combat identity."""
        return (
            f"Enemy(name={self.name}, type={self.enemy_type}, stage={self.stage}, "
            f"hp={self.hp}/{self.max_hp}, attack={self.attack})"
        )

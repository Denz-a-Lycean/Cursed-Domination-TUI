"""Skill models that package combat effects into structured payloads."""

from abc import ABC, abstractmethod


class Skill(ABC):
    """
    Abstract skill contract.
    """

    def __init__(self, name, description=""):
        self._name = name
        self._description = description

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description

    @abstractmethod
    def use(self, user, target):
        """
        Execute the skill effect.
        """

    def _base_result(self, message=None):
        """Return the baseline response shape used by every skill."""
        return {
            "success": True,
            "damage": 0,
            "message": message or self.description or f"{self.name} takes effect.",
            "lines": [],
            "bonus_domain": 0,
        }

    def __str__(self):
        """Return a concise skill label suitable for menus and debug output."""
        return f"{self.name}: {self.description}" if self.description else self.name


class DamageSkill(Skill):
    def __init__(self, name, damage, description="", bonus_domain=0):
        super().__init__(name, description)
        self._damage = max(0, int(damage))
        self._bonus_domain = max(0, int(bonus_domain))

    @property
    def damage(self):
        return self._damage

    def use(self, user, target):
        """Apply a fixed amount of damage to the chosen target."""
        target.take_damage(self.damage)
        result = self._base_result()
        result["damage"] = self.damage
        result["bonus_domain"] = self._bonus_domain
        return result


class MultiHitSkill(Skill):
    def __init__(self, name, hits, damage_per_hit, description="", bonus_domain=0):
        super().__init__(name, description)
        self._hits = max(1, int(hits))
        self._damage_per_hit = max(0, int(damage_per_hit))
        self._bonus_domain = max(0, int(bonus_domain))

    def use(self, user, target):
        """Apply repeated fixed hits and report the total damage dealt."""
        total_damage = self._hits * self._damage_per_hit
        target.take_damage(total_damage)
        result = self._base_result(
            f"{self.name} lands {self._hits} crushing hits."
        )
        result["damage"] = total_damage
        result["bonus_domain"] = self._bonus_domain
        result["lines"].append(
            f"Total damage: {total_damage} ({self._hits} x {self._damage_per_hit})."
        )
        return result


class EffectSkill(Skill):
    def __init__(self, name, description="", effect=None, damage=0, bonus_domain=0):
        super().__init__(name, description)
        self._effect = effect
        self._damage = max(0, int(damage))
        self._bonus_domain = max(0, int(bonus_domain))

    def use(self, user, target):
        """Resolve optional flat damage first, then apply the custom effect."""
        result = self._base_result()
        result["bonus_domain"] = self._bonus_domain

        if self._damage > 0:
            target.take_damage(self._damage)
            result["damage"] += self._damage

        if self._effect:
            effect_result = self._effect(user, target) or {}
            if isinstance(effect_result, dict):
                result["damage"] += max(0, int(effect_result.get("damage", 0)))
                if effect_result.get("message"):
                    result["message"] = effect_result["message"]
                result["lines"].extend(effect_result.get("lines", []))

        return result

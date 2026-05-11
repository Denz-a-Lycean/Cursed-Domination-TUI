"""Item models that return structured results to the combat UI."""

from abc import ABC, abstractmethod


class Item(ABC):
    """
    Abstract item contract.
    """

    def __init__(self, name):
        # Item names are shown directly in the inventory menu and save data.
        self._name = name

    @property
    def name(self):
        return self._name

    @abstractmethod
    def apply(self, player):
        """
        Apply the item effect to the player.
        """

    def _result(self, success, message, damage=0):
        """Build a consistent payload for callers such as combat/inventory UI."""
        return {
            "success": bool(success),
            "damage": max(0, int(damage)),
            "message": message,
        }

    def __str__(self):
        """Return the display name so logs and menus stay readable."""
        return self.name


class HealItem(Item):
    def __init__(self):
        super().__init__("Healing Potion")

    def apply(self, player):
        """Restore HP unless the player's health is already full."""
        if player.hp >= player.max_hp:
            return self._result(False, "Your HP is already full.")

        heal_amount = 30
        previous_hp = player.hp
        player.heal(heal_amount)
        restored = player.hp - previous_hp
        return self._result(True, f"Healed {restored} HP.")


class DomainChargeItem(Item):
    def __init__(self):
        super().__init__("Domain Shard")

    def apply(self, player):
        """Recharge domain energy unless the meter is already capped."""
        if player.domain_meter >= 100:
            return self._result(False, "Your domain meter is already full.")

        previous_meter = player.domain_meter
        player.domain_meter += 25
        restored = player.domain_meter - previous_meter
        return self._result(True, f"Domain meter increased by {restored}.")


class AttackBoostItem(Item):
    def __init__(self):
        super().__init__("Cursed Talisman")

    def apply(self, player):
        """Provide a simple permanent attack increase for the current run."""
        boost_amount = 4
        player.attack += boost_amount
        return self._result(True, f"Attack increased by {boost_amount}.")


ITEM_REGISTRY = {
    "HealItem": HealItem,
    "DomainChargeItem": DomainChargeItem,
    "AttackBoostItem": AttackBoostItem,
}

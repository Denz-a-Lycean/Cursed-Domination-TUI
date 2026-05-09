"""Core abstract model shared by all battle participants."""

from abc import ABC, abstractmethod


class Character(ABC):
    """
    Abstract parent for all combat units.
    """

    def __init__(self, name, hp, attack):
        # Store the shared combat stats behind protected attributes so subclasses
        # can reuse the validation logic exposed through properties.
        self._name = name
        self._max_hp = max(1, hp)
        self._hp = max(0, hp)
        self._attack = max(1, attack)

    @property
    def name(self):
        return self._name

    @property
    def hp(self):
        return self._hp

    @hp.setter
    def hp(self, value):
        self._hp = max(0, min(int(value), self.max_hp))

    @property
    def max_hp(self):
        return self._max_hp

    @max_hp.setter
    def max_hp(self, value):
        self._max_hp = max(1, int(value))
        self._hp = min(self._hp, self._max_hp)

    @property
    def attack(self):
        return self._attack

    @attack.setter
    def attack(self, value):
        self._attack = max(1, int(value))

    def is_alive(self):
        """Return True while the character still has HP remaining."""
        return self.hp > 0

    def take_damage(self, damage):
        """Reduce HP while preserving the lower bound enforced by `hp`."""
        self.hp -= max(0, int(damage))

    def heal(self, amount):
        """Restore HP while respecting the character's max HP."""
        self.hp += max(0, int(amount))

    def __str__(self):
        """Summarize the most important combat stats for logs and debugging."""
        return (
            f"{self.__class__.__name__}("
            f"name={self.name}, hp={self.hp}/{self.max_hp}, attack={self.attack})"
        )

    @abstractmethod
    def perform_attack(self, target):
        """
        Polymorphic attack behavior implemented by subclasses.
        """

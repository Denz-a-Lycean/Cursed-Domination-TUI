"""Player model containing progression, skills, inventory, and save helpers."""

from models.character import Character
from models.item import AttackBoostItem, DomainChargeItem, HealItem, ITEM_REGISTRY
from models.skill import DamageSkill, EffectSkill, MultiHitSkill
from systems.inventory import Inventory
from utils.randomizer import randint


# Centralized class data keeps the Player constructor small and makes balance
# changes easier because skill/domain definitions live in one place.
CLASS_PROFILES = {
    "Dancer": {
        "character_name": "JC",
        "domain_name": "D.D.A: Death Dancing Arena",
        "domain_desc": "Traps the opponent. Continuously drains their cursed energy over time. The longer they stay, the weaker they become.",
        "skills": lambda player: [
            DamageSkill(
                "Punch",
                12,
                "A straightforward but powerful strike infused with cursed energy.",
            ),
            EffectSkill(
                "Rhythmic: Hawak mo ang beat",
                "JC syncs his movements to an internal rhythm, enhancing his combat flow. Harder to predict.",
                effect=player._dancer_rhythm_effect,
                damage=15,
                bonus_domain=10,
            ),
            DamageSkill(
                "Skaddle: The Death Dancing",
                24,
                "JC activates his cursed technique, granting a massive boost in power and speed for 50 seconds.",
                bonus_domain=15,
            ),
        ],
    },
    "Bouncer": {
        "character_name": "Joem",
        "domain_name": "Silent Rebound Palace",
        "domain_desc": "All sound is erased. The opponent cannot hear anything, not even their own movements.",
        "skills": lambda player: [
            DamageSkill(
                "Bounce",
                14,
                "Joem leaps toward the enemy with explosive force, delivering a heavy impact on landing.",
            ),
            MultiHitSkill(
                "Daily press!",
                3,
                7,
                "A rapid flurry of multiple punches delivered in quick succession.",
                bonus_domain=5,
            ),
            EffectSkill(
                "Appeal to Bloattary",
                "His body instantly bloats into a massive size. Despite his weight, he moves faster than ever.",
                effect=player._bouncer_pressure_effect,
                damage=18,
                bonus_domain=10,
            ),
        ],
    },
    "Seeker": {
        "character_name": "Gaudenz",
        "domain_name": "Eye of Padullon",
        "domain_desc": "Gaudenz projects multiple copies of himself simultaneously, attacking from all directions.",
        "skills": lambda player: [
            EffectSkill(
                "Glare",
                "Locks eyes with the enemy, pressuring and potentially stunning them through sheer focus.",
                effect=player._glare_effect,
                damage=10,
            ),
            EffectSkill(
                "Battle cry",
                "A powerful shout that boosts stats while shaking the enemy's concentration and resolve.",
                effect=player._battle_cry_effect,
                damage=13,
                bonus_domain=10,
            ),
            EffectSkill(
                "Time Stop",
                "Skips the enemy turn, leaving them completely helpless during the freeze.",
                effect=player._time_stop_effect,
                damage=6,
                bonus_domain=10,
            ),
        ],
    },
}


class Player(Character):
    """
    Player class that extends Character.
    Includes leveling, domain, and mental system.
    """

    def __init__(self, name, player_class, starter_items=True):
        super().__init__(name, hp=100, attack=10)

        self.player_class = player_class
        self._level = 1
        self._exp = 0
        self._domain_meter = 0
        self._mental_instability = 0
        self._death_count = 0
        # Combat state tracks short-lived turn effects such as defending.
        self._defending = False
        self._inventory = Inventory()
        if starter_items:
            self._inventory.add_item(HealItem())
            self._inventory.add_item(DomainChargeItem())
            self._inventory.add_item(AttackBoostItem())

        self._apply_class_profile()

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, value):
        self._level = max(1, int(value))

    @property
    def exp(self):
        return self._exp

    @exp.setter
    def exp(self, value):
        self._exp = max(0, int(value))

    @property
    def domain_meter(self):
        return self._domain_meter

    @domain_meter.setter
    def domain_meter(self, value):
        self._domain_meter = max(0, min(100, int(value)))

    @property
    def mental_instability(self):
        return self._mental_instability

    @mental_instability.setter
    def mental_instability(self, value):
        self._mental_instability = max(0, min(5, int(value)))

    @property
    def death_count(self):
        return self._death_count

    @death_count.setter
    def death_count(self, value):
        self._death_count = max(0, int(value))

    @property
    def defending(self):
        return self._defending

    @defending.setter
    def defending(self, value):
        self._defending = bool(value)

    @property
    def inventory(self):
        return self._inventory

    def _apply_class_profile(self):
        """Load the class-specific domain name and skill list."""
        profile = CLASS_PROFILES.get(self.player_class, CLASS_PROFILES["Seeker"])
        self.domain_name = profile["domain_name"]
        self.domain_desc = profile.get("domain_desc", "")
        self.skills = profile["skills"](self)

    def perform_attack(self, target):
        """Polymorphic basic attack from Character."""
        damage = self.attack
        target.take_damage(damage)
        # Controlled randomness for domain gain so it no longer always
        # advances by a fixed amount. Keeps early-game feel varied.
        gain = randint(5, 15)
        self.domain_meter = min(100, self.domain_meter + gain)
        return {
            "success": True,
            "damage": damage,
            "domain_gain": gain,
            "message": f"{self.name} strikes the curse for {damage} damage! (Domain +{gain}% )",
        }

    def defend(self):
        """Enter a guarded state and gain a small amount of domain energy."""
        self.defending = True
        # Keep a small, reliable defensive gain so tutorials and tests
        # that expect a consistent value continue to behave.
        self.domain_meter = min(100, self.domain_meter + 5)
        return 5

    def use_domain(self, target):
        """Trigger the class domain when the meter is full."""
        if self.domain_meter < 100:
            return {
                "success": False,
                "damage": 0,
                "message": "Domain not ready.",
                "lines": [],
            }

        result = self._domain_effect(target)
        self.domain_meter = 0
        return result

    def use_skill(self, skill_index, target):
        """Execute one of the player's class skills and build domain charge."""
        try:
            skill = self.skills[skill_index]
        except (IndexError, TypeError):
            return {"success": False, "damage": 0, "message": "Skill failed.", "lines": []}

        result = skill.use(self, target)
        result["message"] = f"{self.name} used {skill.name}. {result['message']}"
        result["skill_name"] = skill.name
        bonus_domain = result.pop("bonus_domain", 0)
        # Skill-based domain gains are now randomized within a controlled
        # range, with class/skill-specific bonuses applied.
        base = randint(8, 12)
        gain = base + int(bonus_domain)
        self.domain_meter = min(100, self.domain_meter + gain)
        result["domain_gain"] = gain
        return result

    def gain_exp(self, amount):
        """Award EXP and return any level-up payloads produced."""
        self.exp += amount
        level_ups = []
        while self.exp >= 100:
            self.exp -= 100
            level_ups.append(self.level_up())
        return level_ups

    def level_up(self):
        """Increase stats and return a summary that the UI can render."""
        previous_max_hp = self.max_hp
        previous_attack = self.attack
        self.level += 1
        self.max_hp += 20
        self.attack += 5
        self.hp = self.max_hp
        return {
            "level": self.level,
            "hp_gain": self.max_hp - previous_max_hp,
            "atk_gain": self.attack - previous_attack,
        }

    def serialize_state(self):
        """Convert the player into JSON-safe save data."""
        return {
            "name": self.name,
            "class": self.player_class,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "attack": self.attack,
            "level": self.level,
            "exp": self.exp,
            "domain_meter": self.domain_meter,
            "mental_instability": self.mental_instability,
            "death_count": self.death_count,
            "inventory": [item.__class__.__name__ for item in self.inventory.items],
        }

    def load_state(self, data):
        """Hydrate the player from validated save data."""
        self.max_hp = data.get("max_hp", self.max_hp)
        self.hp = data.get("hp", self.hp)
        self.attack = data.get("attack", self.attack)
        self.level = data.get("level", self.level)
        self.exp = data.get("exp", self.exp)
        self.domain_meter = data.get("domain_meter", self.domain_meter)
        self.mental_instability = data.get("mental_instability", self.mental_instability)
        self.death_count = data.get("death_count", self.death_count)

        items = []
        for item_name in data.get("inventory", []):
            item_class = ITEM_REGISTRY.get(item_name)
            if item_class:
                items.append(item_class())
        self.inventory.replace_items(items)
        return self

    @classmethod
    def from_save_data(cls, data):
        """Build a player instance directly from validated save data."""
        player = cls(
            data.get("name", "Player"),
            data.get("class", "Seeker"),
            starter_items=False,
        )
        return player.load_state(data)

    def _domain_effect(self, target):
        """Resolve the class-specific effect of Domain Expansion."""
        # Domain attacks are intentionally stronger than regular skills,
        # but capped to stay balanced for early/mid-game.
        domain_bonus = int(self.attack * 0.3)
        if self.player_class == "Dancer":
            damage = (self.attack * 2) + 10 + domain_bonus
            target.take_damage(damage)
            target.attack = max(1, target.attack - 3)
            return {
                "success": True,
                "damage": damage,
                "message": f"{self.name} opened {self.domain_name}.",
                "lines": ["The arena drains the curse's power. Enemy attack fell by 3."],
            }

        if self.player_class == "Bouncer":
            damage = (self.attack * 2) + 8 + domain_bonus
            target.take_damage(damage)
            target.skip_next_turn = True
            return {
                "success": True,
                "damage": damage,
                "message": f"{self.name} opened {self.domain_name}.",
                "lines": ["Silence crushes the battlefield. The enemy will miss its next turn."],
            }

        damage = (self.attack * 2) + 12 + domain_bonus
        target.take_damage(damage)
        target.skip_next_turn = True
        target.attack = max(1, target.attack - 2)
        return {
            "success": True,
            "damage": damage,
            "message": f"{self.name} opened {self.domain_name}.",
            "lines": ["Illusions strike from every angle. Enemy attack fell by 2 and its next turn is skipped."],
        }

    def _dancer_rhythm_effect(self, user, target):
        """Dancer utility skill that softens the enemy's offense."""
        target.attack = max(1, target.attack - 1)
        return {
            "message": "The rhythm disrupts the enemy's timing.",
            "lines": ["Enemy attack fell by 1."],
        }

    def _bouncer_pressure_effect(self, user, target):
        """Bouncer utility skill that hits morale and damage output."""
        target.attack = max(1, target.attack - 2)
        return {
            "message": "The impact leaves the enemy shaken.",
            "lines": ["Enemy attack fell by 2."],
        }

    def _glare_effect(self, user, target):
        """Seeker opener that weakens the enemy with focused pressure."""
        target.attack = max(1, target.attack - 2)
        return {
            "message": "The glare pins the curse in place for a moment.",
            "lines": ["Enemy attack fell by 2."],
        }

    def _battle_cry_effect(self, user, target):
        """Seeker sustain skill that heals slightly and weakens the enemy."""
        target.attack = max(1, target.attack - 1)
        user.heal(8)
        return {
            "message": "The battle cry steadies your heart and rattles the enemy.",
            "lines": ["Recovered 8 HP.", "Enemy attack fell by 1."],
        }

    def _time_stop_effect(self, user, target):
        """
        Seeker special skill removes the enemy's next turn.
        """
        target.skip_next_turn = True
        return {
            "message": "Time fractures around the enemy.",
            "lines": ["The enemy will miss its next turn."],
        }

    def __str__(self):
        """Return a readable run summary for logs, saves, and debug output."""
        return (
            f"Player(name={self.name}, class={self.player_class}, level={self.level}, "
            f"hp={self.hp}/{self.max_hp}, attack={self.attack}, "
            f"domain={self.domain_meter}%, instability={self.mental_instability})"
        )

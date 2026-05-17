"""Campaign flow controller tying story, combat, rewards, and checkpoints together."""

import time

from models.enemy import Enemy
from models.item import AttackBoostItem, DomainChargeItem, HealItem
from systems.combat import start_combat
from systems.save_manager import save_game, clear_save
from utils.effects import format_duration, set_glitch_level
from systems.tutorial import run_tutorial


# Intro scenes are separated from the loop so the story can be tested and
# maintained without burying dialogue inside control-flow code.
INTRO_SCENES = [
    {
        "title": "Grandfather",
        "lines": [
            "Your grandfather died quietly, leaving behind words you never fully understood.",
            "He told you to stay strong no matter what happens.",
            "",
            'You: "I guess I\'m really doing this now."',
        ],
    },
    {
        "title": "3 Years Later",
        "lines": [
            "(Poof!)",
            'Kogane: "Ding-dong, ding-dong. I am Kogane, your personal assistant from here on out."',
            'You: "...What?"',
            'Kogane: "Yep, assigned to you. I guide you, update you, and try to keep you alive."',
        ],
    },
    {
        "title": "First Meeting",
        "lines": [
            'You: "You just popped out of nowhere and started talking like you own the place."',
            'Kogane: "Not owning, just doing my job. You\'re a sorcerer now."',
            'You: "Tch. Great. I get a talking thing as a partner."',
            'Kogane: "Not just anything, I\'m efficient, reliable, and a little annoying."',
            'You: "Yeah, I can already tell."',
            'Kogane: "Good. That means it\'s working."',
        ],
    },
]


# Stage data centralizes balance, rewards, and story beats per chapter.
STAGE_DATA = {
    1: {
        "title": "Tutorial (0)",
        "threat": "Something's coming, be ready.",
        "enemy": {"name": "Weak Curse", "hp": 40, "attack": 6, "enemy_type": "weak"},
        "exp": 40,
        "reward_item": HealItem,
        "pre_story": [
            {
                "title": "Tutorial (0)",
                "lines": [
                    "Night falls over General Trias. Strange sightings appear in schools and hospitals as cursed energy rises.",
                    "The situation feels off, but still under control.",
                    "",
                    "(Poof!)",
                    'Kogane: "Ding-dong. Ding-dong. Simple cleanup mission assigned. Stay alert. Stay alert."',
                    'You: "Yeah... something feels off."',
                    "",
                    "Something's coming, be ready.",
                ],
            }
        ],
        "post_story": [
            {
                "title": "After Stage 1",
                "lines": [
                    "The weak curses go down easily, but their numbers feel wrong.",
                    'You: "That\'s it? I was just getting started."',
                    'Kogane: "Ding-dong. Ding-dong. Update detected. Same disturbances in other areas."',
                ],
            }
        ],
    },
    2: {
        "title": "Escalation",
        "threat": "Stage 2 incoming, be ready.",
        "enemy": {"name": "Fast Curse", "hp": 55, "attack": 9, "enemy_type": "fast"},
        "exp": 50,
        "reward_item": DomainChargeItem,
        "pre_story": [
            {
                "title": "Escalation",
                "lines": [
                    "Reports increase across multiple locations at once.",
                    "Cursed spirits are now appearing in groups, not randomly.",
                    "",
                    "(Poof!)",
                    'Kogane: "Ding-dong. Ding-dong. Multiple incidents confirmed. The pattern is not normal."',
                    'You: "They\'re grouping up? Good...saves me time."',
                    "",
                    "Stage 2 incoming, be ready.",
                ],
            }
        ],
        "post_story": [
            {
                "title": "After Stage 2",
                "lines": [
                    "Enemies move faster and fight back harder. A pattern starts forming after each battle.",
                    "(Poof!)",
                    'Kogane: "Ding-dong. Ding-dong. Analysis complete. They are being pulled."',
                    'You: "Yeah... something\'s pulling them. I wanna see what it is."',
                ],
            }
        ],
    },
    3: {
        "title": "Pressure Spike",
        "threat": "Stage 3 incoming be ready.",
        "enemy": {"name": "Aggressive Curse", "hp": 80, "attack": 12, "enemy_type": "aggressive"},
        "exp": 60,
        "reward_item": AttackBoostItem,
        "pre_story": [
            {
                "title": "Pressure Spike",
                "lines": [
                    "Entire areas begin to destabilize. Something unseen is watching as cursed energy rises sharply.",
                    'You: "This is getting interesting."',
                    "(Poof!)",
                    'Kogane: "Ding-dong. Ding-dong. Energy spike detected. Cause unknown."',
                    'You: "That pressure... finally something worth hitting."',
                    "",
                    "Stage 3 incoming be ready.",
                ],
            }
        ],
        "post_story": [
            {
                "title": "After Stage 3",
                "lines": [
                    "Fights become more aggressive and coordinated. Even after winning, the pressure stays.",
                    'You: "More are coming? Perfect. Don\'t hold me back."',
                    "(Poof!)",
                    'Kogane: "Ding-dong. Ding-dong. Warning issued. You are pushing too far."',
                ],
            }
        ],
    },
    4: {
        "title": "Distortion",
        "threat": "Stage 4 incoming be ready.",
        "enemy": {"name": "Elite Curse", "hp": 90, "attack": 15, "enemy_type": "elite"},
        "exp": 70,
        "reward_item": HealItem,
        "pre_story": [
            {
                "title": "Distortion",
                "lines": [
                    "The sky begins to distort as time feels unstable in certain areas.",
                    "The cursed spirits grow more violent, reacting to something approaching.",
                    "(Poof!)",
                    'Kogane: "Ding-dong. Ding-dong. Energy levels are rising rapidly. The situation is unstable."',
                    'You: "So that\'s it... you\'re getting closer, huh. Good. I was getting bored."',
                    "",
                    "Stage 4 incoming be ready.",
                ],
            }
        ],
        "post_story": [
            {
                "title": "Silence",
                "lines": [
                    "Chaos spreads across multiple waves. After the last fight, everything goes silent.",
                    'You: "Everything just stopped...? Tch. Don\'t tell me that\'s all."',
                    "(Poof!)",
                    'Kogane: "Ding-dong. Ding-dong. Silence detected. Threat level uncertain."',
                ],
            }
        ],
    },
    5: {
        "title": "Special Grade",
        "threat": "Final Battle",
        "enemy": {"name": "Orlegou (Special Grade)", "hp": 180, "attack": 20, "enemy_type": "boss"},
        "exp": 100,
        "reward_item": None,
        "pre_story": [
            {
                "title": "Eclipse",
                "lines": [
                    "An eclipse forms. The air turns heavy. A Special Grade appears from the darkness.",
                    'You: "There you are."',
                    'Orlegou: "And this is what they sent to face me?"',
                    "(Poof!)",
                    'Kogane: "Ding-dong. Ding-dong. Emergency alert. Special Grade detected."',
                ],
            },
            {
                "title": "Boss Introduction",
                "lines": [
                    'You: "That\'s the kind of energy I\'ve been waiting for."',
                    'Orlegou: "How disappointing. I expected something... worth my time."',
                    'You: "Don\'t die too fast... I wanna enjoy this."',
                    'You: "Let\'s dance, shall we?"',
                    'Orlegou: "...Good. Try not to bore me."',
                    "",
                    "Final Battle.",
                ],
            },
        ],
        "post_story": [
            {
                "title": "Aftermath",
                "lines": [
                    "The Boss Has Fallen.",
                    "",
                    "The eclipse begins to fade. The heavy air slowly lifts.",
                    'You: "...That\'s it. That\'s what I was waiting for."',
                    "(Poof!)",
                    'Kogane: "Ding-dong. Ding-dong. It\'s done. Energy levels are dropping. Let\'s go home."',
                    'You: "Yeah."',
                ],
            },
            {
                "title": "False Victory",
                "lines": [
                    "A few seconds pass. Nothing moves.",
                    "",
                    "Then the ground shifts.",
                    "The entity stirs. Slowly, without urgency, it rises.",
                    'Orlegou: "...Hm. Stronger than I expected. But that was still just a greeting."',
                    'Orlegou: "Find me again... when you\'re ready to show me something real."',
                ],
            },
            {
                "title": "Final Words",
                "lines": [
                    "The entity disappears into the dark. No warning. It is simply gone.",
                    'Kogane: "...What just happened out there?"',
                    'You: "...he let me win."',
                    'You: "Next time... I\'ll make sure he can\'t walk away."',
                ],
            },
        ],
    },
}


class Game:
    """
    Main game controller.
    Kept as a required class for the course project, while its implementation
    lives under systems because it coordinates overall game logic.
    """

    def __init__(self, player, presenter, elapsed_time=0):
        self.player = player
        self.presenter = presenter
        self.current_stage = 1
        self.max_stage = max(STAGE_DATA)
        self.start_time = time.monotonic()
        self.elapsed_time_before_session = elapsed_time
        self._intro_shown = False
        self._tutorial_shown = False
        self._checkpoint_state = None
        set_glitch_level(self.player.mental_instability)

    @property
    def total_elapsed_time(self):
        return self.elapsed_time_before_session + (time.monotonic() - self.start_time)

    def _status_lines(self):
        return [
            f"Player: {self.player.name} ({self.player.player_class})",
            f"Stage: {self.current_stage}/{self.max_stage}   Time: {format_duration(self.total_elapsed_time)}",
            f"HP {self.player.hp}/{self.player.max_hp}   Domain {self.player.domain_meter}%   Instability {self.player.mental_instability}",
        ]

    def _show_scene(self, title, lines, pause_after=True):
        """Render one story/gameplay scene through the active presenter."""
        self.presenter.screen(
            title,
            lines,
            status_lines=self._status_lines(),
            footer="Press Enter to continue.",
        )
        # `AnsiGamePresenter.screen()` already blocks for Enter, so there is no
        # second wait here even if older callers still pass `pause_after=True`.

    def _show_scene_sequence(self, scenes):
        """Render a list of scene dictionaries in order."""
        for scene in scenes:
            self._show_scene(scene["title"], scene["lines"])

    def _show_intro(self):
        """Display the opening cutscene once per run."""
        self._show_scene_sequence(INTRO_SCENES)
        self._intro_shown = True

    def _show_stage_story(self, stage):
        """Display the pre-battle story for the current stage."""
        self._show_scene_sequence(STAGE_DATA[stage].get("pre_story", []))

    def _show_post_stage_story(self, stage):
        """Display the aftermath story after clearing a stage."""
        self._show_scene_sequence(STAGE_DATA[stage].get("post_story", []))

    def _prepare_stage(self):
        """Prepare temporary stage state when a new stage begins."""
        self.player.defending = False
        # Stage 5 uses fixed HP values for both sides for a predictable boss fight.
        if self.current_stage == 5:
            self.player.max_hp = 100
            self.player.hp = 100
        set_glitch_level(self.player.mental_instability)

    def generate_enemy(self):
        """Generate enemy based on stage data."""
        stage_data = STAGE_DATA[self.current_stage]["enemy"]
        base_hp = int(stage_data["hp"])
        player_hp_bonus = max(0, int(self.player.max_hp) - 100)
        # Keep enemy growth aligned with the player's HP growth each stage.
        enemy_hp = base_hp + player_hp_bonus
        # Final-stage boss uses a fixed HP target as requested.
        if self.current_stage == 5:
            enemy_hp = 250

        return Enemy(
            stage_data["name"],
            enemy_hp,
            stage_data["attack"],
            enemy_type=stage_data["enemy_type"],
            stage=self.current_stage,
        )

    def _capture_checkpoint(self):
        """Snapshot the player's state so retries restore the stage start."""
        self._checkpoint_state = self.player.serialize_state()

    def give_rewards(self):
        """Give EXP and item rewards after winning."""
        stage_data = STAGE_DATA[self.current_stage]
        exp_gain = stage_data["exp"]
        reward_lines = [f"Stage {self.current_stage} Cleared!", f"You gained {exp_gain} EXP."]

        reward_item_classes = stage_data.get("reward_item")
        reward_items = []
        if reward_item_classes is not None:
            if isinstance(reward_item_classes, (list, tuple, set)):
                reward_item_classes_iter = reward_item_classes
            else:
                reward_item_classes_iter = [reward_item_classes]

            for item_class in reward_item_classes_iter:
                if item_class is None:
                    continue
                reward_items.append(item_class())

        for idx, reward_item in enumerate(reward_items, start=1):
            self.player.inventory.add_item(reward_item)
            reward_lines.append(f"+ Item {idx}: {reward_item.name}.")
        if not reward_items:
            reward_lines.append("+ Items: None")

        level_ups = self.player.gain_exp(exp_gain)
        reward_lines.append(
            f"Level: {self.player.level}  HP: {self.player.hp}/{self.player.max_hp}  ATK: {self.player.attack}"
        )
        self.presenter.screen("Victory", reward_lines, status_lines=self._status_lines())
        self.presenter.loading(
            "Victory",
            "Calculating rewards and progression.",
            status_lines=self._status_lines(),
            seconds=1.6,
        )

        for delta in level_ups:
            self.presenter.screen(
                "Level Up!",
                [
                    f"You reached Level {delta['level']}.",
                    f"Max HP +{delta['hp_gain']}",
                    f"Attack +{delta['atk_gain']}",
                    "HP fully restored.",
                ],
                status_lines=self._status_lines(),
            )
            self.presenter.loading(
                "Level Up!",
                "Absorbing the power surge.",
                status_lines=self._status_lines(),
                seconds=1.2,
            )

    def death_system(self):
        """Reverse Curse Technique logic with true stage checkpoint restore."""
        new_instability = self.player.mental_instability + 1
        new_death_count = self.player.death_count + 1

        self.presenter.screen(
            "Reverse Curse Technique",
            [
                "You force your soul back into the fight.",
                f"Mental Instability: {new_instability}",
                f"Death Count: {new_death_count}",
                "The stage rewinds to the last checkpoint.",
            ],
            status_lines=self._status_lines(),
        )

        retry_index = self.presenter.menu(
            "Retry Current Stage?",
            ["Retry", "Give Up"],
            status_callback=self._status_lines,
        )

        if retry_index != 0:
            confirm_index = self.presenter.menu(
                "Game Over",
                ["No - Return to Retry Menu", "Yes - End This Run"],
                status_callback=self._status_lines,
                help_text="Are you sure? Choose a number and press Enter.",
            )
            if confirm_index == 0:
                return self.death_system()
            return False

        if self._checkpoint_state:
            restored_state = dict(self._checkpoint_state)
            restored_state["mental_instability"] = new_instability
            restored_state["death_count"] = new_death_count
            self.player.load_state(restored_state)
        else:
            self.player.hp = self.player.max_hp
            self.player.mental_instability = new_instability
            self.player.death_count = new_death_count

        set_glitch_level(self.player.mental_instability)
        save_game(self.player, self.current_stage, self.total_elapsed_time)
        return True

    def _show_ending(self):
        self.presenter.screen(
            "Ending",
            [
                "You survived the cursed domination.",
                "The fight is over for now, but Orlegou is still waiting.",
                "The story is not finished. The hunt continues.",
            ],
            status_lines=self._status_lines(),
        )

    def start(self):
        """Main game loop."""
        if not self._intro_shown and self.current_stage == 1:
            self._show_intro()
            # Run a short guided tutorial once at the start of a new run.
            if not self._tutorial_shown:
                run_tutorial(self)
                self._tutorial_shown = True

        while True:
            if self.current_stage > self.max_stage:
                self._show_ending()
                # Final run complete: clear persisted save so player doesn't
                # accidentally resume a finished run.
                try:
                    clear_save()
                except Exception:
                    pass
                break

            self._prepare_stage()
            self._show_stage_story(self.current_stage)
            self._capture_checkpoint()

            enemy = self.generate_enemy()
            result = start_combat(self.player, enemy, self.presenter, self)

            if result == "ESCAPE":
                # Player aborted the battle (Esc). Return to caller without triggering death flow.
                break

            if result == "WIN":
                cleared_stage = self.current_stage
                self.give_rewards()
                self._show_post_stage_story(cleared_stage)
                self.current_stage += 1
                if self.current_stage <= self.max_stage:
                    save_game(self.player, self.current_stage, self.total_elapsed_time)
                continue

            retry = self.death_system()
            if not retry:
                break

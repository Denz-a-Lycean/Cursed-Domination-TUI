"""
Single-stage battle flow using canonical `Game`, `CombatSystem`, and `AnsiGamePresenter`.

Thin `gameplay_N_*.py` modules re-export the concrete screen classes defined here.
"""

from __future__ import annotations

import sys

from core.engine import BaseScreen, ESC, RESET
from systems.ansi_game_presenter import AnsiGamePresenter
from systems.combat import start_combat
from systems.game import Game
from systems.save_manager import save_game
from utils.effects import set_glitch_level


class GameplayStageBattleScreen(BaseScreen):
    """
    Runs one stage: prepare → checkpoint → combat loop with optional death retry.
    """

    def __init__(
        self,
        window,
        state,
        stage_num: int,
        frame_title: str,
        win_next_state: str,
        saved_stage_after_win: int,
    ):
        super().__init__(window)
        self.state = state
        self.stage_num = int(stage_num)
        self.title = frame_title
        self.win_next_state = win_next_state
        self.saved_stage_after_win = int(saved_stage_after_win)

    def setup_ui(self):
        self.widgets = []

    def _sync_glitch_ui(self, player):
        if player:
            self.state.instability = player.mental_instability
            set_glitch_level(player.mental_instability)

    def run(self) -> str:
        self._update_layout_from_window()
        sys.stdout.write(f"{ESC}2J{RESET}")
        sys.stdout.flush()

        if not self.state.player:
            from models.player import Player

            self.state.player = Player(self.state.player_name or "Player", "Seeker")

        presenter = AnsiGamePresenter(self.window)
        game = Game(
            self.state.player,
            presenter,
            elapsed_time=self.state.elapsed_time_before_session,
        )
        game.current_stage = self.stage_num
        game._intro_shown = True
        game._tutorial_shown = True

        game._prepare_stage()
        game._capture_checkpoint()
        # Stage checkpoint is now authoritative inside `Game`.
        # Keep UI-facing stage index in global state only.
        self.state.checkpoint_stage = self.stage_num
        self.state.last_checkpoint_payload = dict(game._checkpoint_state) if isinstance(game._checkpoint_state, dict) else None

        self._sync_glitch_ui(self.state.player)


        while True:
            enemy = game.generate_enemy()

            result = start_combat(self.state.player, enemy, presenter, game)

            if result == "ESCAPE":
                return "SCREEN_MAIN_MENU"

            if result == "WIN":
                game.give_rewards()
                self.state.current_stage = self.saved_stage_after_win
                game.current_stage = self.saved_stage_after_win
                self._sync_glitch_ui(self.state.player)
                # Mirror reference save rule; always persist boss-clear with next stage index for ANSI flow.
                save_game(
                    self.state.player,
                    self.state.current_stage,
                    game.total_elapsed_time,
                )
                return self.win_next_state

            retry = game.death_system()
            self._sync_glitch_ui(self.state.player)

            if not retry:
                return "SCREEN_MAIN_MENU"



class GameplayTutorialScreen(GameplayStageBattleScreen):
    def __init__(self, window, state):
        super().__init__(
            window,
            state,
            stage_num=1,
            frame_title="Tutorial: Night over General Trias",
            win_next_state="SCENE_05_DISTURBANCE",
            saved_stage_after_win=2,
        )


class GameplayDisturbanceScreen(GameplayStageBattleScreen):
    def __init__(self, window, state):
        super().__init__(
            window,
            state,
            stage_num=2,
            frame_title="Escalation: The Unseen Pull",
            win_next_state="SCENE_06_PRESSURE",
            saved_stage_after_win=3,
        )


class GameplayPressureScreen(GameplayStageBattleScreen):
    def __init__(self, window, state):
        super().__init__(
            window,
            state,
            stage_num=3,
            frame_title="Pressure Spike",
            win_next_state="GAMEPLAY_04_CHAOS",
            saved_stage_after_win=4,
        )


class GameplayChaosScreen(GameplayStageBattleScreen):
    def __init__(self, window, state):
        super().__init__(
            window,
            state,
            stage_num=4,
            frame_title="Distortion",
            win_next_state="SCENE_07_BOSS_ENTRY",
            saved_stage_after_win=5,
        )


class GameplayBossScreen(GameplayStageBattleScreen):
    def __init__(self, window, state):
        super().__init__(
            window,
            state,
            stage_num=5,
            frame_title="Special Grade: Orlegou",
            win_next_state="SCENE_08_BOSS_DEFEAT",
            saved_stage_after_win=6,
        )

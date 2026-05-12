## Introduction

This document summarizes the `ANSI_SCREEN` project: a terminal-based, ANSI-styled roguelike/combat story game written in Python. It covers high-level architecture, ASCII UML diagrams, the main concepts (characters, items, skills, systems), development challenges, and key learnings.

## UML Diagrams (ASCII)

High-level component view:

```
+-----------------+     +----------------------+     +------------------+
|   main.py       | --> |   WindowManager /    | <-- |   assets/         |
| (entry & UI)    |     |   core.engine (UI)   |     | (ascii art / data)|
+-----------------+     +----------------------+     +------------------+
           |                        |                       
           v                        v                       
    +--------------+        +----------------+    +--------------------+
    |  scenes/     | ---->  |  systems/      | -> |  models/            |
    | (stage runner)|       | (game, combat, |    | (player, enemy,     |
    +--------------+        |  presenter)    |    |  item, skill)       |
                            +----------------+    +--------------------+

```

Class relationships (combat domain):

```
      Character (abstract)
           /   \
          /     \
      Player   Enemy
        |         |
     Inventory   AI behavior
        |
      Item(s) (HealItem, DomainChargeItem, AttackBoostItem)
        |
      Skill(s) (DamageSkill, EffectSkill, MultiHitSkill)

```

Screen/state flow (simplified):

```
MainMenu -> NameEntry -> SkillSelection -> GameplayStage(s) -> Victory/Death -> Save/Load
```

## Explain the Concept

- **Core idea**: A turn-based, stage-driven text game with ASCII UI where the player progresses through stages, fights enemies, gains EXP and items, and uses class-specific "domain" mechanics.
- **Characters**: Implemented via models.character.Character base class.
  - Player extends Character adding class profile, skills, inventory, domain meter, leveling, and save/serialize helpers.
  - Enemy extends Character adding simple AI decision logic based on enemy_type and stage.
- **Skills**: Encapsulated in `models.skill` as three types: `DamageSkill`, `MultiHitSkill`, and `EffectSkill`. Skills return structured payloads (damage, lines, bonus_domain) consumable by the combat UI.
- **Items**: Implemented in `models.item`. Items provide effects (heal, domain charge, attack boost) and a consistent result payload for UI.
- **Systems**:
  - `systems.game.Game`: orchestrates stage generation, story scenes, rewards, checkpoints, and progression.
  - `systems.combat.CombatSystem`: turn-based combat loop with presenter hooks for animations and menus.
  - `systems.save_manager`: JSON save/load with validation.
  - `systems.ansi_game_presenter.AnsiGamePresenter`: translates game state into ANSI-framed UI (HUD, menus, dialogue).
- **UI / Engine**: `core.engine` provides widgets (`Label`, `Button`, `TextBox`), `WindowManager`, and `BaseScreen` for consistent, centered 140x30 frame rendering.
- **Scenes**: `scenes/` modules describe story beats (intro, pre/post stage text) and provide `GameplayStage` screens that run a stage's combat loop.

## Challenges Faced During Development

- Terminal compatibility: ensuring ANSI sequences render consistently across Windows PowerShell/CMD required careful use of escape codes and terminal setup (e.g., enabling virtual terminal processing, alternate buffer).
- Text layout and ANSI: mixing colored ANSI escape sequences with fixed-width alignment and centering required helper utilities to measure visible length versus raw string length.
- Input handling: supporting both blocking and non-blocking key reads across platforms (msvcrt on Windows, fallback to stdin/select) while handling Ctrl+C gracefully.
- Balancing deterministic behavior and randomness: combat and domain gains needed controlled randomness (helper wrappers in `utils.randomizer`) for stable testing while keeping gameplay variety.
- Save validation: to avoid corrupt saves causing crashes, a validation layer normalizes and sanitizes load data before hydrating `Player` instances.

## Learnings

- Separate concerns: the project cleanly separates presentation (`AnsiGamePresenter` / `core.engine`) from domain (`models/`) and orchestration (`systems/`), which made adding features like domain mechanics and animated HUD easier.
- Structured payloads simplify UI integration: skills and items return consistent dict payloads used by `CombatSystem` and presenter, reducing ad-hoc rendering code.
- Testing & automation: small wrappers around randomness (`utils.randomizer`) made it straightforward to seed and test combat flows.
- UX-first constraints: designing for a fixed 140x30 layout simplifies design but requires extra work to center and adapt to variable terminal sizes.
- Defensive IO: explicit validation and controlled input loops (with interrupt handlers) make the game robust for both interactive and automated runs.

---

If you'd like, I can:
- add class diagrams per-file (detailed ASCII for `Player`, `Enemy`, `CombatSystem`),
- produce a smaller printable summary (one-page), or
- open a PR that adds this file to `docs/` and links it from the main `README.md`.

File created: [PROJECT_ANALYSIS.md](PROJECT_ANALYSIS.md#L1)

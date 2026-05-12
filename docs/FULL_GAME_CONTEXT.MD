# CURSED DOMINATION — FULL GAME CONTEXT
# MASTER IMPLEMENTATION CONTEXT DOCUMENT

Last Updated: 2026-05-08

---

# PROJECT OVERVIEW

## Game Title
Cursed Domination

## Genre
CLI / Terminal-Based RPG

## Main Concept
Cursed Domination is a terminal-based RPG built entirely in Python using Object-Oriented Programming principles. The game focuses on turn-based combat, progression systems, story integration, domain mechanics, checkpoint retry systems, instability effects, and immersive terminal presentation using ASCII/ANSI/TUI effects.

The game must feel:
- Stylish
- Atmospheric
- Aggressive
- Chaotic
- Story-driven
- Visually immersive despite being CLI-only

The project prioritizes:
1. Gameplay flow
2. Stability
3. Story immersion
4. Terminal presentation
5. Replayability
6. OOP structure
7. Requirement compliance

---

# IMPORTANT DEVELOPMENT PHILOSOPHY

## Core Design Rule
Even though the game is CLI-only, the experience should feel cinematic.

The terminal is treated as:
- a screen
- a stage
- a cinematic canvas

ASCII animations, ANSI effects, transitions, spacing, timing, glitching, and text pacing are all part of gameplay immersion.

The game should NOT feel like:
- plain print statements
- basic school-project menus
- static text dumps

The game SHOULD feel:
- alive
- reactive
- dramatic
- unstable during high tension

---

# CORE GAMEPLAY LOOP

```text
START GAME
    ↓
MAIN MENU
    ↓
NEW GAME / LOAD GAME
    ↓
PLAYER SETUP
(Name + Class Selection)
    ↓
TUTORIAL STAGE
(Kogane explains mechanics)
    ↓
STAGE LOOP
    ↓
STORY SCENE
    ↓
COMBAT
    ↓
REWARDS
    ↓
SAVE
    ↓
NEXT STAGE
    ↓
FINAL BOSS
    ↓
ENDING
    ↓
RETURN TO MAIN MENU

---

# GAME STRUCTURE

## Total Stages

| Stage    | Purpose                 |
| -------- | ----------------------- |
| Tutorial | Teach mechanics         |
| Stage 1  | Weak enemy introduction |
| Stage 2  | Faster enemies          |
| Stage 3  | Aggressive enemies      |
| Stage 4  | Pressure/elite stage    |
| Stage 5  | Orlegou boss battle     |

---

# STORY SUMMARY

## Main Premise

Three years after the death of the protagonist’s grandfather, cursed activity begins increasing rapidly across General Trias.

The player becomes involved in the world of curses and is assigned a floating assistant named Kogane.

At first:

* missions seem normal
* enemies are weak

But something is wrong:

* cursed spirits are grouping together
* energy spikes become abnormal
* reality itself begins distorting

Eventually:
the player encounters a Special Grade entity named Orlegou.

After defeating it:
the player realizes the fight was merely a “greeting.”

The true conflict has only begun.

---

# STORY TONE

The story tone should be:

* dark
* sarcastic
* stylish
* slightly comedic
* increasingly unsettling

Kogane acts as:

* guide
* announcer
* system narrator
* comic relief
* warning system

The player acts:

* confident
* reckless
* battle-hungry
* increasingly obsessed with stronger enemies

---

# IMPORTANT CHARACTERS

## Player

Unnamed protagonist chosen by the player.

Traits:

* confident
* aggressive
* thrill-seeking
* obsessed with stronger enemies

---

## Kogane

Floating assistant entity.

Speech style:

* repetitive
* robotic
* “Ding-dong. Ding-dong.”
* system-like announcements

Role:

* explains mechanics
* narrates alerts
* guides progression
* comments on danger levels

IMPORTANT:
Kogane should feel alive in dialogue.

---

## Orlegou

Special Grade curse.

Traits:

* calm
* overwhelming
* disappointed
* never emotional
* terrifying through composure

IMPORTANT:
Orlegou should NEVER feel loud or cartoonish.

Its danger comes from:

* calm speech
* confidence
* overwhelming pressure

---

# TUTORIAL DESIGN

## Tutorial Purpose

The tutorial exists to:

* teach controls
* explain combat
* introduce Kogane
* show combat flow
* avoid confusion

The tutorial MUST be interactive.

---

# TUTORIAL FLOW

```text
Kogane Introduction
    ↓
Basic Explanation
    ↓
Weak Enemy Appears
    ↓
Player Learns:
    - Attack
    - Defend
    - Skills
    - Inventory
    - Domain Meter
    ↓
Player Wins
    ↓
Stage 1 Begins
```

---

# COMBAT SYSTEM

## Combat Style

Turn-based.

Flow:

```text
PLAYER TURN
    ↓
ENEMY TURN
    ↓
REPEAT
```

---

# PLAYER ACTIONS

## 1. Attack

Opens skill menu.

---

## 2. Defend

Reduces incoming damage.

Can also slightly increase domain progress.

---

## 3. Domain Expansion

Only available at 100%.

High damage or special effects.

Resets after use.

---

## 4. Inventory

Use healing or buff items.

---

# DOMAIN SYSTEM

## IMPORTANT DESIGN RULE

The domain system must NOT feel like:

* permanent stat stacking
* generic power-up mode

The domain system should feel:

* unstable
* momentum-based
* dramatic
* unpredictable

---

# DOMAIN PROGRESSION RULES

## Old System (BAD)

```text
Every attack = +10%
```

Problems:

* predictable
* boring
* overpowered
* repetitive

---

# New Recommended System

## Randomized Domain Gain

Every action gives:

```text
+5% to +18%
```

Depending on:

* skill used
* critical moments
* randomness
* enemy pressure

---

# DOMAIN RESET RULE

IMPORTANT:
Domain progress MUST reset:

* after domain activation
* after stage completion
* after retry/death

No permanent carry-over.

---

# OPTIONAL ADVANCED SYSTEM

## Sigmoid-Based Domain Scaling

Purpose:
Prevent predictable linear growth.

Possible concept:

* slower early gain
* faster mid gain
* slower near 100%

This creates:

* tension
* unpredictability
* pacing

---

# PLAYER CLASSES

## JC the Dancer

Playstyle:

* rhythm
* mobility
* aggressive combos

Themes:

* dance
* speed
* flow

---

## Joem the Bouncer

Playstyle:

* heavy damage
* pressure
* brute force

Themes:

* impact
* body enlargement
* overwhelming force

---

## Gaudenz the Seeker

Playstyle:

* control
* disruption
* tactical pressure

Themes:

* eye techniques
* stun
* time manipulation

---

# ENEMY DESIGN

## Enemy Types

| Type       | Behavior                    |
| ---------- | --------------------------- |
| Weak       | Basic attacks               |
| Fast       | Multiple actions / pressure |
| Aggressive | Heavy damage                |
| Elite      | Mixed mechanics             |
| Boss       | Unique attack patterns      |

---

# ENEMY AI RULES

Enemy behavior should:

* react to HP
* react to stage
* react to pressure
* NOT be purely random

---

# REVERSE CURSE SYSTEM

## Purpose

Acts as:

* checkpoint system
* retry system
* instability mechanic

---

# On Death

Player:

* revives at stage start
* keeps penalties
* retries stage

---

# Penalties

Each death:

* increases instability
* increases visual corruption
* worsens glitch effects
* alters dialogue slightly

---

# INSTABILITY LEVELS

| Death Count | Effect            |
| ----------- | ----------------- |
| 0           | Normal            |
| 1–2         | Minor glitches    |
| 3+          | Heavy instability |
| Extreme     | Possible collapse |

---

# VISUAL PRESENTATION

# VERY IMPORTANT

The game presentation should heavily use:

* ASCII
* ANSI
* TUI formatting
* transitions
* animation timing
* screen clearing
* cinematic spacing

---

# UI/UX GOALS

The interface should feel:

* clean
* dramatic
* readable
* stylish

---

# EXAMPLE FORMAT

```text
====================================
            YOUR TURN
====================================

HP: 120/120
DOMAIN: 64%
LEVEL: 4

------------------------------------

1. Attack
2. Defend
3. Domain
4. Inventory
```

---

# ASCII / ANSI DESIGN GOALS

## Story Scenes

Use:

* centered text
* fade-ins
* pauses
* atmospheric spacing

---

## Combat

Use:

* animated damage
* flashing critical hits
* slash effects
* enemy entrance animations

---

## Boss Fight

Use:

* eclipse visuals
* screen distortion
* glitch transitions
* heavy ANSI effects

---

## Reverse Curse

Use:

* corrupted text
* flickering menus
* unstable dialogue
* distorted UI

---

# SAVE SYSTEM

## Uses JSON

Must save:

* player name
* class
* level
* HP
* EXP
* inventory
* stage
* instability
* death count

---

# SAVE REQUIREMENTS

Must safely handle:

* missing files
* corrupted files
* invalid JSON

No crashing allowed.

---

# REQUIRED OOP STRUCTURE

## Core Classes

```text
Character
Player
Enemy
Item
Game
Skill
CombatSystem
SaveManager
```

---

# OOP REQUIREMENTS

Must demonstrate:

* inheritance
* encapsulation
* abstraction
* polymorphism

---

# FILE STRUCTURE

```text
main.py

models/
    character.py
    player.py
    enemy.py
    item.py
    skill.py

systems/
    game.py
    combat.py
    inventory.py
    save_manager.py

utils/
    effects.py
    presenter.py
    validator.py
    randomizer.py
    input_handler.py

data/
    save.json
```

---

# CODING RULES

## Style

Variables/functions:

```python
snake_case
```

Classes:

```python
PascalCase
```

---

# SAFETY RULES

Must:

* validate all input
* prevent crashes
* use try/except
* safely recover from invalid input

---

# TESTING REQUIREMENTS

The game should support:

```powershell
python -m unittest -q
```

---

# IMPORTANT DESIGN PRIORITIES

## PRIORITY ORDER

### 1. Stability

Game must never crash.

### 2. Playability

Complete start-to-finish experience.

### 3. Story Integration

Scenes must connect naturally.

### 4. Presentation

ASCII/ANSI immersion.

### 5. Polish

Animations, spacing, transitions.

---

# FINAL EXPERIENCE GOAL

The final game should feel like:

* a cinematic terminal RPG
* a cursed anime battle system
* a corrupted command-line experience
* a playable story, not just menus

Even without graphics,
the player should feel:

* tension
* escalation
* pressure
* immersion
* instability
* excitement

The terminal itself should feel alive.

```
```

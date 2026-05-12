# List of CHANGES from tasked in TODO

## (DONE) Domain Timer + Overlay Fix (systems/ansi_game_presenter.py)

- [x] Overlay geometry is computed once at the start of `AnsiGamePresenter.domain_expansion_animation()` (outer/inner box positions), so the timer loop no longer re-centers/recalculates overlay layout each tick.
- [x] Countdown display is integer seconds only (`remaining_i`), clamped to 0 when time expires.
- [x] Barrier bar fill is deterministic via an integer remaining->fill mapping (no float rounding jitter).
- [x] ESC is handled during the timer loop to exit the domain timer early.
- [x] Flicker is reduced by rendering the base battle panel once before the loop, then writing only the overlay boxes each tick.
- [x] Smoke test note: run `main.py`, trigger Domain Expansion, confirm stable timer overlay and ESC behavior.


## (DONE) Autopilot attribute-based selection (main.py)

- [x] Replace fragile `isinstance(w, Button)` checks with attribute-based detection (`hasattr(w, 'action_name')` and `is_enabled`).
- [x] `AutoPilotMixin._auto_choose_action()` now selects actionable widgets by `action_name` and deterministic label sorting.
- [x] Notes: This avoids class-identity mismatches across imports and makes autopilot progression reliable for UI screens.
 - [x] Notes: This avoids class-identity mismatches across imports and makes autopilot progression reliable for UI screens.
 - [x] Trigger changed: autopilot enabled only when running `python main.py -copilot`. Autopilot is only for TUI/UI-UX debugging.
 - [x] Autopilot extended to gameplay: `AnsiGamePresenter.menu()` now returns deterministic selections when `-copilot` is present, and `stop()` is non-blocking to allow automated captures.



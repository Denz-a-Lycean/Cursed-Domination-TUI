# TODO LISTING


## (DONE) TODO: Domain Timer + Overlay Fix

- [x] Refactor `AnsiGamePresenter.domain_expansion_animation()` to compute overlay geometry once (no per-tick re-centering).
- [x] Update countdown display to integer seconds (no float decimals) and clamp at 0.
- [x] Ensure barrier bar fill uses deterministic remaining->fill mapping.
- [x] Handle ESC during timer loop (break/exit early).
- [x] Reduce flicker: avoid rebuilding full battle panel every tick; only redraw overlay regions.
- [x] Smoke test: run `main.py`, trigger Domain Expansion, verify stable timer overlay and controls.



## (DONE) TODO: Autopilot attribute-based selection

- [x] Make autopilot choose widgets by `action_name` and `is_enabled` rather than fragile `isinstance` checks.
- [x] Update `main.py` AutoPilotMixin._auto_choose_action() to be attribute-based and deterministic.
 - [x] Verify main menu and UI screens advance under `python main.py -copilot`.
 - [x] Confirm autopilot is strictly for TUI/UI-UX debugging only (not gameplay automation).
 - [x] Verify main menu and UI screens advance under `python main.py -copilot`.
 - [x] Extend autopilot to gameplay: presenter auto-selects menu choices and `stop()` is non-blocking in `-copilot`.



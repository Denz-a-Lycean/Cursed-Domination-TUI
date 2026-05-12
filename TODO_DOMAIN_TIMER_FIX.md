# TODO: Domain Timer + Overlay Fix

- [ ] Refactor `AnsiGamePresenter.domain_expansion_animation()` to compute overlay geometry once (no per-tick re-centering).
- [ ] Update countdown display to integer seconds (no float decimals) and clamp at 0.
- [ ] Ensure barrier bar fill uses deterministic remaining->fill mapping.
- [ ] Handle ESC during timer loop (break/exit early).
- [ ] Reduce flicker: avoid rebuilding full battle panel every tick; only redraw overlay regions.
- [ ] Smoke test: run `main.py`, trigger Domain Expansion, verify stable timer overlay and controls.


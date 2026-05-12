Problems & Proposed Solutions
=============================

Date: 2026-05-12

Scope
-----
This document summarizes issues I found during a code review of the game code (focused on the rendering/presenter, combat flow, assets, and save system). Each issue has: a short description, impact, a proposed fix, and a suggested priority.

Files inspected (non-exhaustive)
-------------------------------
- `systems/ansi_game_presenter.py`
- `systems/combat.py`
- `systems/save_manager.py`
- `systems/game.py`
- `assets/ascii_arts/dance.py`
- `assets/ascii_arts/bounce.py`
- `assets/ascii_arts/banlag.py`

Summary of findings
-------------------
1) Inconsistent handling of callable `status_lines`/`status_data` in `AnsiGamePresenter.loading()`

- Symptom: `CombatSystem` often passes `status_lines=self._status_lines` and `status_data=self._status_data` (callables). Many presenter animation hooks handle callables by calling them inside the animation loop (see `attack_animation`, `domain_expansion_animation`, `domain_attack_animation`). However, `loading()` assigns `parsed = status_data if status_data is not None else (_parse_combat_status(list(status_lines or [])) if status_lines else None)` which can leave `parsed` equal to a callable instead of the expected dict. Passing a callable into `_battle_panel_buffer` leads to attribute errors when the presenter expects `parsed.get(...)`.

- Impact: intermittent crashes or incorrect rendering when `loading()` is invoked with callables; subtle and hard to trace because exceptions are swallowed in many places.

- Proposed fix: make `loading()` mirror the callable-handling pattern used elsewhere. Example:

```py
            if status_data is not None:
                st = status_data() if callable(status_data) else status_data
            else:
                st = status_lines() if callable(status_lines) else status_lines
            parsed = _parse_combat_status(list(st or [])) if st else None
```

Place that logic inside the loop so parsed updates every redraw.

- Priority: High

2) Silent/poor diagnostics when asset loading or rendering fails

- Symptom: `_load_asset_module()` and `_render_asset_overlay()` ignore exceptions and return `None` silently. Failed loads result in missing domain overlays with no log messages.

- Impact: debugging asset problems is time-consuming; failures hidden from maintainers.

- Proposed fix: record load failures to the presenter's log buffer (use `self._push_log(...)`) and include an optional verbose flag for presenter initialization. Example change in `_load_asset_module()` except block:

```py
        except Exception as exc:
            try:
                self._push_log(f"Asset load failed: {fname} -> {exc}")
            except Exception:
                pass
            return None
```

- Priority: Medium

3) Unsafe execution model for ASCII asset modules

- Symptom: `_load_asset_module()` executes entire Python source from `assets/ascii_arts/*.py` via `exec`. That runs top-level imports and any top-level code in the asset file (even if a `main()` guard is present, imports and other module-level statements execute). This can cause side-effects, platform-specific imports (e.g. `msvcrt`), or security concerns if assets are modified.

- Impact: assets with top-level code may alter stdout/terminal state during load, import platform-only modules or cause errors. It also poses a maintainability/security risk.

- Proposed fixes (in order of preference):
  - Convert ASCII assets to pure-data (plain `.txt` frames or Python files that only declare `render_domain_frame()` and avoid imports/top-level code). Minimal friction and safest.
  - Or: change loader to only parse & compile the `render_domain_frame` function (using `ast` to extract the function node and compile it), avoiding execution of arbitrary top-level code. This requires a bit more code but is robust and still uses only the standard library.
  - As a short-term mitigation: detect risky tokens (e.g. `msvcrt`, `os.system`, `sys.stdout.write`) and reject the asset with a helpful log message.

- Priority: High (security + reliability)

4) Truncation/clamping may break ANSI escape sequences

- Symptom: `_clamp()` uses `len(s)` to decide truncation and then slices the raw string. If `s` contains ANSI color sequences, the length calculation and slicing can cut an escape sequence producing broken terminal codes or corrupt rendering.

- Impact: corrupted output, broken colors, or control sequences visible in the UI when long colored strings are clipped.

- Proposed fix: implement ANSI-aware truncation. Two reasonable approaches:
  - Prefer preserving color: iterate through the original string, copy full ANSI sequences verbatim, and count only visible characters when deciding when to truncate. When truncated, append `...` and preserve open escapes by closing color with `RESET` if necessary.
  - Simpler fallback: use `_strip_ansi()` to get the plain text for truncation and return a plain (non-colored) truncated string. This loses color but avoids broken sequences.

Suggested safe implementation sketch (preserve ANSI):

```py
def _clamp(s: str, max_len: int) -> str:
    s = str(s).replace("\n", " ")
    if _visible_len(s) <= max_len:
        return s
    out = []
    visible = 0
    i = 0
    while i < len(s) and visible < max_len - 3:
        if s[i] == '\033':
            m = ANSI_SEQ.match(s, i)
            if m:
                out.append(m.group(0))
                i = m.end()
                continue
        out.append(s[i])
        visible += 1
        i += 1
    out.append('...')
    return ''.join(out)
```

- Priority: Medium

5) Minor UX / robustness notes

- `AnsiGamePresenter._write_full()` writes `ESC + 'H' + buffer + RESET` to stdout. In places where partial overlays are used, ensure `RESET` placement doesn't accidentally clear intended colors. Also review ordering of `_clamp()` then `_pad_ansi_line()` (truncation before padding) — an ANSI-aware clamp should be used prior to padding.

- `save_manager.load_game()` swallows JSON parsing errors and returns `None` silently. It would be helpful to surface a log message or persist a diagnostic file when a save file cannot be parsed, to aid debugging corrupted saves.

- Domain animations call `get_keypress_nb()` during long timers but don't act on the key; if you intend to allow the player to interrupt the domain with a key, the function needs to process the key and gracefully exit. If not intended, consider removing the `break` on key press to avoid confusion.

Recommended immediate actions
---------------------------
1. Fix `AnsiGamePresenter.loading()` callable handling (high priority). This is a small, low-risk change and will eliminate a class of subtle bugs.
2. Add logging to `_load_asset_module()` and `_render_asset_overlay()` so asset load failures are visible to developers (medium priority).
3. Migrate ASCII assets to data-only files or implement an AST-based safe loader (high priority). If you prefer a quick path, convert current `assets/ascii_arts` modules so they only contain the single `render_domain_frame()` function and no platform imports.
4. Implement ANSI-aware `_clamp()` or adopt the simpler fallback (strip ANSI before truncation) to avoid broken escape sequences (medium priority).

Suggested next steps for me (pick one)
------------------------------------
- I can implement the `loading()` fix and add logging for asset loading now (small, safe changes) and then run `tests/smoke_playthrough.py` to sanity-check runtime behavior.
- Or I can instead implement the AST-based safe loader for domain assets (larger change) and adjust the presenter to use it.
- Or I can leave code untouched and just commit this analysis document — you can tell me which of the above you want implemented.

How to reproduce likely failures
-------------------------------
- Run `python tests/smoke_playthrough.py` and inspect stdout/stderr for missing asset overlays or weird exceptions in animation steps. If animations are missing, check the presenter's logs (it records messages via `_push_log`) or the `docs/SAVE_CHANGES.md` and save files for additional diagnostics.

Closing
-------
I created this file so you can review the findings and choose which changes I should apply automatically. If you want, I can implement the `loading()` fix and the logging improvement right away and re-run the smoke playthrough.

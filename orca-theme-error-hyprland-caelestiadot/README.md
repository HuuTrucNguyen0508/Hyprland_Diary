# Orca / Cursor Theme Flash & Revert Fix

**Date:** 2026-08-19  
**Context:** Theme applied briefly on open, then reverted to black background. Existing tabs kept theme after Orca restart; new tabs did not.

---

## Symptoms

- Theme flashed for a split second, then background returned to black.
- Restarting Orca restored theme on **existing** tabs only — **new** terminal tabs stayed black/default.
- Cursor had similar auto-theme override behavior.

---

## Root Cause

1. **Caelestia color injection on shell startup**  
   Fish ran `cat ~/.local/state/caelestia/sequences.txt` on every interactive session. That file sends OSC sequences (including `OSC 11` background color `rgb:0c/0f/0b`), overriding Orca/Cursor terminal themes on each new tab.

2. **Cursor auto color-scheme detection**  
   `"window.autoDetectColorScheme": true` let Cursor follow system theme after startup, overriding manual theme choice.

3. **Orca settings (informational, not edited)**  
   Orca profile already had `terminalThemeDark: "Everforest Dark"` and `leftSidebarAppearanceMode: "match-terminal"` in `~/.config/orca/profiles/local-default/orca-data.json`. The problem was shell startup overriding terminal colors, not missing Orca theme config.

---

## Changes Applied

### 1. Cursor — disable auto scheme detection

**File:** `~/.config/Cursor/User/settings.json`

```json
{
    "window.autoDetectColorScheme": false
}
```

### 2. Fish — skip Caelestia sequences in Orca/Cursor terminals

**File:** `~/.config/fish/config.fish`

**Before:**
```fish
# Custom colours
cat ~/.local/state/caelestia/sequences.txt 2> /dev/null
```

**After:**
```fish
# Custom colors from Caelestia; skip in Orca/Cursor terminals so
# their own terminal themes are not overridden on new tabs.
if test "$TERM_PROGRAM" != "Orca"; and test "$TERM_PROGRAM" != "vscode"
    cat ~/.local/state/caelestia/sequences.txt 2> /dev/null
end
```

Detected env in Orca terminals: `TERM_PROGRAM=Orca`.

### 3. Orca restart

Orca was restarted so config/runtime picked up cleanly:

- Old PID: `60811` → New PID: `66739`
- Runtime verified: `state: ready`, `graph: ready`

---

## Verification

1. Fully quit and reopen Orca (and Cursor if open).
2. Open a **new** terminal tab — background should match selected Orca terminal theme (e.g. Everforest Dark), not forced black from Caelestia.
3. In Cursor, theme should no longer flip after startup.

---

## Related Paths (reference)

| Path | Role |
|------|------|
| `~/.local/state/caelestia/sequences.txt` | Caelestia OSC color sequences (background + palette) |
| `~/.config/fish/config.fish` | Shell startup; Caelestia color guard |
| `~/.config/Cursor/User/settings.json` | Cursor theme auto-detect |
| `~/.config/orca/profiles/local-default/orca-data.json` | Orca app + terminal theme settings |

---

## Not changed / optional follow-ups

- Orca UI “follow system theme” (if present) — disable manually if theme still drifts.
- Pin explicit Cursor theme: `"workbench.colorTheme": "<your theme>"` in `settings.json`.
- Restrict Caelestia sequences to specific terminals only (e.g. foot/kitty) if needed.
- Fish syntax error on startup from Orca preflight script (`ORCA_CODEX_LAUNCH_PREFLIGHT`) — separate issue; does not affect theme fix above.

# Orca / Cursor theme flash and revert

2026-08-19

Theme flashed for a split second on open, then the background went black again. After an Orca restart, existing tabs kept the theme. New terminal tabs did not. Cursor had a similar auto-theme override.

## Causes

### Caelestia colour injection on shell startup

Fish ran this on every interactive session:

```fish
cat ~/.local/state/caelestia/sequences.txt 2> /dev/null
```

That file dumps OSC sequences, including `OSC 11` background `rgb:0c/0f/0b`. Every new tab got painted over by Caelestia, no matter what Orca or Cursor had set.

### Cursor auto colour-scheme detection

`"window.autoDetectColorScheme": true` let Cursor follow the system theme after startup and override the manual choice.

### Orca itself was fine

Profile already had `terminalThemeDark: "Everforest Dark"` and `leftSidebarAppearanceMode: "match-terminal"` in `~/.config/orca/profiles/local-default/orca-data.json`. Missing Orca theme config was not the bug. The shell was.

## Changes

### Cursor: stop auto scheme detection

`~/.config/Cursor/User/settings.json`:

```json
{
    "window.autoDetectColorScheme": false
}
```

### Fish: skip Caelestia sequences in Orca and Cursor terminals

`~/.config/fish/config.fish`

Before:

```fish
# Custom colours
cat ~/.local/state/caelestia/sequences.txt 2> /dev/null
```

After:

```fish
# Custom colors from Caelestia; skip in Orca/Cursor terminals so
# their own terminal themes are not overridden on new tabs.
if test "$TERM_PROGRAM" != "Orca"; and test "$TERM_PROGRAM" != "vscode"
    cat ~/.local/state/caelestia/sequences.txt 2> /dev/null
end
```

Orca terminals report `TERM_PROGRAM=Orca`.

### Restart Orca

Restarted so runtime picked up cleanly. Old PID `60811` → new PID `66739`. Runtime checked: `state: ready`, `graph: ready`.

## Check

1. Fully quit and reopen Orca (and Cursor if it is open).
2. Open a new terminal tab. Background should match the Orca terminal theme (Everforest Dark here), not Caelestia's forced black.
3. In Cursor, the theme should stop flipping after startup.

## Paths

| Path | Role |
|------|------|
| `~/.local/state/caelestia/sequences.txt` | Caelestia OSC colour sequences |
| `~/.config/fish/config.fish` | Shell startup; Caelestia colour guard |
| `~/.config/Cursor/User/settings.json` | Cursor theme auto-detect |
| `~/.config/orca/profiles/local-default/orca-data.json` | Orca app + terminal theme |

## Optional follow-ups I did not do

- If Orca has a "follow system theme" toggle and things still drift, turn that off by hand.
- Pin an explicit Cursor theme with `"workbench.colorTheme": "<your theme>"`.
- Restrict Caelestia sequences to specific terminals only (foot/kitty) if you want that elsewhere.
- Fish syntax noise from Orca's preflight script (`ORCA_CODEX_LAUNCH_PREFLIGHT`) is a separate issue. It does not break this theme fix.

## Copies in this folder

| File | Live path |
|------|-----------|
| `config.fish` | `~/.config/fish/config.fish` |
| `Cursor-settings.json` | `~/.config/Cursor/User/settings.json` |
| `orca-data.json` | `~/.config/orca/profiles/local-default/orca-data.json` |

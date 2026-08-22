# Orca / Cursor theme flash and revert

2026-08-19. Theme flashed for a split second on open, then the background went black again. After an Orca restart, existing tabs kept the theme. New terminal tabs did not. Cursor had a similar auto-theme override.

## Catch up in 60 seconds

**Cause:** Fish printed Caelestia OSC sequences (`~/.local/state/caelestia/sequences.txt`) into every new tab, painting over Orca/Cursor terminal themes. Cursor also had `window.autoDetectColorScheme: true`.

**Fix:** Skip sequences when `TERM_PROGRAM` is `Orca` or `vscode`. Turn off Cursor auto-detect.

```fish
# In ~/.config/fish/config.fish — guard around sequences.txt cat
if test "$TERM_PROGRAM" != "Orca"; and test "$TERM_PROGRAM" != "vscode"
    cat ~/.local/state/caelestia/sequences.txt 2> /dev/null
end
```

Fully quit and reopen Orca/Cursor after editing.

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

Profile already had `terminalThemeDark: "Everforest Dark"` in `orca-data.json`. Missing Orca theme config was not the bug. The shell was.

## Changes

### Cursor

`~/.config/Cursor/User/settings.json`:

```json
{
    "window.autoDetectColorScheme": false
}
```

### Fish

Guard around the sequences cat (see catch-up block above).

## Check

1. Fully quit and reopen Orca (and Cursor if open).
2. New terminal tab: background should match Orca terminal theme, not Caelestia's forced black.
3. Cursor theme should stop flipping after startup.

## Paths

| Path | Role |
|------|------|
| `~/.local/state/caelestia/sequences.txt` | Caelestia OSC colour sequences |
| `~/.config/fish/config.fish` | Shell startup; Caelestia colour guard |
| `~/.config/Cursor/User/settings.json` | Cursor theme auto-detect |
| `~/.config/orca/profiles/local-default/orca-data.json` | Orca app + terminal theme |

## Optional follow-ups I did not do

- Pin an explicit Cursor theme with `"workbench.colorTheme": "<your theme>"`.
- Restrict Caelestia sequences to specific terminals only (foot/kitty) if you want that elsewhere.
- Fish syntax noise from Orca's preflight script is a separate issue.

## Copies in this folder

| File | Live path |
|------|-----------|
| `config.fish` | `~/.config/fish/config.fish` |
| `Cursor-settings.json` | `~/.config/Cursor/User/settings.json` |
| `orca-data.json` | `~/.config/orca/profiles/local-default/orca-data.json` |

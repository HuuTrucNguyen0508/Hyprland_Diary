# Zen Browser follows Caelestia

Zen does not speak Caelestia natively. `caelestia-zen-sync` rewrites CSS variables into each profile's `chrome/` folder when `scheme.json` changes. Toolbar and tabs follow the wallpaper. Page content does not.

## Catch up in 60 seconds

Service watches `~/.local/state/caelestia/` and regenerates `caelestia-colors.css`. **Full Zen restart** required after a wallpaper change. Colours lag a few seconds even then.

```bash
systemctl --user is-active caelestia-zen-sync.service   # expect: active
systemctl --user restart caelestia-zen-sync.service
cat ~/.config/zen/*/chrome/caelestia-colors.css
```

Needs `fish`, `jq`, `inotify-tools`. Profile must have `toolkit.legacyUserProfileCustomizations.stylesheets = true` in `user.js`.

| Piece | Path |
|-------|------|
| Profile chrome | `~/.config/zen/<profile>/chrome/` |
| Generated vars | `chrome/caelestia-colors.css` |
| Rules you edit | `chrome/userChrome.css` |
| Sync script | `~/.local/bin/caelestia-zen-sync` |
| Service | `caelestia-zen-sync.service` |
| Scheme | `~/.local/state/caelestia/scheme.json` |

## Profile prefs

Without this, Zen ignores `userChrome.css` entirely:

```js
user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);
```

Put it in `user.js` (or set it once in prefs). The `chrome/` directory has to exist under the profile.

## Files

`userChrome.css` stays mine. It only imports the generated file and paints chrome backgrounds:

```css
@import url("caelestia-colors.css");

#navigator-toolbox,
#nav-bar,
#urlbar-container,
#TabsToolbar,
#PersonalToolbar,
#PanelUI-menu-button,
#unified-extensions-button,
#window-controls {
  background: var(--zen-colors-tertiary) !important;
}
```

`caelestia-colors.css` is overwritten by the sync script. Do not hand-edit it.

| CSS variable | From `scheme.json` |
|--------------|--------------------|
| `--zen-colors-primary` | `colours.primary` |
| `--zen-colors-secondary` | `colours.secondary` |
| `--zen-colors-tertiary` | `colours.surfaceContainer` |
| `--zen-colors-primary-foreground` | `colours.onPrimary` |
| `--zen-colors-input-bg` | `colours.surfaceBright` |
| `--zen-colors-border` / `border-contrast` | `colours.outlineVariant` |
| `--zen-colors-hover-bg` | `colours.surfaceContainerHigh` |

The script walks every `~/.config/zen/*/chrome` folder, so a second profile gets the same treatment without extra config.

## Service

```bash
systemctl --user enable --now caelestia-zen-sync.service
```

On start it writes CSS once, then `inotifywait -m` on `~/.local/state/caelestia` and regenerates when `scheme.json` lands.

## Caveats

- Zen does not pick up the new chrome CSS live. Quit fully and reopen after a scheme change.
- Restart can take a bit before the new colours show. Same lag as the cursor theme.

## Check

Change wallpaper, quit Zen fully, open it again, give it a moment, then look at the toolbar.

## Copies in this folder

| File | Live path |
|------|-----------|
| `caelestia-zen-sync` | `~/.local/bin/caelestia-zen-sync` |
| `caelestia-zen-sync.service` | `~/.config/systemd/user/caelestia-zen-sync.service` |
| `userChrome.css` | `~/.config/zen/<profile>/chrome/userChrome.css` |
| `caelestia-colors.css` | `~/.config/zen/<profile>/chrome/caelestia-colors.css` |

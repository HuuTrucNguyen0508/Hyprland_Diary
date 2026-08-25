# Caelestia launcher: Flow-style search

Super opens Caelestia's launcher. Stock it mostly finds apps. This overlay adds Flow Launcher vibes: type a filename, a calc, a URL, a window title, or a PATH binary, and Enter does the thing.

Aug 2026. Built in the Orca worktree `~/orca/projects/Hyprland_Laucnher` (typo kept; that is the real folder name).

## Start here

**Who this helps:** Caelestia on Hyprland, wanting file/window/calc/URL/runner rows in the Super launcher without switching to Walker for every search.

**What Super does now (mixed list, top to bottom):**

| Kind | Example | Enter |
|------|---------|-------|
| Calc / convert | `2+2`, `100 USD to EUR` | copies result (`wl-copy`) |
| URL | `https://…` or `example.com` | opens in browser |
| Window | title / class match | focuses via Hyprland Lua dispatch |
| App | desktop entries (stock) | launches app |
| Runner | PATH binary, e.g. `btop` | Ghostty `-e` + wrap script |
| File | `base.yml` | `xdg-open` |
| Web | any query ≥2 chars | Google search row |

Inactive Elephant providers stay hidden (`1password`, `bitwarden`, `dnfpackages`, `niriactions`, `nirisessions`).

```bash
# Overlay must point at the working shell copy
readlink -f ~/.config/quickshell/caelestia
# expect: …/orca/projects/Hyprland_Laucnher/shell

# After QML / helper edits
qs -c caelestia kill; sleep 0.2; caelestia shell -d

# After Elephant config edits
systemctl --user restart elephant.service
```

## How it is wired

Caelestia loads `~/.config/quickshell/caelestia` over `/etc/xdg/quickshell/caelestia`. That path is a symlink into the Orca project `shell/`.

`AppList.qml` still does app search. On the default "apps" state it also fans the typed text out to four singletons:

1. `Extras` — Qalculator async, URL detect, Google row
2. `Windows` — `hypr_windows.py list` → `hyprctl -j clients`
3. `Runner` — Elephant `runner` via `elephant_provider_query.py`
4. `Files` — Elephant `files` via `elephant_files_query.py`, with `fd` fallback on a short list of common roots (not full `$HOME`, that is too slow per keystroke)

Result order in code: calc/url head, then windows, apps, runner, files, then the Google tail.

### Window focus gotcha

Stock-style `hyprctl dispatch focuswindow` fails on this Hyprland 0.56 Lua stack. Focus uses:

```text
hyprctl dispatch 'hl.dsp.focus({ window = "address:0x…" })'
```

with a workspace switch fallback for special / other workspaces. See `assets/hypr_windows.py`.

### Runner / terminal gotcha

Ghostty treats args as config keys unless you pass `-e` before the wrap script. Runner launch is:

```text
<terminal> -e <shellDir>/assets/wrap_term_launch.sh <binary>
```

Without `-e` you get `cli:N:…: invalid field` and nothing useful runs.

## Live paths

Prefer these if diary copies drift.

| Piece | Live path |
|-------|-----------|
| Working Quickshell overlay | `~/orca/projects/Hyprland_Laucnher/shell` |
| Symlink Caelestia uses | `~/.config/quickshell/caelestia` → that `shell/` |
| Stock package (untouched) | `/etc/xdg/quickshell/caelestia` |
| Pristine backups + restore notes | `~/orca/projects/Hyprland_Laucnher/backups/` |
| Elephant files / providerlist / runner | `~/.config/elephant/` |
| Elephant daemon | `elephant.service` (user) |

## Rollback to stock launcher

```bash
rm -rf ~/.config/quickshell/caelestia
qs -c caelestia kill; sleep 0.2; caelestia shell -d
```

Optional: restore `files.toml` from a `*.bak-*` next to it, then `systemctl --user restart elephant.service`. The package under `/etc/xdg/…` was never edited. Full notes: [RESTORE.md](./RESTORE.md).

## After a caelestia-shell package update

Upstream QML under `/etc/xdg/quickshell/caelestia` can move. Re-copy stock into `shell/`, then re-apply the launcher patches (or rebase the overlay). Do not delete `backups/` first.

## Copies in this folder

Snapshots from the Aug 2026 worktree. Canonical code stays under `~/orca/projects/Hyprland_Laucnher/`.

| Path here | What it is |
|-----------|------------|
| `AppList.qml` | Merge order + query fan-out |
| `services/*.qml` | Files, Extras, Runner, Windows singletons |
| `items/*.qml` | File / extra / result row UI |
| `assets/*.py` | Elephant helpers + Hyprland window list/focus |
| `elephant/*.toml` | Live Elephant config snapshot |
| `RESTORE.md` | Rollback steps |
| `project-README.md` | Short README from the Orca worktree |

## Related

- [Orca theme + Caelestia](../Orca-ide-theme-error/) — Fish OSC vs Orca/Cursor terminals (separate issue)
- [Logout button](../Loging%20screen%20and%20logout%20button/logout-button/) — same Hyprland Lua dispatch world (`hl.dsp.*`)

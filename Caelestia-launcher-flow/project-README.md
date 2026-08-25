# Hyprland Launcher (Caelestia + Flow-style extras)

Extends the Caelestia launcher so Super can:

- Find files (`base.yml`) via Elephant + `fd`
- Auto-calc / convert (`2+2`, `100 USD to EUR`) and copy on Enter
- Focus open windows (Elephant `windows`)
- Run `$PATH` commands (Elephant `runner`)
- Open URLs (`https://…` or `example.com`)
- Search the web (Google row for the typed query)

Inactive Elephant providers are hidden in `~/.config/elephant/providerlist.toml`
(`1password`, `bitwarden`, `dnfpackages`, `niriactions`, `nirisessions`).

## Layout

- `shell/` — working Quickshell overlay (symlinked to `~/.config/quickshell/caelestia`)
- `backups/` — pristine snapshots taken before changes; see `backups/RESTORE.md`

## Restore stock launcher

```bash
rm -rf ~/.config/quickshell/caelestia
qs -c caelestia kill; sleep 0.2; caelestia shell -d
```

## Refresh after caelestia-shell package updates

Re-copy upstream QML, then re-apply the file-search / extras patches (or rebase
`shell/` against `/etc/xdg/quickshell/caelestia`).

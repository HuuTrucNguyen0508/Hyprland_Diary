# Restore stock Caelestia launcher

The working launcher before this project was the system package at
`/etc/xdg/quickshell/caelestia`. User overlay at `~/.config/quickshell/caelestia`
takes precedence when present.

## Rollback

1. Remove the overlay:
   `rm -rf ~/.config/quickshell/caelestia`
2. Restart the shell:
   `qs -c caelestia kill; sleep 0.2; caelestia shell -d`
3. Optionally restore related configs from the matching
   `backups/caelestia-shell-TIMESTAMP/related/` folder
   (`shell.json`, `keybinds.lua`, `files.toml`).
4. If you changed Elephant indexing and want stock defaults:
   `cp ~/.config/elephant/files.toml.bak-* ~/.config/elephant/files.toml`
   then `systemctl --user restart elephant.service`

You do not need to restore `/etc/xdg/...`; the package was never modified.

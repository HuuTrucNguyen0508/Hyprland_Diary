# Caelestia shell after system updates

## Start here

This entry is for anyone running the [Caelestia](https://github.com/caelestia-dots/caelestia) shell from AUR packages on Arch or CachyOS. After a normal `pacman -Syu`, the bar can crash or fail to load, because some AUR packages were built against library versions the update just replaced. The fix is to rebuild that one package. Nothing in your config is wrong.

Two ways it has broken here so far:

| Date | Trigger | Package to rebuild | What you see |
| ---- | ------- | ------------------ | ------------ |
| Nov 2026 (25th) | `qt6-base` 6.12.0 to 6.12.1 | `quickshell-git` | Red `COMPATIBILITY WARNING` during the update; crash risk |
| Nov 2026 (20th) | `sndio` 1.10 to 1.11 (soname bump) | `libcava` | After reboot, no bar or wallpaper; Hyprland itself runs |

Sanity checks after any update:

```bash
quickshell --private-check-compat && echo "quickshell OK"

# Caelestia stack: list any binary or library with a missing link
pacman -Qql quickshell-git caelestia-shell libcava qt6-m3shapes-git \
  | grep -E '\.so(\.|$)|/usr/bin/' \
  | while read -r f; do [ -f "$f" ] && ldd "$f" 2>/dev/null | grep -q 'not found' && echo "BROKEN $f"; done
```

No output from the second command means every link resolves.

## Quickshell after a Qt update

Quickshell (the QML runtime under Caelestia) compiles against Qt's private headers. Qt only keeps those stable within one exact version, so even a patch bump like 6.12.0 to 6.12.1 needs a rebuild. Repo packages (`extra/quickshell`) get rebuilt by the packagers. `quickshell-git` from the AUR does not, so that part is on you.

The package ships a pacman hook that runs after every `qt6-base` or `qt6-wayland` upgrade and checks this for you. When it fails, the update output looks like this:

```
(15/19) Querying Quickshell compatibility after Qt6 update...
COMPATIBILITY WARNING: Quickshell was built against Qt 6.12.0 but the system has
updated to Qt 6.12.1 without rebuilding the package. This is likely to cause
crashes, so you must rebuild the quickshell package.
error: command failed to execute correctly
```

The `error:` line is only the hook exiting non-zero. The rest of the update completed.

### Fix

The quick way, which also pulls the newest Quickshell commit:

```bash
paru -S quickshell-git --rebuild
```

What I ran instead, to rebuild the same commit so that Qt was the only thing changing:

```bash
cd ~/.cache/paru/clone/quickshell-git
makepkg -f --holdver          # --holdver: don't pull new git commits
pkexec pacman -U "$PWD"/quickshell-git-*.pkg.tar.zst
quickshell --private-check-compat && echo OK
```

Two snags:

- `makepkg` stopped on `Missing dependencies: ninja`. A cleanup of orphans had removed it since the last build. `pkexec pacman -S --needed --asdeps ninja` fixed it.
- `pkexec` starts in `/`, so a relative package path gives `could not find or read package`. Use an absolute path, as above.

Then restart the running shell. It still has the old binary and old Qt loaded in memory:

```bash
caelestia shell -k
caelestia shell -d
```

To check that the new process really uses the new Qt:

```bash
grep -o '/usr/lib/libQt6Core.so[^ ]*' /proc/$(pgrep -xo qs)/maps | sort -u
# expect the current version, e.g. /usr/lib/libQt6Core.so.6.12.1
```

## libcava after an sndio update

Here the symptom shows up only after a reboot. Hyprland runs but there is no bar and no wallpaper. The Quickshell log has:

```
Cannot load library /usr/lib/qt6/qml/Caelestia/Services/libcaelestia-servicesplugin.so:
libsndio.so.7: cannot open shared object file
```

`sndio` 1.11 renamed its library from `libsndio.so.7` to `libsndio.so.9`. The AUR `libcava` (audio visualiser library, used by Caelestia's services plugin) was still linked to `.so.7`. One plugin failing to load takes the whole shell config down with it.

### Fix

```bash
paru -G libcava && cd libcava
pkexec pacman -S --needed --asdeps meson autoconf-archive
makepkg -f
pkexec pacman -U "$PWD"/libcava-*.pkg.tar.zst
ldd /usr/lib/libcava.so.1 | grep sndio     # expect libsndio.so.9
caelestia shell -d
```

## General pattern

When an update in the official repos bumps a library, AUR packages that link to it are not rebuilt automatically. For the whole system, not just Caelestia:

```bash
pacman -Qqm | xargs pacman -Qql 2>/dev/null \
  | grep -E '\.so(\.|$)|/usr/bin/' \
  | while read -r f; do [ -f "$f" ] && ldd "$f" 2>/dev/null | grep -q 'not found' && echo "$f"; done
```

Any file it prints belongs to an AUR package that needs a rebuild, or that is dead and can go. `pacman -Qo <file>` tells you which package.

## Live paths

Prefer live paths if the copies here drift.

| Piece | Path |
| ----- | ---- |
| Compat hook (from the `quickshell-git` package) | `/usr/share/libalpm/hooks/quickshell-check.hook` |
| paru build cache | `~/.cache/paru/clone/<package>/` |
| Shell autostart | `~/.config/hypr/hyprland/execs.lua` (`caelestia shell -d`) |
| Quickshell logs | `qs log -c caelestia`, files under `/run/user/1000/quickshell/` |
| Update history | `/var/log/pacman.log` |

## Copies in this folder

| File | What it is |
| ---- | ---------- |
| `quickshell-check.hook` | The pacman hook that prints the compatibility warning |

## Related

- [Caelestia launcher (Flow-style)](../Caelestia-launcher-flow/): the QML overlay that also has to keep pace with `caelestia-shell` updates
- [Snapshots and recovery](../Snapshots-and-recovery/): rolling back an update that breaks more than the shell
- [Administrative dialogs](../Loging%20screen%20and%20logout%20button/authentication-on-right-monitor/): where the `pkexec` password prompts appear

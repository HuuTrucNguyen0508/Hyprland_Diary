-- Snippet from ~/.config/caelestia/hypr-user.lua (TURZX binds only)

-- Omarchy-style Fast.com speedtest (desktop dials + TURZX takeover)
hl.bind("SUPER + SHIFT + F", hl.dsp.exec_cmd("~/.config/hypr/scripts/toggle_speedtest.sh"))

-- TURZX stats dashboard peek (10s, extends on repeat)
hl.bind("SUPER + SHIFT + D", hl.dsp.exec_cmd("~/.config/hypr/scripts/toggle_dashboard_peek.sh"))

-- TURZX ambient screen: next app
hl.bind("SUPER + SHIFT + N", hl.dsp.exec_cmd("~/.config/hypr/scripts/ambient_next.sh"))

hl.monitor({
    output = "DP-3",
    mode = "2560x1440@165",
    position = "0x0",
    scale = 1,
    cm = "hdr",
    bitdepth = 10,
    sdrbrightness = 3,
    sdrsaturation = 1.25,
})

hl.monitor({
    output = "HDMI-A-1",
    mode = "1920x1080@60",
    position = "2560x0",
    scale = 1,
})

hl.workspace_rule({ workspace = "1", monitor = "DP-3", default = true })
hl.workspace_rule({ workspace = "2", monitor = "HDMI-A-1", default = true })

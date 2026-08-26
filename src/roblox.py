import win32gui  # type: ignore


def is_active():
    window = win32gui.GetForegroundWindow()

    return win32gui.GetWindowText(window) == "Roblox"

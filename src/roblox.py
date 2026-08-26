import win32gui


def is_active():
    window = win32gui.GetForegroundWindow()

    return win32gui.GetWindowText(window) == "Roblox"

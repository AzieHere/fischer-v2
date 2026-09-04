@echo off

set "REPO_URL=https://github.com/AzieHere/fischer-v2"
set "DEST_DIR=%APPDATA%\fischer-v2"
set "SHORTCUT_DESKTOP=%USERPROFILE%\Desktop\fischer v2.lnk"
set "SHORTCUT_START=%APPDATA%\Microsoft\Windows\Start Menu\Programs\fischer v2.lnk"
set "UNINSTALL_START=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Uninstall fischer v2.lnk"

if exist "%DEST_DIR%" (
    cd /d "%DEST_DIR%"
    git pull
) else (
    git clone "%REPO_URL%" "%DEST_DIR%"
)

cd /d "%DEST_DIR%"
if exist "requirements.txt" (
    python -m pip install -r requirements.txt
)

set "UNINSTALL_BAT=%DEST_DIR%\uninstall.bat"
echo @echo off > "%UNINSTALL_BAT%"
echo taskkill /f /im pythonw.exe ^>nul 2^>nul >> "%UNINSTALL_BAT%"
echo del /f /q "%SHORTCUT_DESKTOP%" ^>nul 2^>nul >> "%UNINSTALL_BAT%"
echo del /f /q "%SHORTCUT_START%" ^>nul 2^>nul >> "%UNINSTALL_BAT%"
echo del /f /q "%UNINSTALL_START%" ^>nul 2^>nul >> "%UNINSTALL_BAT%"
echo cd /d "%%TEMP%%" >> "%UNINSTALL_BAT%"
echo rmdir /s /q "%DEST_DIR%" ^>nul 2^>nul >> "%UNINSTALL_BAT%"

set "VBS=%TEMP%\shortcut.vbs"

echo Set oWS = WScript.CreateObject("WScript.Shell") > "%VBS%"
echo Set oLink = oWS.CreateShortcut("%SHORTCUT_DESKTOP%") >> "%VBS%"
echo oLink.TargetPath = "pythonw.exe" >> "%VBS%"
echo oLink.Arguments = """%DEST_DIR%\src\main.py""" >> "%VBS%"
echo oLink.WorkingDirectory = "%DEST_DIR%" >> "%VBS%"
echo oLink.IconLocation = "%DEST_DIR%\images\icon.ico" >> "%VBS%"
echo oLink.Save >> "%VBS%"

echo Set oLink = oWS.CreateShortcut("%SHORTCUT_START%") >> "%VBS%"
echo oLink.TargetPath = "pythonw.exe" >> "%VBS%"
echo oLink.Arguments = """%DEST_DIR%\src\main.py""" >> "%VBS%"
echo oLink.WorkingDirectory = "%DEST_DIR%" >> "%VBS%"
echo oLink.IconLocation = "%DEST_DIR%\images\icon.ico" >> "%VBS%"
echo oLink.Save >> "%VBS%"

echo Set oLink = oWS.CreateShortcut("%UNINSTALL_START%") >> "%VBS%"
echo oLink.TargetPath = "%UNINSTALL_BAT%" >> "%VBS%"
echo oLink.WorkingDirectory = "%DEST_DIR%" >> "%VBS%"
echo oLink.Description = "Uninstall fischer v2" >> "%VBS%"
echo oLink.IconLocation = "%DEST_DIR%\images\icon.ico" >> "%VBS%"
echo oLink.Save >> "%VBS%"

cscript /nologo "%VBS%"
del "%VBS%"

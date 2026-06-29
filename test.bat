@echo off
title CS2 ESP
:: Launch without console window using pythonw.exe
:: If pythonw.exe is not in PATH, specify full path, e.g., C:\Python310\pythonw.exe
start "" pythonw.exe esp.py
:: For extra stealth, rename pythonw.exe to winlogon.exe and use that (requires admin)
:: Alternatively, compile esp.py to .exe with PyInstaller --noconsole and run that
exit

# TraceLauncher

## Overview

This project automates login and traceId creation using Selenium with ChromeDriver.

---

## Setup and Run on macOS

### 1. Create a virtual environment named `selenium-env`
`python3 -m venv selenium-env`

### 2. Activate the virtual environment
`source selenium-env/bin/activate`

### 3. Install required packages
`pip install -r requirements.txt`

### 4. Run the script
`python trace_launcher_console.py`

### 5. Or you can add it to **flows** config file
```json
        {
            "name": "Tealium New Trace",
            "cmd" : "cd /Users/walid/Work && source selenium-env/bin/activate && python3 /Users/walid/Work/trace_launcher_console.py"
        }
```

## Important Notes

- The **first launch of the app may take some time** because it downloads the ChromeDriver binary.
- You will need to **log in manually the first time** because the script uses a separate Selenium Chrome profile and does **not** share cookies with your default Chrome browser.
- Please **close the Chrome window after use** to avoid profile locking issues on subsequent runs.

### To generate package installers
`pyinstaller --onedir --icon tealium.icns --windowed --name "TraceLauncher" trace_launcher.py`

`npx create-dmg dist/TraceLauncher.app --icon tealium.icns --overwrite --dmg-title='TraceLauncher Installer' --identity=""`
- For Windows you can use: **Inno Setup** after generating the exe file by **pyinstaller**.

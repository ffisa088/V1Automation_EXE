@echo off
setlocal EnableExtensions EnableDelayedExpansion
REM ================================================================
REM  setup.bat  -  AcSys ERP Automation One-Click Setup
REM  Run this ONCE on any new PC before using BehaveTestRunner.exe
REM ================================================================

title AcSys ERP Automation - One-Click Setup Installer

REM Project root folder (ensure working directory is project folder even if run as admin)
set "PROJECT=%~dp0"
if "!PROJECT:~-1!"=="\" set "PROJECT=!PROJECT:~0,-1!"
cd /d "!PROJECT!"

cls
echo.
echo  ================================================================
echo   AcSys ERP Automation - Automated Setup Installer
echo   Auto-downloads and installs everything needed for this PC
echo  ================================================================
echo   Project folder: !PROJECT!
echo  ================================================================
echo.

REM ── 1. Internet Connection Check ─────────────────────────────────
echo  [1/7] Checking internet connection...
ping -n 1 8.8.8.8 >nul 2>&1
if errorlevel 1 (
    echo        WARNING: ICMP ping blocked, trying HTTPS probe...
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; try { (New-Object Net.WebClient).DownloadString('https://www.google.com') | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
    if errorlevel 1 (
        echo        ERROR: No active internet connection detected!
        echo        An internet connection is required for initial setup.
        echo        Please connect to the internet and run setup.bat again.
        echo.
        pause
        exit /b 1
    )
)
echo        Internet connection OK.

REM ── 2. Google Chrome Check & Auto-Install ────────────────────────
echo.
echo  [2/7] Checking Google Chrome browser...
set "CHROME_BIN="
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" set "CHROME_BIN=C:\Program Files\Google\Chrome\Application\chrome.exe"
if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" set "CHROME_BIN=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" set "CHROME_BIN=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"

if not "!CHROME_BIN!"=="" goto CHROME_READY

echo        Google Chrome not found. Auto-downloading Chrome installer...
set "CHROME_SETUP=%TEMP%\ChromeStandaloneSetup64.exe"
powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object Net.WebClient).DownloadFile('https://dl.google.com/chrome/install/latest/chrome_installer.exe', '%TEMP%\ChromeStandaloneSetup64.exe')"
if exist "%TEMP%\ChromeStandaloneSetup64.exe" (
    echo        Installing Google Chrome silently (please wait 20-40 seconds)...
    start /wait "" "%TEMP%\ChromeStandaloneSetup64.exe" /silent /install
    del "%TEMP%\ChromeStandaloneSetup64.exe" >nul 2>&1
)

REM Wait loop up to 45 seconds for Chrome to complete install
set /a c_wait=0
:WAIT_CHROME
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" set "CHROME_BIN=C:\Program Files\Google\Chrome\Application\chrome.exe"
if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" set "CHROME_BIN=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" set "CHROME_BIN=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
if not "!CHROME_BIN!"=="" goto CHROME_READY

if !c_wait! lss 9 (
    set /a c_wait+=1
    timeout /t 5 >nul
    goto WAIT_CHROME
)

echo        ERROR: Automatic Chrome installation failed.
echo        Please install Chrome manually: https://www.google.com/chrome/
start https://www.google.com/chrome/
pause
exit /b 1

:CHROME_READY
set "CHROME_VER="
for /f "usebackq tokens=*" %%V in (`powershell -NoProfile -Command "(Get-Item '!CHROME_BIN!').VersionInfo.FileVersion" 2^>nul`) do (
    set "CHROME_VER=%%V"
)
if "!CHROME_VER!"=="" set "CHROME_VER=detected"
echo        Google Chrome ready: !CHROME_BIN! (v!CHROME_VER!)

REM ── 3. Python Check & Auto-Install ────────────────────────────────
echo.
echo  [3/7] Checking Python runtime...
set "SYS_PYTHON="

REM Priority 1: Check existing venv inside project
if exist "!PROJECT!\venv\Scripts\python.exe" (
    "!PROJECT!\venv\Scripts\python.exe" --version >nul 2>&1
    if not errorlevel 1 (
        set "SYS_PYTHON=!PROJECT!\venv\Scripts\python.exe"
        echo        Valid project virtual environment found.
        goto PYTHON_FOUND
    ) else (
        echo        Notice: Existing venv is invalid or copied from another PC.
        echo        Resetting virtual environment cleanly for this PC...
        rmdir /s /q "!PROJECT!\venv" >nul 2>&1
    )
)

REM Priority 2: Check Windows Python Launcher (py.exe)
for /f "tokens=*" %%I in ('py -3 -c "import sys; print(sys.executable)" 2^>nul') do (
    if "!SYS_PYTHON!"=="" (
        if exist "%%I" (
            "%%I" --version >nul 2>&1
            if not errorlevel 1 set "SYS_PYTHON=%%I"
        )
    )
)

REM Priority 3: Check existing Python in PATH (skipping broken WindowsApps dummy stub)
if "!SYS_PYTHON!"=="" (
    where python >nul 2>&1
    if not errorlevel 1 (
        for /f "delims=" %%I in ('where python 2^>nul') do (
            if "!SYS_PYTHON!"=="" (
                echo "%%I" | findstr /i "WindowsApps" >nul
                if errorlevel 1 (
                    "%%I" --version >nul 2>&1
                    if not errorlevel 1 set "SYS_PYTHON=%%I"
                )
            )
        )
    )
)

REM Priority 4: Search standard installation paths
if "!SYS_PYTHON!"=="" (
    for %%V in (315 314 313 312 311 310) do (
        if "!SYS_PYTHON!"=="" (
            if exist "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" set "SYS_PYTHON=%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe"
            if exist "C:\Python%%V\python.exe" set "SYS_PYTHON=C:\Python%%V\python.exe"
            if exist "C:\Program Files\Python%%V\python.exe" set "SYS_PYTHON=C:\Program Files\Python%%V\python.exe"
            if exist "C:\Program Files (x86)\Python%%V\python.exe" set "SYS_PYTHON=C:\Program Files (x86)\Python%%V\python.exe"
        )
    )
    for %%V in (3.15 3.14 3.13 3.12 3.11 3.10) do (
        if "!SYS_PYTHON!"=="" (
            if exist "%LOCALAPPDATA%\Python\pythoncore-%%V-64\python.exe" set "SYS_PYTHON=%LOCALAPPDATA%\Python\pythoncore-%%V-64\python.exe"
        )
    )
)

if not "!SYS_PYTHON!"=="" goto PYTHON_FOUND

REM Priority 5: Auto-download Python 3.12 (64-bit) if not found
echo        Python not detected on system.
echo        Auto-downloading official Python 3.12 (64-bit) installer...
set "PY_INSTALLER=%TEMP%\python_installer_setup.exe"
powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object Net.WebClient).DownloadFile('https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe', '%TEMP%\python_installer_setup.exe')"
if exist "%TEMP%\python_installer_setup.exe" (
    echo        Installing Python 3.12 (silent install with pip and PATH)...
    echo        Please wait 30-60 seconds while Python installs...
    start /wait "" "%TEMP%\python_installer_setup.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_pip=1 SimpleInstall=1
    del "%TEMP%\python_installer_setup.exe" >nul 2>&1
    
    REM Locate newly installed Python
    if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
        set "SYS_PYTHON=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    ) else if exist "C:\Python312\python.exe" (
        set "SYS_PYTHON=C:\Python312\python.exe"
    ) else if exist "C:\Program Files\Python312\python.exe" (
        set "SYS_PYTHON=C:\Program Files\Python312\python.exe"
    ) else (
        for /f "tokens=*" %%I in ('py -3 -c "import sys; print(sys.executable)" 2^>nul') do if "!SYS_PYTHON!"=="" set "SYS_PYTHON=%%I"
        if "!SYS_PYTHON!"=="" (
            where python >nul 2>&1 && for /f "delims=" %%I in ('where python 2^>nul') do if "!SYS_PYTHON!"=="" set "SYS_PYTHON=%%I"
        )
    )
)

if "!SYS_PYTHON!"=="" (
    echo        ERROR: Could not detect or install Python automatically.
    echo        Please install Python manually from: https://www.python.org/downloads/
    echo        IMPORTANT: Make sure to check the box "Add Python to PATH"!
    start https://www.python.org/downloads/
    pause
    exit /b 1
)

:PYTHON_FOUND
for /f "usebackq tokens=*" %%V in (`powershell -NoProfile -Command "& '!SYS_PYTHON!' --version" 2^>nul`) do (
    set "PY_VER=%%V"
)
echo        Base Python executable: !SYS_PYTHON! (!PY_VER!)

REM ── 4. Virtual Environment (venv) Setup ───────────────────────────
echo.
echo  [4/7] Preparing dedicated project virtual environment (venv)...
if not exist "!PROJECT!\venv\Scripts\python.exe" (
    echo        Creating dedicated virtual environment in "!PROJECT!\venv"...
    "!SYS_PYTHON!" -m venv "!PROJECT!\venv"
    if errorlevel 1 (
        echo        WARNING: venv creation had an issue. Falling back to system python.
        set "PYTHON=!SYS_PYTHON!"
    ) else (
        set "PYTHON=!PROJECT!\venv\Scripts\python.exe"
    )
) else (
    set "PYTHON=!PROJECT!\venv\Scripts\python.exe"
)
echo        Virtual environment ready: !PYTHON!

REM ── 5. Pip & Package Dependencies ─────────────────────────────────
echo.
echo  [5/7] Installing/verifying required automation packages...
echo        Upgrading pip, setuptools, and wheel...
"!PYTHON!" -m pip install --upgrade pip setuptools wheel --quiet

if exist "!PROJECT!\requirements.txt" (
    echo        Installing packages from requirements.txt...
    "!PYTHON!" -m pip install -r "!PROJECT!\requirements.txt" --quiet
)
if errorlevel 1 (
    echo        Notice: Installing core automation dependencies directly...
    "!PYTHON!" -m pip install selenium behave webdriver-manager behave-html-formatter python-dotenv colorama requests --quiet
    if errorlevel 1 (
        echo        ERROR: Package installation failed. Retrying with verbose output...
        "!PYTHON!" -m pip install selenium behave webdriver-manager behave-html-formatter python-dotenv colorama requests
        if errorlevel 1 goto INSTALL_FAILED
    )
)
echo        All Python automation packages are installed.

REM ── 6. ChromeDriver & Runtime Folders ─────────────────────────────
echo.
echo  [6/7] Configuring matching ChromeDriver and project folders...

REM Terminate any stale chromedriver processes to prevent file lock
taskkill /F /IM chromedriver.exe >nul 2>&1

REM Auto-sync ChromeDriver matching the installed Chrome version
echo        Syncing ChromeDriver to match installed Chrome...
"!PYTHON!" -c "import os, shutil; from webdriver_manager.chrome import ChromeDriverManager; p = ChromeDriverManager().install(); dest = os.path.join(r'!PROJECT!', 'chromedriver.exe'); shutil.copy2(p, dest) if os.path.isfile(p) else None; print('       Matching ChromeDriver synced successfully.')" 2>nul
if not exist "!PROJECT!\chromedriver.exe" (
    echo        Notice: Selenium Manager will auto-manage ChromeDriver during tests.
) else (
    echo        Local ChromeDriver verified: !PROJECT!\chromedriver.exe
)

REM Ensure all runtime folders exist
for %%D in (features features\steps features\Forms reports screenshots downloads uploads) do (
    if not exist "!PROJECT!\%%D" mkdir "!PROJECT!\%%D"
)

REM Ensure default config.env exists
if not exist "!PROJECT!\config.env" (
    echo        Creating default config.env...
    (
        echo # Login Configuration
        echo LOGIN_URL=https://sbx.acsyscrm.com:8443/ERPWEB/login
        echo TENANT_CODE=T1001
        echo USERNAME=Admin
        echo PASSWORD=12345
        echo.
        echo # Browser Settings
        echo CLOSE_BROWSER_AFTER_TEST=false
        echo BROWSER_MAXIMIZED=true
        echo WAIT_TIMEOUT=10
        echo SHORT_WAIT=2
    ) > "!PROJECT!\config.env"
    echo        Default config.env created.
)

REM ── 7. Verification Health Check ──────────────────────────────────
echo.
echo  [7/7] Performing installation health check...
echo.
echo  ----------------------------------------------------------------
"!PYTHON!" -c "import selenium; print('  [OK] Selenium           v' + selenium.__version__)" 2>nul || echo   [FAIL] Selenium
"!PYTHON!" -c "import behave; print('  [OK] Behave             v' + behave.__version__)" 2>nul || echo   [FAIL] Behave
"!PYTHON!" -c "import webdriver_manager; print('  [OK] WebDriver-Manager  v' + webdriver_manager.__version__)" 2>nul || echo   [FAIL] WebDriver-Manager
"!PYTHON!" -c "import behave_html_formatter; print('  [OK] HTML-Formatter     OK')" 2>nul || echo   [FAIL] HTML-Formatter
"!PYTHON!" -c "import dotenv; print('  [OK] Python-Dotenv      OK')" 2>nul || echo   [FAIL] Python-Dotenv
"!PYTHON!" -c "import colorama; print('  [OK] Colorama           OK')" 2>nul || echo   [FAIL] Colorama

REM Test browser launch
echo.
echo  Testing Chrome browser automation launch...
"!PYTHON!" -c "from selenium import webdriver; o = webdriver.ChromeOptions(); o.add_argument('--headless=new'); d = webdriver.Chrome(options=o); d.quit(); print('  [OK] Chrome automation smoke test PASSED')" 2>nul || echo   [WARNING] Headless Chrome test check had an issue, tests will still attempt live Chrome launch.
echo  ----------------------------------------------------------------

echo.
echo  ================================================================
echo   SETUP COMPLETE - THIS PC IS FULLY READY FOR TESTING!
echo  ================================================================
echo.
echo   How to test:
echo   1. Double-click "BehaveTestRunner.exe"  (Interactive runner)
echo      OR double-click "run_tests.bat"     (Script runner)
echo   2. Select which tests to run from the menu
echo   3. HTML reports will be generated in: !PROJECT!\reports\
echo  ================================================================
echo.
pause
exit /b 0

:INSTALL_FAILED
echo.
echo  ================================================================
echo   ERROR: Package installation could not complete.
echo   Please ensure your internet connection is active and rerun setup.bat
echo  ================================================================
echo.
pause
exit /b 1


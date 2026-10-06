@echo off
REM ================================================================
REM  run_tests.bat  -  AcSys ERP BDD Automation Launcher
REM  Works with Python directly - no EXE rebuild needed
REM ================================================================

if not defined BAT_LOOP (
    set BAT_LOOP=1
    cmd /k "%~f0"
    exit
)

setlocal enabledelayedexpansion

REM ── Project root (folder where this bat lives) ────────────────
set "PROJECT=%~dp0"
if "!PROJECT:~-1!"=="\" set "PROJECT=!PROJECT:~0,-1!"

REM ── Auto-find Python ──────────────────────────────────────────
set "PYTHON="

if exist "!PROJECT!\venv\Scripts\python.exe" (
    set "PYTHON=!PROJECT!\venv\Scripts\python.exe"
    goto PYTHON_FOUND
)

REM Check Windows Python launcher
if "!PYTHON!"=="" (
    for /f "tokens=*" %%I in ('py -3 -c "import sys; print(sys.executable)" 2^>nul') do (
        if "!PYTHON!"=="" if exist "%%I" set "PYTHON=%%I"
    )
)

for %%V in (315 314 313 312 311 310) do (
    if "!PYTHON!"=="" (
        set "TRY=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python%%V\python.exe"
        if exist "!TRY!" set "PYTHON=!TRY!"
        set "TRY=C:\Program Files\Python%%V\python.exe"
        if exist "!TRY!" set "PYTHON=!TRY!"
        set "TRY=C:\Python%%V\python.exe"
        if exist "!TRY!" set "PYTHON=!TRY!"
    )
)

for %%V in (3.15 3.14 3.13 3.12 3.11 3.10) do (
    if "!PYTHON!"=="" (
        set "TRY=C:\Users\%USERNAME%\AppData\Local\Python\pythoncore-%%V-64\python.exe"
        if exist "!TRY!" set "PYTHON=!TRY!"
    )
)

if "!PYTHON!"=="" (
    where python >nul 2>&1
    if not errorlevel 1 (
        for /f "delims=" %%I in ('where python 2^>nul') do (
            if "!PYTHON!"=="" (
                echo "%%I" | findstr /i "WindowsApps" >nul
                if errorlevel 1 set "PYTHON=%%I"
            )
        )
    )
)

:PYTHON_FOUND

REM ================================================================
:MAIN_MENU
cls
cd /d "!PROJECT!"

echo.
echo  ================================================================
echo   AcSys ERP  BDD Automation Runner
echo  ================================================================
echo   Folder  : !PROJECT!
echo   Python  : !PYTHON!
echo   Runner  : BehaveTestRunner.py
echo  ================================================================
echo.

REM ── Pre-flight checks ─────────────────────────────────────────
if "!PYTHON!"=="" (
    echo  ERROR: Python not found!
    echo.
    echo  Please run setup.bat first to install Python.
    echo  Or install manually from: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

if not exist "!PROJECT!\BehaveTestRunner.py" (
    echo  ERROR: BehaveTestRunner.py not found in:
    echo         !PROJECT!
    echo.
    pause
    exit /b 1
)

if not exist "!PROJECT!\features\login.feature" (
    echo  ERROR: features\login.feature not found!
    echo.
    pause
    exit /b 1
)

echo   Main Menu
echo  ----------------------------------------------------------------
echo   1.  Run ALL feature files
echo   2.  Run tests by TAG
echo   3.  Browse and select a feature file
echo   4.  Exit
echo  ----------------------------------------------------------------
echo.
set "MAIN_CHOICE="
set /p MAIN_CHOICE=  Your choice (1-4): 

if "!MAIN_CHOICE!"=="1" goto RUN_ALL
if "!MAIN_CHOICE!"=="2" goto RUN_TAG
if "!MAIN_CHOICE!"=="3" goto BROWSE
if "!MAIN_CHOICE!"=="4" goto BYE

echo  Invalid choice. Please enter 1, 2, 3 or 4.
timeout /t 2 >nul
goto MAIN_MENU

REM ================================================================
REM  1. RUN ALL
REM ================================================================
:RUN_ALL
cls
echo.
echo  ================================================================
echo   Running ALL feature files
echo   Login runs first automatically
echo   Each file gets its own HTML report
echo  ================================================================
echo.

"!PYTHON!" "!PROJECT!\BehaveTestRunner.py" --run-all
set "EXIT_CODE=!errorlevel!"
goto AFTER_RUN

REM ================================================================
REM  2. RUN BY TAG
REM ================================================================
:RUN_TAG
cls
echo.
echo  ================================================================
echo   Run Tests by TAG
echo  ================================================================
echo.
echo  Scanning feature files for tags...
echo.

set /a tagcount=0
set "TAGTMP=!PROJECT!\_tmp_tags_.txt"
if exist "!TAGTMP!" del "!TAGTMP!"

for /f "delims=" %%F in ('dir "!PROJECT!\features\*.feature" /b /s 2^>nul') do (
    for /f "tokens=*" %%L in ('findstr /r /c:"^[ @]*@" "%%F" 2^>nul') do (
        set "LINE=%%L"
        for %%W in (!LINE!) do (
            set "WORD=%%W"
            if "!WORD:~0,1!"=="@" (
                set "RAWTAG=!WORD:~1!"
                if "!RAWTAG:~-1!"=="," set "RAWTAG=!RAWTAG:~0,-1!"
                if not defined SEEN_!RAWTAG! (
                    set "SEEN_!RAWTAG!=1"
                    echo !RAWTAG!>> "!TAGTMP!"
                    set /a tagcount+=1
                )
            )
        )
    )
)

if !tagcount! EQU 0 (
    echo  No @tags found in any feature file.
    echo.
    set "CHOSEN_TAG="
    set /p CHOSEN_TAG=  Enter tag manually e.g. @smoke :
    if "!CHOSEN_TAG!"=="" (
        echo  Tag cannot be empty!
        timeout /t 2 >nul
        goto MAIN_MENU
    )
    if exist "!TAGTMP!" del "!TAGTMP!"
    goto DO_TAG
)

set /a tidx=0
for /f "delims=" %%T in ("!TAGTMP!") do (
    set /a tidx+=1
    set "TAGITEM_!tidx!=%%T"
)
if exist "!TAGTMP!" del "!TAGTMP!"

echo  Found !tagcount! tag(s):
echo.
echo  ----------------------------------------------------------------
for /L %%i in (1,1,!tidx!) do (
    echo   %%i.  @!TAGITEM_%%i!
)
echo  ----------------------------------------------------------------
echo   0.  Back to Main Menu
echo.
set "TAG_CHOICE="
set /p TAG_CHOICE=  Enter number: 

if "!TAG_CHOICE!"=="0" goto MAIN_MENU

set "CHOSEN_TAG=@!TAGITEM_%TAG_CHOICE%!"
if "!CHOSEN_TAG!"=="@" (
    echo  Invalid selection!
    timeout /t 2 >nul
    goto RUN_TAG
)

:DO_TAG
cls
echo.
echo  ================================================================
echo   Running tag: !CHOSEN_TAG!
echo   Login runs first automatically
echo  ================================================================
echo.

"!PYTHON!" "!PROJECT!\BehaveTestRunner.py" --tag "!CHOSEN_TAG!"
set "EXIT_CODE=!errorlevel!"
goto AFTER_RUN

REM ================================================================
REM  3. BROWSE AND SELECT
REM ================================================================
:BROWSE
cls
echo.
echo  ================================================================
echo   Browse and Select a Feature File
echo   Login runs first automatically
echo  ================================================================
echo.

set /a idx=0
set "LAST_DIR=__NONE__"

for /f "delims=" %%F in ('dir "!PROJECT!\features\*.feature" /b /s 2^>nul ^| findstr /v /i "login.feature"') do (
    set "FULL_%%F=%%F"
    set "BFULL=%%F"
    set "BREL=!BFULL:%PROJECT%\=!"
    set /a idx+=1
    set "BITEM_!idx!=!BREL!"

    for %%A in ("%%F") do set "BNAME=%%~nA"

    set "BPAR=!BFULL:%PROJECT%\features\=!"
    for %%A in ("%%F") do set "BPAR=%%~dpA"
    set "BPAR=!BPAR:!PROJECT!\features\=!"
    if "!BPAR:~-1!"=="\" set "BPAR=!BPAR:~0,-1!"
    REM Remove trailing backslash if any
    if "!BPAR:~-1!"=="\" set "BPAR=!BPAR:~0,-1!"

    if not "!BPAR!"=="!LAST_DIR!" (
        echo.
        echo   -- !BPAR! --
        set "LAST_DIR=!BPAR!"
    )
    echo      !idx!.  !BNAME!
)

if !idx! EQU 0 (
    echo  No feature files found apart from login.feature
    timeout /t 3 >nul
    goto MAIN_MENU
)

echo.
echo  ----------------------------------------------------------------
echo    0.  Back to Main Menu
echo  ----------------------------------------------------------------
echo.
set "BROWSE_CHOICE="
set /p BROWSE_CHOICE=  Enter number: 

if "!BROWSE_CHOICE!"=="0" goto MAIN_MENU
if "!BROWSE_CHOICE!"=="" goto BROWSE

REM Validate numeric
set /a BROWSE_NUM=!BROWSE_CHOICE!+0
if !BROWSE_NUM! LSS 1 (
    echo  Invalid number. Please try again.
    timeout /t 2 >nul
    goto BROWSE
)
if !BROWSE_NUM! GTR !idx! (
    echo  Invalid number. Please try again.
    timeout /t 2 >nul
    goto BROWSE
)

for %%N in (!BROWSE_NUM!) do set "SEL=!BITEM_%%N!"
if "!SEL!"=="" (
    echo  Invalid number. Please try again.
    timeout /t 2 >nul
    goto BROWSE
)

cls
echo.
echo  ================================================================
echo   Running: !SEL!
echo   Login runs first automatically
echo  ================================================================
echo.

"!PYTHON!" "!PROJECT!\BehaveTestRunner.py" --feature "!SEL!"
set "EXIT_CODE=!errorlevel!"
goto AFTER_RUN

REM ================================================================
REM  AFTER RUN
REM ================================================================
:AFTER_RUN
echo.
echo  ================================================================
if !EXIT_CODE! EQU 0 (
    echo   ALL TESTS PASSED
) else if !EXIT_CODE! EQU 2 (
    echo   TESTS PASSED with warnings
) else (
    echo   SOME TESTS FAILED
    echo   Screenshots: !PROJECT!\screenshots\
)
echo  ================================================================
echo   Reports: !PROJECT!\reports\
echo  ================================================================
echo.

set "OPEN_REP="
set /p OPEN_REP=  Open reports folder? (y/n default=y): 
if "!OPEN_REP!"=="" set "OPEN_REP=y"
if /i "!OPEN_REP!"=="y" explorer "!PROJECT!\reports"

echo.
echo  Press any key to return to Main Menu
echo  Close this window to Exit
echo.
pause >nul
goto MAIN_MENU

REM ================================================================
REM  EXIT
REM ================================================================
:BYE
echo.
echo  Goodbye!
timeout /t 1 >nul
exit /b 0

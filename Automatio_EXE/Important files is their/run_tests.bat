

@echo off
if not defined BAT_LOOP (
    set BAT_LOOP=1
    cmd /k "%~f0"
    exit
)

setlocal enabledelayedexpansion

:MAIN_MENU
cls

cd /d "%~dp0"

echo.
echo ========================================
echo    Behave Test Runner
echo ========================================
echo.
echo Current folder: %cd%
echo.

REM Check if executable exists
if not exist "BehaveTestRunner.exe" (
    echo ========================================
    echo ERROR: BehaveTestRunner.exe not found!
    echo ========================================
    echo Please ensure the executable is in this folder.
    echo.
    pause
    exit /b 1
)

echo ==========================
echo Main Menu:
echo ==========================
echo.
echo 1. Run ALL tests (login + all features)
echo 2. Run tests with TAG
echo 3. Browse and select feature/folder
echo 4. Exit
echo.

set /p MAIN_CHOICE=Enter your choice (1-4): 

if "%MAIN_CHOICE%"=="1" goto RUN_ALL
if "%MAIN_CHOICE%"=="2" goto RUN_TAG
if "%MAIN_CHOICE%"=="3" goto BROWSE_SELECT
if "%MAIN_CHOICE%"=="4" goto EXIT_SCRIPT

echo Invalid choice. Please try again.
timeout /t 2 >nul
goto MAIN_MENU

REM ========================================
REM Run ALL tests
REM ========================================
:RUN_ALL
cls
echo.
echo Running ALL tests (login first, then all features)...
echo.
set "TARGET=features"
set "TARGET_TYPE=all"
goto GET_OPTIONS

REM ========================================
REM Run tests with TAG
REM ========================================
:RUN_TAG
cls
echo.
echo ========================================
echo  Scanning feature files for tags...
echo ========================================
echo.

set /a tagcount=0
set "TAGTMP=%cd%\_temp_tags.txt"
del "%TAGTMP%" >nul 2>&1

REM Scan all feature files for lines starting with @ and extract tags
for /f "delims=" %%F in ('dir "features\*.feature" /b /s 2^>nul') do (
    for /f "tokens=*" %%L in ('findstr /r /c:"^[ @]*@" "%%F" 2^>nul') do (
        set "LINE=%%L"
        REM Process each word in the line that starts with @
        for %%W in (!LINE!) do (
            set "WORD=%%W"
            if "!WORD:~0,1!"=="@" (
                REM Strip leading @ for storage
                set "RAWTAG=!WORD:~1!"
                REM Remove any trailing comma
                if "!RAWTAG:~-1!"=="," set "RAWTAG=!RAWTAG:~0,-1!"
                REM Dedup using in-memory flag — avoids broken findstr loop
                if not defined SEEN_!RAWTAG! (
                    set "SEEN_!RAWTAG!=1"
                    echo !RAWTAG!>> "%TAGTMP%"
                    set /a tagcount+=1
                )
            )
        )
    )
)

if !tagcount! EQU 0 (
    echo No tags found in any feature files.
    echo.
    set /p TAG=Enter tag name manually ^(with @^): 
    if "!TAG!"=="" (
        echo Error: Tag cannot be empty.
        timeout /t 2 >nul
        goto MAIN_MENU
    )
    del "%TAGTMP%" >nul 2>&1
    set "TARGET=!TAG!"
    set "TARGET_TYPE=tag"
    goto GET_OPTIONS
)

REM Build numbered tag list
set /a tidx=0
for /f "delims=" %%T in (%TAGTMP%) do (
    set /a tidx+=1
    set "TAG_!tidx!=%%T"
)
del "%TAGTMP%" >nul 2>&1

REM Display tag menu
echo  Found !tagcount! tag(s) across all feature files:
echo.
echo ----------------------------------------
for /L %%i in (1,1,!tidx!) do (
    echo    %%i^)  @!TAG_%%i!
)
echo ----------------------------------------
echo.
echo   0^)  Back to Main Menu
echo.
set /p TAG_CHOICE=Enter number: 

if "!TAG_CHOICE!"=="0" goto MAIN_MENU

set "CHOSEN_TAG=!TAG_!TAG_CHOICE!!"
if "!CHOSEN_TAG!"=="" (
    echo Invalid choice!
    timeout /t 2 >nul
    goto RUN_TAG
)

set "TARGET=@!CHOSEN_TAG!"
set "TARGET_TYPE=tag"
goto GET_OPTIONS

REM ========================================
REM Browse and Select
REM ========================================
:BROWSE_SELECT
cls
echo.
echo ========================================
echo  Browse Features / Folders
echo ========================================
echo.
echo NOTE: Login will run first automatically
echo.

set /a idx=0

REM Collect all feature files EXCEPT login.feature
for /f "delims=" %%F in ('dir "features\*.feature" /b /s 2^>nul ^| findstr /v /i "login.feature"') do (
    set "FULL_PATH=%%F"
    set "REL_PATH=!FULL_PATH:%cd%\=!"
    set /a idx+=1
    set "ITEM_!idx!=!REL_PATH!"
    set "TYPE_!idx!=file"
)

REM Collect all folders containing feature files
for /f "delims=" %%D in ('dir "features" /b /s /ad 2^>nul') do (
    dir "%%D\*.feature" /b >nul 2>&1
    if not errorlevel 1 (
        set "FULL_PATH=%%D"
        set "REL_PATH=!FULL_PATH:%cd%\=!"
        set /a idx+=1
        set "ITEM_!idx!=!REL_PATH!"
        set "TYPE_!idx!=folder"
    )
)

if !idx! EQU 0 (
    echo No feature files found!
    timeout /t 2 >nul
    goto MAIN_MENU
)

REM ── Display items grouped neatly ──────────────────────────────────────
set "TMPFILE=%cd%\_temp_menu.txt"
del "%TMPFILE%" >nul 2>&1

set "LAST_PARENT="

for /L %%i in (1,1,!idx!) do (
    set "CURRENT=!ITEM_%%i!"
    set "FTYPE=!TYPE_%%i!"

    if "!FTYPE!"=="folder" (
        REM --- derive short folder name ---
        for %%A in ("!CURRENT!") do set "SHORT=%%~nxA"
        REM --- derive parent path to use as group header ---
        for %%A in ("!CURRENT!") do set "PARENT=%%~dpA"
        set "PARENT=!PARENT:features\=!"
        set "PARENT=!PARENT:~0,-1!"

        echo. >> "%TMPFILE%"
        echo   [FOLDER]  %%i^)  !SHORT! >> "%TMPFILE%"
    ) else (
        REM --- derive file name and its immediate parent folder ---
        for %%A in ("!CURRENT!") do set "FNAME=%%~nA"
        for %%A in ("!CURRENT!") do set "FPARENT=%%~dpA"
        REM strip leading path up to features\
        set "FPARENT=!FPARENT:*features\=!"
        REM remove trailing backslash
        if "!FPARENT:~-1!"=="\" set "FPARENT=!FPARENT:~0,-1!"

        REM Print a group header when the parent folder changes
        if not "!FPARENT!"=="!LAST_PARENT!" (
            echo. >> "%TMPFILE%"
            if "!FPARENT!"=="" (
                echo   -- Root Features -- >> "%TMPFILE%"
            ) else (
                echo   -- !FPARENT! -- >> "%TMPFILE%"
            )
            set "LAST_PARENT=!FPARENT!"
        )

        echo      %%i^)  !FNAME! >> "%TMPFILE%"
    )
)

type "%TMPFILE%"
del "%TMPFILE%" >nul 2>&1

echo.
echo ----------------------------------------
echo   0^)  Back to Main Menu
echo ----------------------------------------
echo.
set /p BROWSE_CHOICE=Enter number: 

if "%BROWSE_CHOICE%"=="0" goto MAIN_MENU

set "TARGET=!ITEM_%BROWSE_CHOICE%!"
set "TARGET_TYPE=!TYPE_%BROWSE_CHOICE%!"

if "!TARGET!"=="" (
    echo Invalid choice!
    timeout /t 2 >nul
    goto BROWSE_SELECT
)

goto GET_OPTIONS

REM ========================================
REM Get execution options
REM ========================================
:GET_OPTIONS
cls
echo.
echo ==========================
echo Execution Options:
echo ==========================
echo.

REM Option 1: Show logs (DEFAULT = y)
set "SHOW_LOGS="
set /p SHOW_LOGS=Show logs in terminal? (y/n, default=y): 
if "%SHOW_LOGS%"=="" set "SHOW_LOGS=y"
if /i "%SHOW_LOGS%"=="y" (
    set "LOG_OPTIONS=--no-capture --no-capture-stderr"
) else (
    set "LOG_OPTIONS="
)

REM Option 2: Generate HTML report
set "GEN_REPORT="
set /p GEN_REPORT=Generate HTML report? (y/n, default=y): 
if "%GEN_REPORT%"=="" set "GEN_REPORT=y"

if /i "%GEN_REPORT%"=="y" (
    if not exist "reports" mkdir reports

    REM Generate timestamp
    for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value 2^>nul') do set datetime=%%I
    set "TIMESTAMP=!datetime:~0,8!_!datetime:~8,6!"

    set "REPORT_FILE=reports\test_report_!TIMESTAMP!.html"
    set "REPORT_OPTIONS=-f behave_html_formatter:HTMLFormatter -o !REPORT_FILE!"
) else (
    set "REPORT_OPTIONS=--format pretty"
)

goto RUN_TESTS

REM ========================================
REM Execute the tests
REM ========================================
:RUN_TESTS
cls
echo.
echo ========================================
echo Running Behave Tests
echo ========================================
echo.

if "!TARGET_TYPE!"=="all" (
    echo Target: LOGIN + ALL FEATURES
    set "BEHAVE_ARGS=features\login.feature features !LOG_OPTIONS! !REPORT_OPTIONS!"
) else if "!TARGET_TYPE!"=="tag" (
    echo Target: LOGIN + TAG !TARGET!
    set "BEHAVE_ARGS=features\login.feature --tags !TARGET! !LOG_OPTIONS! !REPORT_OPTIONS!"
) else if "!TARGET_TYPE!"=="folder" (
    echo Target: LOGIN + FOLDER !TARGET!
    set "BEHAVE_ARGS=features\login.feature !TARGET! !LOG_OPTIONS! !REPORT_OPTIONS!"
) else if "!TARGET_TYPE!"=="file" (
    echo Target: LOGIN + FEATURE !TARGET!
    set "BEHAVE_ARGS=features\login.feature !TARGET! !LOG_OPTIONS! !REPORT_OPTIONS!"
)

if not "!LOG_OPTIONS!"=="" echo Logs: Enabled
if /i "!GEN_REPORT!"=="y" echo Report: !REPORT_FILE!
echo.
echo --------------------------
echo.

echo Command: BehaveTestRunner.exe !BEHAVE_ARGS!
echo.
BehaveTestRunner.exe !BEHAVE_ARGS!
set "EXIT_CODE=!errorlevel!"

if !EXIT_CODE! GEQ 9009 (
    echo.
    echo --------------------------
    echo Executable not found, trying: python -m behave
    echo --------------------------
    echo.

    where python >nul 2>&1
    if not errorlevel 1 (
        echo Command: python -m behave !BEHAVE_ARGS!
        echo.
        python -m behave !BEHAVE_ARGS!
        set "EXIT_CODE=!errorlevel!"
    ) else (
        echo ERROR: Python not found. Cannot run behave.
        set "EXIT_CODE=1"
    )
)

echo.
echo --------------------------
echo.

if !EXIT_CODE! EQU 0 (
    echo ========================================
    echo    TESTS PASSED!
    echo ========================================
    goto GENERATE_REPORT
)
if !EXIT_CODE! EQU 2 (
    echo ========================================
    echo    TESTS PASSED! ^(with warnings^)
    echo ========================================
    goto GENERATE_REPORT
)
echo ========================================
echo    TESTS FAILED!
echo    Exit Code: !EXIT_CODE!
echo ========================================

:GENERATE_REPORT

if /i "!GEN_REPORT!"=="y" (
    if exist "!REPORT_FILE!" (
        echo.
        echo ========================================
        echo HTML Report Generated
        echo ========================================
        echo Standard Report: !REPORT_FILE!

        if exist "convert_report_to_table.py" (
            echo.
            echo Generating Confluence report...
            python convert_report_to_table.py "!REPORT_FILE!"
            
            for %%F in ("!REPORT_FILE!") do set "REPORT_DIR=%%~dpF"
            for %%F in ("!REPORT_FILE!") do set "REPORT_NAME=%%~nxF"
            set "CONFLUENCE_REPORT=!REPORT_DIR!confluence_!REPORT_NAME!"
            
            if exist "!CONFLUENCE_REPORT!" (
                echo Confluence Report: !CONFLUENCE_REPORT!
            )
        )

        echo.
        echo ========================================
        set /p OPEN_REPORT=Open report in browser? (y/n, default=y): 
        if "!OPEN_REPORT!"=="" set "OPEN_REPORT=y"
        if /i "!OPEN_REPORT!"=="y" (
            if exist "!CONFLUENCE_REPORT!" (
                echo Opening Confluence report...
                start "" "!CONFLUENCE_REPORT!"
            ) else (
                echo Opening standard report...
                start "" "!REPORT_FILE!"
            )
        )
    ) else (
        echo.
        echo Warning: HTML report was not generated.
    )
)

echo.
echo ==========================
echo Task completed.
echo ==========================
echo.
echo Press any key to return to main menu
echo Close window to exit
echo ==========================
pause >nul
goto MAIN_MENU

:EXIT_SCRIPT
echo.
echo Exiting...
exit /b 0

@echo off
setlocal enabledelayedexpansion
REM pingslo interactive runner - easy way to run the tool

REM activate virtual environment if it exists
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else (
    echo Warning: Virtual environment not found. Run setup.bat first.
    echo.
    pause
    exit /b 1
)

:menu
cls
echo ========================================
echo        PingSLO - Network Monitor
echo ========================================
echo.
echo Select Probe Mode:
echo   1. TCP Connection Time
echo   2. HTTP Time-To-First-Byte (TTFB)
echo   3. Configure SLO Thresholds
echo   4. Exit
echo.
set /p mode="Enter choice (1-4): "

if "%mode%"=="4" exit /b 0
if "%mode%"=="3" goto configure_slo
if "%mode%"=="1" set probe_mode=tcp
if "%mode%"=="2" set probe_mode=http

if not defined probe_mode (
    echo Invalid choice. Please try again.
    timeout /t 2 >nul
    goto menu
)

echo.
echo ========================================
echo    Enter Targets (Websites/URLs)
echo ========================================
echo.
echo Enter websites one at a time.
echo Examples: google.com, github.com:443, https://example.com
echo Type 'done' when finished.
echo.

REM create temp file for targets
set targets_file=temp_targets.txt
if exist %targets_file% del %targets_file%

:input_targets
set /p target="Enter target (or 'done'): "

if /i "%target%"=="done" goto check_targets
if "%target%"=="" goto input_targets

REM validate target format
echo %target% | findstr /r "^[a-zA-Z0-9.-]*\(:[0-9]*\)\?$" >nul
if errorlevel 1 (
    echo %target% | findstr /r "^https\?://" >nul
    if errorlevel 1 (
        echo   Warning: '%target%' may have invalid format. Continue anyway? (y/n^)
        set /p continue_anyway=
        if /i not "!continue_anyway!"=="y" goto input_targets
    )
)

REM add to temp file
echo %target% >> %targets_file%
echo   Added: %target%
goto input_targets

:check_targets
REM check if any targets were entered
if not exist %targets_file% (
    echo.
    echo Error: No targets entered!
    timeout /t 2 >nul
    goto menu
)

REM count lines in file
set target_count=0
for /f %%a in ('type %targets_file% ^| find /c /v ""') do set target_count=%%a

if %target_count%==0 (
    echo.
    echo Error: No targets entered!
    del %targets_file%
    timeout /t 2 >nul
    goto menu
)

echo.
echo ========================================
echo         Configuration Options
echo ========================================
echo.
set /p samples="Number of samples per target (default 10): "
if "%samples%"=="" set samples=10

echo.
set /p json_output="Save results to JSON file? (y/n, default n): "

echo.
echo ========================================
echo      Running Probes - Please Wait
echo ========================================
echo.
echo Mode: %probe_mode%
echo Targets: %target_count%
echo Samples: %samples%
echo.

REM build command
set use_config=
if exist config.yaml set use_config=--config config.yaml

if /i "%json_output%"=="y" (
    set output_file=report_!date:~-4!!date:~4,2!!date:~7,2!_!time:~0,2!!time:~3,2!!time:~6,2!.json
    set output_file=!output_file: =0!
    python main.py run --targets %targets_file% --mode %probe_mode% --samples %samples% %use_config% --out !output_file!
) else (
    python main.py run --targets %targets_file% --mode %probe_mode% --samples %samples% %use_config%
)

set exit_code=%errorlevel%

REM cleanup
del %targets_file%

if %exit_code% neq 0 (
    echo.
    echo ========================================
    echo   ERROR: Some targets failed to probe
    echo ========================================
    echo.
    echo Possible causes:
    echo   - Invalid hostname or URL format
    echo   - Network connectivity issues
    echo   - DNS resolution failure
    echo   - Firewall blocking connections
    echo   - Target server unreachable
    echo.
    echo Please check your targets and try again.
    echo.
    pause
    goto menu
)

echo.
echo ========================================
echo.
set /p again="Run another test? (y/n): "
if /i "%again%"=="y" goto menu

echo.
echo Thank you for using PingSLO!
timeout /t 2 >nul
exit /b 0

:configure_slo
cls
echo ========================================
echo      Configure SLO Thresholds
echo ========================================
echo.
echo Current config file: config.yaml
if exist config.yaml (
    echo Status: EXISTS
    echo.
    type config.yaml
) else (
    echo Status: NOT FOUND - will create new one
)
echo.
echo ========================================
echo.
echo Enter new threshold values (press Enter to keep current):
echo.

set /p p95_threshold="P95 latency threshold in ms (default 100): "
if "%p95_threshold%"=="" set p95_threshold=100

set /p p99_threshold="P99 latency threshold in ms (leave empty to disable): "

set /p loss_threshold="Max loss percentage (default 5.0): "
if "%loss_threshold%"=="" set loss_threshold=5.0

echo.
echo Creating config.yaml with:
echo   P95 Threshold: %p95_threshold% ms
if not "%p99_threshold%"=="" (
    echo   P99 Threshold: %p99_threshold% ms
) else (
    echo   P99 Threshold: disabled
)
echo   Max Loss: %loss_threshold%%%
echo.

REM create config.yaml
(
echo # SLO Configuration
echo # Generated by PingSLO interactive menu
echo.
echo default_slo:
echo   latency_p95_ms: %p95_threshold%
if not "%p99_threshold%"=="" (
    echo   latency_p99_ms: %p99_threshold%
) else (
    echo   latency_p99_ms: null
)
echo   max_loss_pct: %loss_threshold%
echo.
echo # Per-target overrides example:
echo # target_slos:
echo #   slowserver.example.com:
echo #     latency_p95_ms: 500
echo #     max_loss_pct: 10.0
) > config.yaml

echo.
echo Config saved to config.yaml
echo.
pause
goto menu

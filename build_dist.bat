@echo off
title Build Distribution
echo =========================================
echo    Building Distribution Package
echo =========================================
echo.

set ZIP_NAME=utem_crawler_package.zip

echo [INFO] Preparing files for compression...

:: Check if old zip exists and delete it
if exist "%ZIP_NAME%" (
    del "%ZIP_NAME%"
)

:: Compress the necessary files using Windows native tar
tar -a -c -f "%ZIP_NAME%" app.py scraper_raw.py requirements.txt start_crawler.bat

if %errorlevel% neq 0 (
    echo [ERROR] Failed to create the zip file.
) else (
    echo [SUCCESS] Successfully created %ZIP_NAME%!
    echo You can now share this zip file with others.
)

echo.
pause

@echo off
REM ============================================================
REM  build.bat - Decaf Mini-Compiler Build Script (Windows)
REM  CS-471L Compiler Construction Lab, UET Lahore
REM ============================================================

set PYTHON=python
set SRC=src
set TEST=test
set OUT=output

echo.
echo =============================================
echo   Decaf Mini-Compiler Build Script
echo   CS-471L - UET Lahore - Spring 2026
echo =============================================
echo.

if "%1"=="" goto help
if "%1"=="help" goto help
if "%1"=="test" goto test
if "%1"=="all" goto all
if "%1"=="lexer" goto lexer
if "%1"=="rd" goto rd
if "%1"=="ll" goto ll
if "%1"=="lr" goto lr
if "%1"=="symtab" goto symtab
if "%1"=="first-follow" goto firstfollow
if "%1"=="ll-table" goto lltable
if "%1"=="lr-table" goto lrtable
if "%1"=="clean" goto clean

echo Unknown target: %1
goto help

REM ----------------------------------------------------------------
:test
echo Running all test files...
echo.
for %%f in (%TEST%\test*.decaf) do (
    echo === Testing %%f ===
    %PYTHON% %SRC%\main.py %%f --all
    echo.
)
goto end

REM ----------------------------------------------------------------
:all
if "%2"=="" (
    echo Error: Please provide a source file.  e.g. build.bat all test\test1_valid.decaf
    goto end
)
echo Running all modules on %2 ...
%PYTHON% %SRC%\main.py %2 --all
goto end

REM ----------------------------------------------------------------
:lexer
if "%2"=="" set FILE=%TEST%\test1_valid.decaf
if not "%2"=="" set FILE=%2
echo Running lexer on %FILE% ...
%PYTHON% %SRC%\main.py %FILE% --lexer
goto end

REM ----------------------------------------------------------------
:rd
if "%2"=="" set FILE=%TEST%\test1_valid.decaf
if not "%2"=="" set FILE=%2
echo Running recursive descent parser on %FILE% ...
%PYTHON% %SRC%\main.py %FILE% --rd --symtab
goto end

REM ----------------------------------------------------------------
:ll
if "%2"=="" set FILE=%TEST%\test1_valid.decaf
if not "%2"=="" set FILE=%2
echo Running LL(1) parser on %FILE% ...
%PYTHON% %SRC%\main.py %FILE% --ll
goto end

REM ----------------------------------------------------------------
:lr
if "%2"=="" set FILE=%TEST%\test1_valid.decaf
if not "%2"=="" set FILE=%2
echo Running SLR(1) parser on %FILE% ...
%PYTHON% %SRC%\main.py %FILE% --lr
goto end

REM ----------------------------------------------------------------
:symtab
if "%2"=="" set FILE=%TEST%\test1_valid.decaf
if not "%2"=="" set FILE=%2
echo Running RD parser with symbol table on %FILE% ...
%PYTHON% %SRC%\main.py %FILE% --rd --symtab
goto end

REM ----------------------------------------------------------------
:firstfollow
if "%2"=="" set FILE=%TEST%\test1_valid.decaf
if not "%2"=="" set FILE=%2
echo Printing FIRST and FOLLOW sets for %FILE% ...
%PYTHON% %SRC%\main.py %FILE% --first --follow
goto end

REM ----------------------------------------------------------------
:lltable
if "%2"=="" set FILE=%TEST%\test1_valid.decaf
if not "%2"=="" set FILE=%2
echo Printing LL(1) parse table for %FILE% ...
%PYTHON% %SRC%\main.py %FILE% --ll-table
goto end

REM ----------------------------------------------------------------
:lrtable
if "%2"=="" set FILE=%TEST%\test1_valid.decaf
if not "%2"=="" set FILE=%2
echo Printing SLR(1) action/goto table for %FILE% ...
%PYTHON% %SRC%\main.py %FILE% --lr-table
goto end

REM ----------------------------------------------------------------
:clean
echo Cleaning output directory and Python caches...
if exist %OUT%\*.txt del /q %OUT%\*.txt
for /r . %%d in (__pycache__) do (
    if exist "%%d" rmdir /s /q "%%d"
)
del /s /q *.pyc 2>nul
echo Done.
goto end

REM ----------------------------------------------------------------
:help
echo Usage: build.bat [target] [sourcefile]
echo.
echo Targets:
echo   test          Run all test files through all parsers
echo   all           Run all modules on sourcefile
echo   lexer         Run lexer only
echo   rd            Run recursive descent parser + symbol table
echo   ll            Run LL(1) predictive parser
echo   lr            Run SLR(1) parser
echo   symtab        Run RD parser with symbol table dump
echo   first-follow  Print FIRST and FOLLOW sets
echo   ll-table      Print LL(1) parse table
echo   lr-table      Print SLR(1) action/goto table
echo   clean         Remove output files and Python caches
echo.
echo Examples:
echo   build.bat test
echo   build.bat lexer test\test1_valid.decaf
echo   build.bat rd    test\test2_class.decaf
echo   build.bat all   test\test3_complex.decaf

:end
echo.

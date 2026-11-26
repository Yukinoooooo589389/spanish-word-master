@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
title 打包 Palabra

set "PY=python"
where python >nul 2>nul
if errorlevel 1 set "PY=py -3"

echo [1/3] 检查 PyInstaller ...
%PY% -m PyInstaller --version >nul 2>nul
if errorlevel 1 (
  echo       未安装，正在安装 ...
  %PY% -m pip install --disable-pip-version-check -q pyinstaller
  if errorlevel 1 goto fail
)

echo [2/3] 生成图标 ...
%PY% tools\make_icon.py

echo [3/3] 打包为免安装程序 ...
%PY% -m PyInstaller --noconfirm --clean --windowed ^
  --name Palabra ^
  --icon build\palabra.ico ^
  --add-data "data;data" ^
  --exclude-module PySide6.QtQml ^
  --exclude-module PySide6.QtQuick ^
  --exclude-module PySide6.QtQuickWidgets ^
  --exclude-module PySide6.QtWebEngineCore ^
  --exclude-module PySide6.QtWebEngineWidgets ^
  --exclude-module PySide6.QtMultimedia ^
  --exclude-module PySide6.QtCharts ^
  --exclude-module PySide6.QtSql ^
  --exclude-module PySide6.QtTest ^
  --exclude-module PySide6.Qt3DCore ^
  --exclude-module tkinter ^
  run.py
if errorlevel 1 goto fail

copy /y "使用说明.txt" "dist\Palabra\使用说明.txt" >nul 2>nul
echo.
echo 打包完成： dist\Palabra\Palabra.exe
echo 把整个 dist\Palabra 文件夹压缩后发给别人即可，对方不需要安装 Python。
pause
exit /b 0

:fail
echo.
echo 打包失败，请把上面的错误信息发给我。
pause
exit /b 1

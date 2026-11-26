@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
title Palabra · 背西班牙语单词

set "PY="
where python >nul 2>nul
if not errorlevel 1 set "PY=python"
if not defined PY (
  where py >nul 2>nul
  if not errorlevel 1 set "PY=py -3"
)
if not defined PY goto nopython

%PY% -c "import PySide6" >nul 2>nul
if errorlevel 1 goto install
goto run

:install
echo.
echo 首次运行：正在安装界面依赖 PySide6，大约 70MB，请保持联网 ...
%PY% -m pip install --disable-pip-version-check -q -r requirements.txt
if errorlevel 1 goto pipfail

:run
%PY% run.py %*
if errorlevel 1 goto runfail
exit /b 0

:nopython
echo.
echo [错误] 没有找到 Python。
echo 请安装 Python 3.10 以上版本，安装时务必勾选 "Add Python to PATH"。
echo 解法二：让有 Python 的电脑双击 打包.bat 生成 exe，
echo         再把 dist\Palabra 整个文件夹发给你，双击 Palabra.exe 即可。
echo.
pause
exit /b 1

:pipfail
echo.
echo [错误] 依赖安装失败，通常是网络或代理问题。请手动执行：
echo     %PY% -m pip install PySide6-Essentials
echo.
pause
exit /b 1

:runfail
echo.
echo [错误] 程序启动失败。请把以下命令的输出发给我：
echo     %PY% run.py --selftest
echo.
pause
exit /b 1

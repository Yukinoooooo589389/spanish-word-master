"""生成 Windows 批处理文件：统一 CRLF + 指定编码，避免 cmd 解析翻车。

cmd.exe 对批处理的编码/换行很敏感：
  · 必须是 CRLF，否则 if/() 块和标签会被误解析；
  · UTF-8 无 BOM 时中文会被当成 GBK 读，尾字节吃掉后面的引号/括号，
    于是出现 `'ide6" >nul' is not recognized` 这种报错。
这里默认写 UTF-8 with BOM + CRLF（Win10/11 的 cmd 认得 BOM）。
"""
from __future__ import annotations

import sys
from pathlib import Path

LAUNCH = r"""@echo off
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
"""

PACK = r"""@echo off
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
"""

ROOT = Path(__file__).resolve().parents[1]


def write_bat(path: Path, text: str, encoding: str) -> None:
    data = text.replace("\r\n", "\n").replace("\n", "\r\n").encode(encoding)
    if encoding == "utf-8-sig":
        data = b"\xef\xbb\xbf" + text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8")
    path.write_bytes(data)


def main() -> int:
    encoding = sys.argv[1] if len(sys.argv) > 1 else "utf-8-sig"
    write_bat(ROOT / "启动.bat", LAUNCH, encoding)
    write_bat(ROOT / "打包.bat", PACK, encoding)
    for name in ("启动.bat", "打包.bat"):
        raw = (ROOT / name).read_bytes()
        print(f"{name}: {len(raw)} bytes, CRLF={raw.count(b'\r\n')}, "
              f"LF={raw.count(b'\n')}, BOM={raw[:3] == b'\xef\xbb\xbf'}, enc={encoding}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
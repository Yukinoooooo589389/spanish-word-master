"""语音朗读：走 Windows 内置 SAPI，优先挑选西班牙语语音。"""
from __future__ import annotations

import os
import subprocess
import tempfile
import threading
from pathlib import Path


def _speak_sync(text: str) -> None:
    if os.name != "nt" or not text.strip():
        return
    try:
        path = Path(tempfile.gettempdir()) / "palabra_speak.txt"
        path.write_text(text, encoding="utf-8")
        script = (
            "Add-Type -AssemblyName System.Speech;"
            "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer;"
            "$v=$s.GetInstalledVoices()|Where-Object{$_.VoiceInfo.Culture.Name -like 'es*'}|Select-Object -First 1;"
            "if($v){$s.SelectVoice($v.VoiceInfo.Name)};"
            "$s.Rate=-1;"
            f"$t=Get-Content -Raw -Encoding UTF8 '{path}';"
            "$s.Speak($t)"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden", "-Command", script],
            creationflags=0x08000000,
            timeout=25,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return


def speak(text: str) -> None:
    threading.Thread(target=_speak_sync, args=(text,), daemon=True).start()
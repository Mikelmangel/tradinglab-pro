#!/usr/bin/env python3
"""TradingLab Pro — Instalador Multiplataforma"""
import sys, os, subprocess, platform
from pathlib import Path

R="\033[0m"; G="\033[92m"; Y="\033[93m"; C="\033[96m"; B="\033[1m"
def c(t,col): return f"{col}{t}{R}" if sys.stdout.isatty() else t

def header():
    print()
    print(c("╔══════════════════════════════════════════════════════╗",C))
    print(c("║       TradingLab Pro v2.0 — Instalador               ║",C))
    print(c("║  Bar-by-Bar · MTF · Fundamentales · IA · ML · Replay ║",C))
    print(c("╚══════════════════════════════════════════════════════╝",C))
    print()

def main():
    header()
    base = Path(__file__).parent.parent.resolve()
    print(c(f"  📂  {base}\n",C))

    v = sys.version_info
    print(c(f"  🐍  Python {v.major}.{v.minor}.{v.micro}",C))
    if v < (3,10): print(c("  ❌ Requiere Python 3.10+","\033[91m")); sys.exit(1)
    print(c("  ✅ Python OK",G))

    venv = base/".venv"
    if not venv.exists():
        print(c("  📦  Creando entorno virtual...",C))
        subprocess.check_call([sys.executable,"-m","venv",str(venv)])
    pip = venv/("Scripts/pip.exe" if platform.system()=="Windows" else "bin/pip")
    py  = venv/("Scripts/python.exe" if platform.system()=="Windows" else "bin/python")

    print(c("  📥  Instalando dependencias...\n",C))
    subprocess.check_call([str(pip),"install","--upgrade","pip","-q"])
    subprocess.check_call([str(pip),"install","-r",str(base/"requirements.txt")])

    if platform.system()=="Windows":
        bat=base/"TradingLab Pro.bat"
        bat.write_text(f'@echo off\ntitle TradingLab Pro\n"{py}" "{base/"main.py"}"\npause\n')
        try:
            desk=Path.home()/"Desktop"/"TradingLab Pro.bat"
            desk.write_text(f'@echo off\ncd /d "{base}"\n"{py}" "{base/"main.py"}"\n')
        except: pass
    else:
        sh=base/"run.sh"
        sh.write_text(f'#!/bin/bash\ncd "{base}"\n"{py}" "{base/"main.py"}"\n')
        sh.chmod(0o755)
        if platform.system()=="Linux":
            try:
                df=Path.home()/"Desktop"/"TradingLabPro.desktop"
                df.write_text(f"[Desktop Entry]\nName=TradingLab Pro\nExec={sh}\nTerminal=false\nType=Application\n")
                df.chmod(0o755)
            except: pass

    print(c("\n╔══════════════════════════════════════════════════════╗",G))
    print(c("║  ✅  ¡Instalación completada!                        ║",G))
    print(c("╚══════════════════════════════════════════════════════╝",G))
    print(c("  Windows: TradingLab Pro.bat  |  Linux/Mac: ./run.sh\n",G))

if __name__=="__main__": main()

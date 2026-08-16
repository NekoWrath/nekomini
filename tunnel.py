#!/usr/bin/env python3
"""
🌐 One-Click Tunnel Helper for Telegram Mini App
Автоматически создает бесплатный публичный HTTPS-туннель для port 8000.
"""

import subprocess
import shutil
import sys
import time

def main():
    print("""
=============================================================
   🌐 БЫСТРЫЙ ПРОБРОС ПОРТА ДЛЯ TELEGRAM MINI APP
=============================================================
""")

    # 1. Check if ngrok is installed
    if shutil.which("ngrok"):
        print("🚀 Запуск туннеля через ngrok...")
        subprocess.run(["ngrok", "http", "8000"])
        return

    # 2. Check if cloudflared is installed
    if shutil.which("cloudflared"):
        print("🚀 Запуск туннеля через Cloudflare (cloudflared)...")
        subprocess.run(["cloudflared", "tunnel", "--url", "http://localhost:8000"])
        return

    # 3. Default: Instant SSH Pinggy Tunnel (No installation required on Mac/Linux!)
    print("✨ Используем мгновенный SSH-туннель Pinggy (не требует установки программ):")
    print("👉 Нажмите Enter, чтобы запустить...")
    input()

    try:
        cmd = [
            "ssh",
            "-p", "443",
            "-R0:localhost:8000",
            "-o", "StrictHostKeyChecking=no",
            "-o", "ServerAliveInterval=30",
            "a.pinggy.io"
        ]
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n🛑 Туннель остановлен.")

if __name__ == "__main__":
    main()

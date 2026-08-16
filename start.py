#!/usr/bin/env python3
"""
🚀 1-Click Launcher & Setup Wizard for Streamer Telegram Mini App
Запуск в 1 клик: интерактивная настройка ключей, автоматическая установка зависимостей и запуск всех сервисов.
"""

import os
import sys
import subprocess
import time
import signal
import shutil
from pathlib import Path

ROOT_DIR = Path(__file__).parent.resolve()
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"
ENV_FILE = BACKEND_DIR / ".env"

# ANSI Colors
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
PURPLE = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_banner():
    print(f"""
{PURPLE}{BOLD}=============================================================
   🎮 STREAMER TELEGRAM MINI APP — 1-CLICK LAUNCHER 🚀
============================================================={RESET}
""")


def get_input(prompt_text, default_value=""):
    if default_value:
        display = f"{CYAN}{prompt_text}{RESET} [{YELLOW}{default_value}{RESET}]: "
    else:
        display = f"{CYAN}{prompt_text}{RESET}: "
    
    val = input(display).strip()
    return val if val else default_value


def interactive_setup():
    print(f"{BOLD}📝 Мастер быстрой настройки (ввод займет 1 минуту):{RESET}\n")

    # 1. BOT_TOKEN
    bot_token = ""
    while not bot_token:
        bot_token = get_input("1. Введите HTTP API Token бота (из @BotFather)")
        if not bot_token or ":" not in bot_token:
            print(f"{RED}⚠️ Токен должен иметь вид 123456789:ABC... Попробуйте еще раз.{RESET}")
            bot_token = ""

    # 2. ADMIN_IDS
    admin_id = ""
    while not admin_id:
        admin_id = get_input("2. Введите ваш личный Telegram ID (узнать в @userinfobot)")
        if not admin_id.isdigit():
            print(f"{RED}⚠️ Telegram ID должен состоять только из цифр. Попробуйте еще раз.{RESET}")
            admin_id = ""

    # 3. Streamer Info
    streamer_name = get_input("3. Никнейм/Имя стримера", "StreamerLegend")
    twitch_url = get_input("4. Ссылка на Twitch канал", "https://twitch.tv/streamer")
    kick_url = get_input("5. Ссылка на Kick канал", "https://kick.com/streamer")
    vk_url = get_input("6. Ссылка на VK Видео", "https://live.vkvideo.ru/streamer")
    telegram_channel = get_input("7. Ссылка на ваш Telegram-канал", "https://t.me/streamer_channel")

    # 4. WebApp URL
    print(f"\n{YELLOW}💡 Ссылка на Mini App (HTTPS):{RESET}")
    print("Если вы тестируете через ngrok, введите полученный адрес (например: https://abcd.ngrok-free.app).")
    print("Если пока нет публичной ссылки, нажмите Enter (будет использован http://localhost:8000 для теста в браузере).")
    webapp_url = get_input("8. HTTPS URL для Mini App", "http://localhost:8000")

    env_content = f"""# ==========================================
# Telegram Bot & Mini App Configuration
# ==========================================

BOT_TOKEN={bot_token}
WEBAPP_URL={webapp_url}
ADMIN_IDS={admin_id}

STREAMER_NAME={streamer_name}
STREAMER_AVATAR=https://images.unsplash.com/photo-1566492031773-4f4e44671857?w=150&auto=format&fit=crop&q=80
TWITCH_URL={twitch_url}
KICK_URL={kick_url}
VK_URL={vk_url}
TELEGRAM_CHANNEL={telegram_channel}

DEBUG_MODE=True
DATABASE_URL=sqlite+aiosqlite:///./tma_streamer.db

API_HOST=0.0.0.0
API_PORT=8000
"""

    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.write(env_content)

    # Save to root .env as well
    with open(ROOT_DIR / ".env", "w", encoding="utf-8") as f:
        f.write(env_content)

    print(f"\n{GREEN}✅ Конфигурация успешно сохранена в .env!{RESET}\n")


def check_and_setup_venv():
    """Checks and creates Python virtualenv, installs backend deps."""
    venv_dir = BACKEND_DIR / "venv"
    pip_bin = venv_dir / "bin" / "pip"
    python_bin = venv_dir / "bin" / "python"

    if sys.platform == "win32":
        pip_bin = venv_dir / "Scripts" / "pip.exe"
        python_bin = venv_dir / "Scripts" / "python.exe"

    if not venv_dir.exists():
        print(f"{CYAN}📦 Создание виртуального окружения Python (venv)...{RESET}")
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)

    print(f"{CYAN}🔄 Проверка и установка зависимостей бэкенда (requirements.txt)...{RESET}")
    subprocess.run([str(pip_bin), "install", "-q", "--upgrade", "pip"], check=False)
    subprocess.run([str(pip_bin), "install", "-q", "-r", str(BACKEND_DIR / "requirements.txt")], check=True)
    print(f"{GREEN}✅ Бэкенд зависимости готовы.{RESET}\n")

    return python_bin


def main():
    print_banner()

    # Step 1: Config
    needs_setup = False
    if not ENV_FILE.exists():
        needs_setup = True
    else:
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            if "123456789:ABCdefGHIjklMNOpqrsTUVwxyz" in content:
                needs_setup = True

    if needs_setup:
        interactive_setup()

    # Step 2: Setup Python backend
    python_bin = check_and_setup_venv()

    # Step 3: Launch All-In-One Backend + Telegram Bot + Mini App UI
    print(f"{GREEN}🚀 Запуск Сервера (FastAPI API + Telegram-бот + Mini App UI)...{RESET}")
    backend_process = subprocess.Popen(
        [str(python_bin), "main.py"],
        cwd=BACKEND_DIR
    )

    print(f"""
{GREEN}{BOLD}=============================================================
   ✨ ВСЕ СЕРВИСЫ УСПЕШНО ЗАПУЩЕНЫ!
============================================================={RESET}
📱 {BOLD}Telegram Mini App & API:{RESET}      http://localhost:8000
🤖 {BOLD}Telegram-бот:@nekomini_bot{RESET}    Активен и принимает /start
📚 {BOLD}Swagger документация:{RESET}        http://localhost:8000/docs

{CYAN}💡 Для открытия Mini App в Telegram со смартфона:{RESET}
1. Запустите в новом терминале: {BOLD}ngrok http 8000{RESET}
2. Скопируйте HTTPS адрес и установите в @BotFather: {BOLD}/setmenubutton{RESET}

{YELLOW}⚡ Для остановки сервера нажмите Ctrl + C{RESET}
""")

    # Handle graceful exit
    def signal_handler(sig, frame):
        print(f"\n{YELLOW}🛑 Остановка сервисов...{RESET}")
        if backend_process:
            backend_process.terminate()
        time.sleep(1)
        print(f"{GREEN}👋 Все процессы остановлены. До встречи!{RESET}")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        backend_process.wait()
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == "__main__":
    main()

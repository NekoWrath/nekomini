#!/usr/bin/env bash
# 🎮 1-Click Launch Script for Mac / Linux
set -e

# Change directory to script location
cd "$(dirname "$0")"

# Check Python 3
if command -v python3 &>/dev/null; then
    PYTHON_CMD=python3
elif command -v python &>/dev/null; then
    PYTHON_CMD=python
else
    echo "❌ Ошибка: Python 3 не найден. Пожалуйста, установите Python 3."
    exit 1
fi

chmod +x start.py
$PYTHON_CMD start.py

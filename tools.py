import subprocess
import os
import webbrowser
import time

# Словарь известных приложений (можешь добавлять свои)
APPS = {
    "браузер": "chrome",
    "хром": "chrome",
    "firefox": "firefox",
    "блокнот": "notepad",
    "проводник": "explorer",
    "калькулятор": "calc",
    "командная строка": "cmd",
    "терминал": "cmd",
    "word": "winword",
    "excel": "excel",
    "powerpoint": "powerpnt",
    "discord": r"C:\Users\Алина\AppData\Local\Discord\app-1.0.9231\Discord.exe",
    "дискорд": r"C:\Users\Алина\AppData\Local\Discord\app-1.0.9231\Discord.exe",
    "telegram": "telegram",
    "телеграм": "telegram",
    "spotify": "spotify",
    "спотифай": "spotify",
    "код": "code",
    "vscode": "code",
}


def open_application(app_name: str) -> str:
    """Открывает приложение по названию."""
    app_name_lower = app_name.lower().strip()
    exe = APPS.get(app_name_lower, app_name_lower)
    try:
        if os.path.isfile(exe):
            os.startfile(exe)
        else:
            subprocess.Popen(exe, shell=True)
        return f"Открываю {app_name}"
    except Exception as e:
        return f"Не удалось открыть {app_name}: {str(e)}"


def open_website(url: str) -> str:
    """Открывает сайт в браузере."""
    if not url.startswith("http"):
        url = "https://" + url
    try:
        webbrowser.open(url)
        return f"Открываю сайт {url}"
    except Exception as e:
        return f"Ошибка открытия сайта: {str(e)}"


def type_text(text: str) -> str:
    """Печатает текст в активном окне."""
    try:
        import pyperclip
        import pyautogui
        time.sleep(0.5)
        pyperclip.copy(text)
        pyautogui.hotkey('ctrl', 'v')
        return f"Напечатал текст: {text}"
    except Exception as e:
        return f"Ошибка при вводе текста: {str(e)}"


def create_file_with_content(filename: str, content: str) -> str:
    """Создаёт файл с содержимым на рабочем столе."""
    try:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        filepath = os.path.join(desktop, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Создал файл {filename} на рабочем столе"
    except Exception as e:
        return f"Ошибка создания файла: {str(e)}"


def read_file(filepath: str) -> str:
    """Читает содержимое файла."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return f"Содержимое файла:\n{content[:500]}"
    except Exception as e:
        return f"Ошибка чтения файла: {str(e)}"


def list_desktop_files() -> str:
    """Показывает файлы на рабочем столе."""
    try:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        files = os.listdir(desktop)
        if files:
            return "Файлы на рабочем столе: " + ", ".join(files)
        else:
            return "Рабочий стол пустой"
    except Exception as e:
        return f"Ошибка: {str(e)}"


def press_hotkey(keys: str) -> str:
    """Нажимает комбинацию клавиш."""
    try:
        import pyautogui
        key_list = keys.lower().replace(" ", "").split("+")
        pyautogui.hotkey(*key_list)
        return f"Нажал клавиши: {keys}"
    except Exception as e:
        return f"Ошибка: {str(e)}"


def take_screenshot() -> str:
    """Делает скриншот экрана."""
    try:
        import pyautogui
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        filepath = os.path.join(desktop, "screenshot.png")
        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)
        return "Скриншот сохранён на рабочем столе как screenshot.png"
    except Exception as e:
        return f"Ошибка скриншота: {str(e)}"


# Описание инструментов для Groq
TOOLS_DESCRIPTION = """
Ты — голосовой ассистент для управления компьютером. Пользователь говорит команды через Яндекс Алису, а ты их выполняешь.

Доступные действия (отвечай ТОЛЬКО в формате JSON):
{
  "action": "название_действия",
  "params": {...},
  "response": "что сказать пользователю"
}

Доступные action:
- "open_app" + params: {"app": "название"} — открыть приложение
- "open_site" + params: {"url": "адрес"} — открыть сайт
- "type_text" + params: {"text": "текст"} — напечатать текст
- "create_file" + params: {"filename": "имя.txt", "content": "содержимое"} — создать файл
- "read_file" + params: {"filepath": "путь"} — прочитать файл
- "list_files" + params: {} — показать файлы на рабочем столе
- "hotkey" + params: {"keys": "ctrl+c"} — нажать клавиши
- "screenshot" + params: {} — сделать скриншот
- "none" + params: {} — если команда непонятна

Примеры:
Команда: "открой браузер" → {"action": "open_app", "params": {"app": "браузер"}, "response": "Открываю браузер"}
Команда: "зайди на ютуб" → {"action": "open_site", "params": {"url": "youtube.com"}, "response": "Открываю YouTube"}
Команда: "открой дискорд" → {"action": "open_app", "params": {"app": "дискорд"}, "response": "Открываю Discord"}
Команда: "напиши привет мир" → {"action": "type_text", "params": {"text": "привет мир"}, "response": "Печатаю текст"}
Команда: "сделай скриншот" → {"action": "screenshot", "params": {}, "response": "Делаю скриншот"}
"""


def execute_action(action: str, params: dict) -> str:
    """Выполняет действие по названию."""
    if action == "open_app":
        return open_application(params.get("app", ""))
    elif action == "open_site":
        return open_website(params.get("url", ""))
    elif action == "type_text":
        return type_text(params.get("text", ""))
    elif action == "create_file":
        return create_file_with_content(params.get("filename", "file.txt"), params.get("content", ""))
    elif action == "read_file":
        return read_file(params.get("filepath", ""))
    elif action == "list_files":
        return list_desktop_files()
    elif action == "hotkey":
        return press_hotkey(params.get("keys", ""))
    elif action == "screenshot":
        return take_screenshot()
    elif action == "none":
        return "Команда не распознана"
    else:
        return f"Неизвестное действие: {action}"

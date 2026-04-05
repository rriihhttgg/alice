import os
import sys
os.environ['PYTHONUNBUFFERED'] = '1'

import json
import requests
from flask import Flask, request
from dotenv import load_dotenv
from collections import deque

load_dotenv()

app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Очередь команд для локального агента
command_queue = deque()

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
Команда: "напиши привет мир" → {"action": "type_text", "params": {"text": "привет мир"}, "response": "Печатаю текст"}
Команда: "сделай скриншот" → {"action": "screenshot", "params": {}, "response": "Делаю скриншот"}
"""


def log(msg):
    print(msg, flush=True)


def ask_groq(user_command: str) -> dict:
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": TOOLS_DESCRIPTION},
            {"role": "user", "content": f"Команда пользователя: {user_command}"}
        ],
        "temperature": 0.1,
        "max_tokens": 500
    }

    try:
        log("[GROQ] Отправляю запрос...")
        response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=10)
        log(f"[GROQ] Статус: {response.status_code}")
        response.raise_for_status()
        data = response.json()

        text = data["choices"][0]["message"]["content"].strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        result = json.loads(text)
        log(f"[GROQ] Результат: {result}")
        return result

    except Exception as e:
        log(f"[GROQ] Ошибка: {e}")
        return {"action": "none", "params": {}, "response": "Ошибка соединения с нейросетью"}


@app.route("/alice", methods=["POST"])
def alice_webhook():
    log("[ALICE] Получен запрос!")
    body = request.json

    user_text = body.get("request", {}).get("command", "")
    session = body.get("session", {})
    version = body.get("version", "1.0")

    log(f"[ALICE] Команда: {user_text}")

    if not user_text:
        result = {
            "version": version,
            "session": session,
            "response": {
                "text": "Привет! Я готов управлять твоим компьютером. Скажи что сделать.",
                "end_session": False
            }
        }
        return app.response_class(
            response=json.dumps(result, ensure_ascii=False),
            mimetype='application/json'
        )

    groq_result = ask_groq(user_text)

    action = groq_result.get("action", "none")
    params = groq_result.get("params", {})
    response_text = groq_result.get("response", "Выполнено")

    # Добавляем команду в очередь для локального агента
    if action != "none":
        command_queue.append({"action": action, "params": params})
        log(f"[QUEUE] Добавлена команда: {action}")

    result = {
        "version": version,
        "session": session,
        "response": {
            "text": response_text,
            "end_session": False
        }
    }
    return app.response_class(
        response=json.dumps(result, ensure_ascii=False),
        mimetype='application/json'
    )


@app.route("/poll", methods=["GET"])
def poll():
    """Локальный агент забирает команды отсюда."""
    if command_queue:
        cmd = command_queue.popleft()
        log(f"[POLL] Отдаю команду агенту: {cmd}")
        return app.response_class(
            response=json.dumps(cmd, ensure_ascii=False),
            mimetype='application/json'
        )
    return app.response_class(
        response=json.dumps({"action": "none", "params": {}}, ensure_ascii=False),
        mimetype='application/json'
    )


@app.route("/", methods=["GET"])
def index():
    return "Сервер работает! Алиса-агент активен 🤖"


if __name__ == "__main__":
    log("=" * 50)
    log("🤖 Алиса-агент запущен!")
    log("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=False)

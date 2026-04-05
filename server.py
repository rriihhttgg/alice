import os
import sys
os.environ['PYTHONUNBUFFERED'] = '1'

import json
import requests
from flask import Flask, request
from dotenv import load_dotenv
from tools import TOOLS_DESCRIPTION, execute_action

load_dotenv()

app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


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
            {
                "role": "system",
                "content": TOOLS_DESCRIPTION
            },
            {
                "role": "user",
                "content": f"Команда пользователя: {user_command}"
            }
        ],
        "temperature": 0.1,
        "max_tokens": 500
    }

    try:
        log("[GROQ] Отправляю запрос...")
        response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=10)
        log(f"[GROQ] Статус ответа: {response.status_code}")
        response.raise_for_status()
        data = response.json()

        text = data["choices"][0]["message"]["content"]
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        result = json.loads(text)
        log(f"[GROQ] Результат: {result}")
        return result

    except json.JSONDecodeError as e:
        log(f"[GROQ] Ошибка JSON: {e}")
        return {"action": "none", "params": {}, "response": "Не понял команду, попробуй ещё раз"}
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
    log(f"[ALICE] GROQ KEY: {GROQ_API_KEY[:10] if GROQ_API_KEY else 'НЕТ КЛЮЧА!'}")

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

    log(f"[ALICE] Действие: {action} | Параметры: {params}")

    if action != "none":
        execute_result = execute_action(action, params)
        log(f"[ALICE] Результат: {execute_result}")

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


@app.route("/", methods=["GET"])
def index():
    return "Сервер работает! Алиса-агент активен 🤖"


@app.route("/test", methods=["GET"])
def test():
    log("[TEST] Тест Groq...")
    result = ask_groq("открой браузер")
    return app.response_class(
        response=json.dumps(result, ensure_ascii=False),
        mimetype='application/json'
    )


if __name__ == "__main__":
    log("=" * 50)
    log("🤖 Алиса-агент запущен!")
    log("Сервер слушает на http://localhost:5000")
    log("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=False)

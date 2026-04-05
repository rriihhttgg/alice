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

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent?key={GEMINI_API_KEY}"


def log(msg):
    print(msg, flush=True)
    sys.stdout.flush()


def ask_gemini(user_command: str) -> dict:
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": TOOLS_DESCRIPTION + f"\n\nКоманда пользователя: {user_command}"
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 500,
        }
    }

    try:
        log(f"[GEMINI] Отправляю запрос...")
        response = requests.post(GEMINI_URL, json=payload, timeout=10)
        log(f"[GEMINI] Статус ответа: {response.status_code}")
        response.raise_for_status()
        data = response.json()

        text = data["candidates"][0]["content"]["parts"][0]["text"]
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        result = json.loads(text)
        log(f"[GEMINI] Результат: {result}")
        return result

    except json.JSONDecodeError as e:
        log(f"[GEMINI] Ошибка JSON: {e}, текст: {text}")
        return {"action": "none", "params": {}, "response": "Не понял команду, попробуй ещё раз"}
    except Exception as e:
        log(f"[GEMINI] Ошибка: {e}")
        return {"action": "none", "params": {}, "response": "Ошибка соединения с нейросетью"}


@app.route("/alice", methods=["POST"])
def alice_webhook():
    log("[ALICE] Получен запрос!")
    body = request.json
    log(f"[ALICE] Тело: {body}")

    user_text = body.get("request", {}).get("command", "")
    session = body.get("session", {})
    version = body.get("version", "1.0")

    log(f"[ALICE] Команда: {user_text}")
    log(f"[ALICE] API KEY: {GEMINI_API_KEY[:10] if GEMINI_API_KEY else 'НЕТ КЛЮЧА!'}")

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

    gemini_result = ask_gemini(user_text)

    action = gemini_result.get("action", "none")
    params = gemini_result.get("params", {})
    response_text = gemini_result.get("response", "Выполнено")

    log(f"[ALICE] Действие: {action} | Параметры: {params}")

    if action != "none":
        execute_result = execute_action(action, params)
        log(f"[ALICE] Результат выполнения: {execute_result}")

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
    log("[TEST] Тест Gemini...")
    result = ask_gemini("открой браузер")
    return app.response_class(
        response=json.dumps(result, ensure_ascii=False),
        mimetype='application/json'
    )


if __name__ == "__main__":
    log("=" * 50)
    log("🤖 Алиса-агент запущен!")
    log("Сервер слушает на http://localhost:5000")
    log("Вебхук для Яндекс Диалогов: /alice")
    log("Тест Gemini: http://localhost:5000/test")
    log("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=False)

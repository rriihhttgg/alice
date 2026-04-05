import json
import os
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from tools import TOOLS_DESCRIPTION, execute_action

load_dotenv()

app = Flask(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"


def ask_gemini(user_command: str) -> dict:
    """Отправляет команду в Gemini и получает действие."""
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
        response = requests.post(GEMINI_URL, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Извлекаем текст ответа
        text = data["candidates"][0]["content"]["parts"][0]["text"]

        # Убираем markdown-обёртку если есть
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        # Парсим JSON
        result = json.loads(text)
        return result

    except json.JSONDecodeError:
        return {"action": "none", "params": {}, "response": "Не понял команду, попробуй ещё раз"}
    except Exception as e:
        print(f"Ошибка Gemini: {e}")
        return {"action": "none", "params": {}, "response": "Ошибка соединения с нейросетью"}


@app.route("/alice", methods=["POST"])
def alice_webhook():
    """Принимает запросы от Яндекс Алисы."""
    body = request.json

    # Получаем текст команды от пользователя
    user_text = body.get("request", {}).get("command", "")
    session = body.get("session", {})
    version = body.get("version", "1.0")

    print(f"[Команда]: {user_text}")

    if not user_text:
        return jsonify({
            "version": version,
            "session": session,
            "response": {
                "text": "Привет! Я готов управлять твоим компьютером. Скажи что сделать.",
                "end_session": False
            }
        })

    # Спрашиваем Gemini что делать
    result = ask_gemini(user_text)

    action = result.get("action", "none")
    params = result.get("params", {})
    response_text = result.get("response", "Выполнено")

    print(f"[Действие]: {action} | [Параметры]: {params}")

    # Выполняем действие на ПК
    if action != "none":
        execute_result = execute_action(action, params)
        print(f"[Результат]: {execute_result}")

    # Отвечаем Алисе
    return jsonify({
        "version": version,
        "session": session,
        "response": {
            "text": response_text,
            "end_session": False
        }
    })


@app.route("/", methods=["GET"])
def index():
    return "Сервер работает! Алиса-агент активен 🤖"


@app.route("/test", methods=["GET"])
def test():
    """Тестовый эндпоинт — проверить что Gemini отвечает."""
    result = ask_gemini("открой браузер")
    return jsonify(result)


if __name__ == "__main__":
    print("=" * 50)
    print("🤖 Алиса-агент запущен!")
    print("Сервер слушает на http://localhost:5000")
    print("Вебхук для Яндекс Диалогов: /alice")
    print("Тест Gemini: http://localhost:5000/test")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=True)

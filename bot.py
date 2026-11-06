"""Бот @zmeikabot для VPrime: отвечает на /start кнопкой запуска игры «Змейка».

Запуск:  set VPRIME_BOT_TOKEN=<токен>  затем  python bot.py
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

TOKEN = os.environ.get("VPRIME_BOT_TOKEN")
if not TOKEN:
    sys.exit("Задайте переменную окружения VPRIME_BOT_TOKEN")

API = f"https://vprime.online/mvp/bot{TOKEN}"
GAME_URL = "https://agentsber.github.io/vprime-snake/?v=3"


def call(method, **params):
    req = urllib.request.Request(
        f"{API}/{method}",
        data=json.dumps(params).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    while True:
        try:
            with urllib.request.urlopen(req, timeout=70) as resp:
                body = json.load(resp)
        except urllib.error.HTTPError as e:
            body = json.load(e)
        if body.get("ok"):
            return body["result"]
        if body.get("error_code") == 429:
            time.sleep(body.get("parameters", {}).get("retry_after", 1))
            continue
        raise RuntimeError(f'{method}: {body.get("error_code")} {body.get("description")}')


def setup():
    call("setMyCommands", commands=[
        {"command": "start", "description": "Начать"},
        {"command": "play", "description": "Играть в Змейку"},
    ])
    call("setChatMenuButton", menu_button={
        "type": "web_app", "text": "Играть", "web_app": {"url": GAME_URL},
    })
    call("setMyDescription", description=(
        "🐍 Классическая Змейка прямо в VPrime. Нажмите «Играть», "
        "ешьте яблоки и побейте свой рекорд!"
    ))
    call("setMyShortDescription", short_description="Классическая игра Змейка 🐍")


def play_markup():
    return {"inline_keyboard": [[
        {"text": "🐍 Играть", "web_app": {"url": GAME_URL}, "style": "primary"},
    ]]}


def handle_message(msg):
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "")
    name = msg.get("from", {}).get("first_name", "")
    if text.startswith("/start") or text.startswith("/play"):
        greeting = f"Привет, {name}! " if name and text.startswith("/start") else ""
        call("sendMessage", chat_id=chat_id,
             text=greeting + "Управляйте змейкой свайпами или стрелками, ешьте яблоки "
                             "и не врезайтесь в стены. Удачи! 🍎",
             reply_markup=play_markup())
    else:
        call("sendMessage", chat_id=chat_id,
             text="Нажмите кнопку, чтобы начать игру 👇",
             reply_markup=play_markup())


def main():
    setup()
    me = call("getMe")
    print(f"Бот @{me['username']} запущен. Ctrl+C для остановки.")
    offset = 0
    while True:
        try:
            updates = call("getUpdates", offset=offset, timeout=30,
                           allowed_updates=["message", "callback_query"])
        except Exception as e:
            print("Ошибка getUpdates:", e)
            time.sleep(5)
            continue
        for update in updates:
            offset = update["update_id"] + 1
            try:
                if "message" in update:
                    handle_message(update["message"])
                elif "callback_query" in update:
                    call("answerCallbackQuery", callback_query_id=update["callback_query"]["id"])
            except Exception as e:
                print("Ошибка обработки:", e)


if __name__ == "__main__":
    main()

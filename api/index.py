from __future__ import annotations

import hmac
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
APP_URL = os.environ.get("APP_URL", "https://temu-bingo.streamlit.app").strip()
WEBHOOK_SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "").strip()
SETUP_SECRET = os.environ.get("SETUP_SECRET", "").strip()


def telegram_api(method: str, payload: dict | None = None) -> dict:
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured.")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload or {}).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "TemuBingoBot/1.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Telegram API HTTP {exc.code}: {body}") from exc
    result = json.loads(body)
    if not result.get("ok"):
        raise RuntimeError(f"Telegram API error: {result}")
    return result


def open_app_markup(chat_type: str) -> dict:
    if chat_type == "private":
        button = {"text": "🎱 Open Temu Bingo", "web_app": {"url": APP_URL}}
    else:
        button = {"text": "🎱 Open Temu Bingo", "url": APP_URL}
    return {"inline_keyboard": [[button]]}


def send_open_app_message(chat_id: int, chat_type: str, first_name: str = "") -> None:
    greeting = f"ሰላም {first_name}!" if first_name else "ሰላም!"
    text = (
        "🎱 ተሙ ቢንጎ\n\n"
        f"{greeting}\n"
        "ተሙ ቢንጎን ለመጫወት ከታች ያለውን ቁልፍ ይጫኑ።\n\n"
        "Tap the button below to open Temu Bingo."
    )
    telegram_api(
        "sendMessage",
        {"chat_id": chat_id, "text": text, "reply_markup": open_app_markup(chat_type)},
    )


class handler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _base_url(self) -> str:
        proto = (self.headers.get("x-forwarded-proto") or "https").split(",")[0].strip()
        host = (self.headers.get("x-forwarded-host") or self.headers.get("host") or "").split(",")[0].strip()
        return f"{proto}://{host}"

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        supplied_setup = params.get("setup", [""])[0]

        if supplied_setup:
            if not SETUP_SECRET or not hmac.compare_digest(supplied_setup, SETUP_SECRET):
                self._send_json(403, {"ok": False, "error": "Invalid setup secret."})
                return
            if not BOT_TOKEN:
                self._send_json(500, {"ok": False, "error": "TELEGRAM_BOT_TOKEN is not configured."})
                return
            if not WEBHOOK_SECRET:
                self._send_json(500, {"ok": False, "error": "TELEGRAM_WEBHOOK_SECRET is not configured."})
                return
            try:
                webhook_url = self._base_url() + "/api"
                webhook_result = telegram_api(
                    "setWebhook",
                    {
                        "url": webhook_url,
                        "secret_token": WEBHOOK_SECRET,
                        "allowed_updates": ["message"],
                        "drop_pending_updates": True,
                    },
                )
                command_result = telegram_api(
                    "setMyCommands",
                    {
                        "commands": [
                            {"command": "start", "description": "Start Temu Bingo"},
                            {"command": "play", "description": "Open the game"},
                            {"command": "deposit", "description": "How to add game balance"},
                            {"command": "help", "description": "Show help"},
                        ]
                    },
                )
                menu_result = None
                menu_error = None
                try:
                    menu_result = telegram_api(
                        "setChatMenuButton",
                        {
                            "menu_button": {
                                "type": "commands"
                            }
                        },
                    )
                except Exception as exc:
                    menu_error = str(exc)
                self._send_json(
                    200,
                    {
                        "ok": True,
                        "bot": "@temubingo_bot",
                        "webhook_url": webhook_url,
                        "app_url": APP_URL,
                        "set_webhook": webhook_result.get("result"),
                        "set_commands": command_result.get("result"),
                        "menu_button": "configured" if menu_result else "not configured",
                        "menu_button_error": menu_error,
                        "message": "Setup complete. Open @temubingo_bot and send /start.",
                    },
                )
            except Exception as exc:
                self._send_json(500, {"ok": False, "error": str(exc)})
            return

        self._send_json(
            200,
            {
                "ok": True,
                "service": "Temu Bingo Telegram bot",
                "bot": "@temubingo_bot",
                "app_url": APP_URL,
                "status": "ready",
            },
        )

    def do_POST(self):
        if WEBHOOK_SECRET:
            supplied_secret = self.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
            if not hmac.compare_digest(supplied_secret, WEBHOOK_SECRET):
                self._send_json(403, {"ok": False, "error": "Invalid webhook secret."})
                return
        try:
            content_length = int(self.headers.get("content-length", "0") or 0)
            raw = self.rfile.read(content_length)
            update = json.loads(raw.decode("utf-8")) if raw else {}
            message = update.get("message")
            if not message:
                self._send_json(200, {"ok": True})
                return
            chat = message.get("chat", {})
            chat_id = chat.get("id")
            if chat_id is None:
                self._send_json(200, {"ok": True})
                return
            chat_type = str(chat.get("type", "private"))
            sender = message.get("from", {})
            first_name = str(sender.get("first_name", "")).strip()
            text = str(message.get("text", "")).strip()

            if text.startswith("/start") or text.startswith("/play"):
                send_open_app_message(
                    int(chat_id),
                    chat_type,
                    first_name,
                )

            elif text.startswith("/deposit"):
                telegram_api(
                    "sendMessage",
                    {
                        "chat_id": int(chat_id),
                        "text": (
                            "💳 Balance\n\n"
                            "To continue playing, your game balance must be at least 20.\n"
                            "Balance additions are handled by the Temu Bingo admin.\n\n"
                            "No payment is processed inside this Telegram bot."
                        ),
                        "reply_markup": open_app_markup(chat_type),
                    },
                )

            elif text.startswith("/help"):
                telegram_api(
                    "sendMessage",
                    {
                        "chat_id": int(chat_id),
                        "text": (
                            "🎱 Temu Bingo commands\n\n"
                            "/start — Start Temu Bingo\n"
                            "/play — Open the game\n"
                            "/deposit — How to add game balance\n"
                            "/help — Show this help"
                        ),
                        "reply_markup": open_app_markup(chat_type),
                    },
                )

            elif text:
                send_open_app_message(
                    int(chat_id),
                    chat_type,
                    first_name,
                )

            self._send_json(200, {"ok": True})
        except Exception as exc:
            print("Webhook error:", repr(exc))
            self._send_json(200, {"ok": False, "handled": True})

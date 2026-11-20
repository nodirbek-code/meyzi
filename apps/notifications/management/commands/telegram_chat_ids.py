from django.core.management.base import BaseCommand, CommandError

from apps.notifications import telegram


class Command(BaseCommand):
    help = (
        "Botga /start yozgan chatlar ID'sini ko'rsatadi — TELEGRAM_ADMIN_CHAT_IDS ga yozish uchun. "
        "Avval TELEGRAM_BOT_TOKEN ni .env ga yozing va botga Telegram'da /start yuboring."
    )

    def handle(self, *args, **options):
        try:
            updates = telegram.call("getUpdates", {"limit": 100})
        except telegram.TelegramError as exc:
            raise CommandError(str(exc)) from None
        chats = {}
        for upd in updates:
            msg = upd.get("message") or upd.get("my_chat_member") or {}
            chat = msg.get("chat")
            if chat:
                name = (
                    chat.get("title")
                    or " ".join(filter(None, [chat.get("first_name"), chat.get("last_name")]))
                    or chat.get("username", "")
                )
                chats[chat["id"]] = f"{name} ({chat.get('type')})"
        if not chats:
            self.stdout.write(
                "Hech kim yozmagan. Telegram'da botingizga /start yuboring va qayta urinib ko'ring."
            )
            return
        for chat_id, name in chats.items():
            self.stdout.write(f"{chat_id}  —  {name}")
        self.stdout.write("\n.env: TELEGRAM_ADMIN_CHAT_IDS=" + ",".join(str(c) for c in chats))

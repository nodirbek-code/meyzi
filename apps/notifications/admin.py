from django.contrib import admin

from .models import TelegramMessage


@admin.register(TelegramMessage)
class TelegramMessageAdmin(admin.ModelAdmin):
    list_display = ["created_at", "event", "chat_id", "status", "attempts", "sent_at"]
    list_filter = ["status", "event"]
    readonly_fields = [f.name for f in TelegramMessage._meta.fields]
    actions = ["retry"]

    def has_add_permission(self, request):
        return False

    @admin.action(description="Qayta yuborish")
    def retry(self, request, queryset):
        n = queryset.exclude(status=TelegramMessage.Status.SENT).update(
            status=TelegramMessage.Status.PENDING, attempts=0, error=""
        )
        self.message_user(request, f"{n} ta xabar navbatga qaytarildi.")

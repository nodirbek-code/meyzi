"""Admin panelda moderatsiya: hamkorlar (agentlik, gid, mehmonxona) ma'lumotlarini admin O'ZGARTIRA OLMAYDI.

Admin faqat ko'radi va qaror qiladi:
- ✅ Tasdiqlash — saytga chiqadi;
- ↩️ Qaytarish — izoh yozadi (qayerda kamchilik bor), hamkorga xabar boradi, u tuzatib qayta yuboradi.

Platformaning o'z sozlamalari (komissiya, "tanlangan", moderator izohi va h.k.) — `admin_editable_fields` da.
"""

from django import forms
from django.contrib import admin, messages
from django.shortcuts import render


def _all_field_names(model) -> list[str]:
    names = [f.name for f in model._meta.concrete_fields]
    names += [f.name for f in model._meta.many_to_many]
    return names


class PartnerDataReadOnlyMixin:
    """ModelAdmin: hamma maydonlar faqat o'qish uchun (`admin_editable_fields` dan tashqari).

    Yangi yozuv qo'shish va o'chirish ham yopiq — bu ma'lumotlarni faqat hamkorning o'zi kiritadi.
    """

    admin_editable_fields: tuple[str, ...] = ()

    def get_readonly_fields(self, request, obj=None):
        extra = list(super().get_readonly_fields(request, obj))
        locked = [n for n in _all_field_names(self.model) if n not in self.admin_editable_fields]
        return list(dict.fromkeys(locked + extra))

    def get_prepopulated_fields(self, request, obj=None):
        return {}

    def has_add_permission(self, request, *args):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ReadOnlyInline(admin.TabularInline):
    """Inline: faqat ko'rish (qo'shish, o'zgartirish, o'chirish yo'q)."""

    extra = 0
    can_delete = False
    show_change_link = False

    def get_readonly_fields(self, request, obj=None):
        return _all_field_names(self.model)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ReturnNoteForm(forms.Form):
    note = forms.CharField(
        label="Kamchiliklar (hamkorga yuboriladi)",
        widget=forms.Textarea(
            attrs={"rows": 6, "cols": 80, "placeholder": "Masalan: rasmlar sifatsiz, narx yo'q…"}
        ),
        min_length=5,
        max_length=2000,
    )


def log_action(modeladmin, request, obj, message: str) -> None:
    """Admin amalini tarixga yozadi (dashboard → "Oxirgi admin amallari")."""
    modeladmin.log_change(request, obj, message)


def return_with_note(modeladmin, request, queryset, *, apply, title: str):
    """Admin action: izoh so'raydigan oraliq sahifa → `apply(obj, note)` har bir yozuv uchun."""
    if "apply" in request.POST:
        form = ReturnNoteForm(request.POST)
        if form.is_valid():
            note = form.cleaned_data["note"].strip()
            n = 0
            for obj in queryset:
                apply(obj, note)
                log_action(modeladmin, request, obj, f"↩️ Qaytarildi: {note}")
                n += 1
            modeladmin.message_user(request, f"{n} ta qaytarildi, izoh yuborildi.", messages.WARNING)
            return None
    else:
        form = ReturnNoteForm()
    return render(
        request,
        "admin/moderation_return.html",
        {
            **modeladmin.admin_site.each_context(request),
            "title": title,
            "objects": queryset,
            "form": form,
            "action": request.POST.get("action"),
            "opts": modeladmin.model._meta,
            "selected": request.POST.getlist(admin.helpers.ACTION_CHECKBOX_NAME),
        },
    )

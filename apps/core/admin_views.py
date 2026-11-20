import mimetypes
from pathlib import Path

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import FileResponse, Http404


@staff_member_required
def private_file(request, path: str):
    """Yopiq faylni faqat admin (is_staff) yuklab oladi."""
    root = Path(settings.PRIVATE_MEDIA_ROOT).resolve()
    target = (root / path).resolve()
    if root not in target.parents or not target.is_file():  # ../ bilan chiqib ketishning oldini olish
        raise Http404
    content_type, _ = mimetypes.guess_type(target.name)
    return FileResponse(open(target, "rb"), content_type=content_type or "application/octet-stream")

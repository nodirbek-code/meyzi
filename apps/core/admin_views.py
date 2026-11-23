import mimetypes
from pathlib import Path

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import FileResponse, Http404

from .files import private_storage


@staff_member_required
def private_file(request, path: str):
    """Yopiq faylni faqat admin (is_staff) yuklab oladi."""
    content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
    if getattr(settings, "CLOUDINARY_URL", ""):
        if ".." in path.split("/") or "\\" in path:
            raise Http404
        try:
            f = private_storage().open(path)
        except FileNotFoundError:
            raise Http404 from None
        return FileResponse(f, content_type=content_type, filename=path.rsplit("/", 1)[-1])
    root = Path(settings.PRIVATE_MEDIA_ROOT).resolve()
    target = (root / path).resolve()
    if root not in target.parents or not target.is_file():  # ../ bilan chiqib ketishning oldini olish
        raise Http404
    return FileResponse(open(target, "rb"), content_type=content_type)

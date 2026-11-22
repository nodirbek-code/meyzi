"""Testlar uchun haqiqiy (Pillow o'qiy oladigan) rasm va video namunalari."""

import io

from PIL import Image


def image_bytes(fmt: str = "PNG", size=(2, 2)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, (30, 120, 60)).save(buf, format=fmt)
    return buf.getvalue()


PNG = image_bytes("PNG")
JPEG = image_bytes("JPEG")
MP4 = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom"
PDF = b"%PDF-1.4\n%test\n"

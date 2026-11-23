"""/control → Media: ZIP orqali ommaviy rasm/video yuklash (faqat asosiy admin). Mantiq — `media_import`."""

import zipfile

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from .control_crud import _Staff
from .media_import import MAX_FILES, MAX_ZIP_MB, media_entries, process_batch
from .models import MediaImportJob


def _job(job: MediaImportJob, *, full: bool) -> dict:
    data = {
        "id": job.pk,
        "name": job.original_name,
        "status": job.status,
        "status_text": job.get_status_display(),
        "total": job.total,
        "processed": job.processed,
        "attached": job.attached,
        "failed": job.processed - job.attached,
        "error": job.error,
        "created_at": job.created_at,
        "finished_at": job.finished_at,
    }
    if full:
        # Avval muammolilar — admin nimani tuzatishini darhol ko'rsin
        data["report"] = sorted(job.report, key=lambda r: r["ok"])
    return data


class MediaImportListView(_Staff):
    parser_classes = [MultiPartParser]

    @extend_schema(responses={200: dict})
    def get(self, request):
        return Response([_job(j, full=False) for j in MediaImportJob.objects.all()[:15]])

    @extend_schema(
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {"file": {"type": "string", "format": "binary"}},
            }
        },
        responses={201: dict},
    )
    def post(self, request):
        upload = request.FILES.get("file")
        if upload is None:
            raise ValidationError({"file": "ZIP faylni tanlang."})
        if not upload.name.lower().endswith(".zip"):
            raise ValidationError({"file": "Faqat .zip arxiv yuklang."})
        if upload.size > MAX_ZIP_MB * 1024 * 1024:
            raise ValidationError(
                {"file": f"ZIP {MAX_ZIP_MB} MB dan katta bo'lmasin — bir necha qismga bo'ling."}
            )
        try:
            with zipfile.ZipFile(upload) as zf:
                names = media_entries(zf)
        except zipfile.BadZipFile:
            raise ValidationError(
                {"file": "Arxivni o'qib bo'lmadi — haqiqiy .zip ekanini tekshiring."}
            ) from None
        if not names:
            raise ValidationError({"file": "Arxivda fayl yo'q."})
        if len(names) > MAX_FILES:
            raise ValidationError({"file": f"Bir arxivda ko'pi bilan {MAX_FILES} ta fayl bo'lsin."})
        upload.seek(0)
        job = MediaImportJob(original_name=upload.name, created_by=request.user, total=len(names))
        job.file.save(upload.name, upload, save=False)
        job.save()
        job = process_batch(job.pk, batch=5) or job  # birinchi natijalar darhol
        return Response(_job(job, full=True), status=status.HTTP_201_CREATED)


class MediaImportDetailView(_Staff):
    @extend_schema(responses={200: dict})
    def get(self, request, pk):
        """Holat + navbatdagi qismni ishlash (sahifa ochiq turganda scheduler'ni kutmasdan)."""
        if not MediaImportJob.objects.filter(pk=pk).exists():
            raise NotFound
        process_batch(pk)
        return Response(_job(MediaImportJob.objects.get(pk=pk), full=True))

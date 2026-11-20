FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# dev — testlar va lint bilan; prod: --build-arg REQUIREMENTS=base
ARG REQUIREMENTS=dev

WORKDIR /app

COPY requirements/ requirements/
RUN pip install -r requirements/${REQUIREMENTS}.txt

COPY . .

# root bo'lmagan foydalanuvchi (prod konteynerlar shu bilan ishlaydi)
RUN useradd --create-home --uid 1000 app \
    && mkdir -p /app/media /app/private_media /app/staticfiles \
    && chown -R app:app /app/media /app/private_media /app/staticfiles

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]

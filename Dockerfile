FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .
COPY run.py .

RUN mkdir -p /app/uploads

EXPOSE 4000

# ESLATMA: migratsiyalar bu yerda AVTOMATIK ishga tushirilmaydi — mavjud Neon
# database'ni tasodifan o'zgartirib qo'ymaslik uchun. Deploy qilishdan oldin
# `alembic upgrade head` (yangi baza) yoki `alembic stamp head` (Prisma bilan
# migratsiya qilingan mavjud baza) buyrug'ini qo'lda, ongli ravishda bajaring.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-4000}"]

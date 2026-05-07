import os
import uuid
from pathlib import Path

from django.core.exceptions import ValidationError


MAX_UPLOAD_SIZE = 5 * 1024 * 1024
ALLOWED_UPLOAD_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".ppt",
    ".pptx",
    ".txt",
    ".zip",
}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/zip",
    "application/x-zip-compressed",
    "text/plain",
}
DANGEROUS_EXTENSIONS = {
    ".bat",
    ".cmd",
    ".com",
    ".dll",
    ".exe",
    ".html",
    ".js",
    ".jsp",
    ".php",
    ".ps1",
    ".py",
    ".sh",
    ".svg",
}


def secure_upload_path(folder):
    def _upload_to(instance, filename):
        extension = Path(filename).suffix.lower()
        return os.path.join(folder, f"{uuid.uuid4().hex}{extension}")

    return _upload_to


def secure_tugas_upload_path(instance, filename):
    extension = Path(filename).suffix.lower()
    return os.path.join("tugas_files", f"{uuid.uuid4().hex}{extension}")


def secure_materi_upload_path(instance, filename):
    extension = Path(filename).suffix.lower()
    return os.path.join("materi_files", f"{uuid.uuid4().hex}{extension}")


def validate_secure_uploaded_file(uploaded_file):
    if not uploaded_file:
        return

    filename = uploaded_file.name or ""
    extension = Path(filename).suffix.lower()
    content_type = getattr(uploaded_file, "content_type", "")

    if extension in DANGEROUS_EXTENSIONS or extension not in ALLOWED_UPLOAD_EXTENSIONS:
        raise ValidationError(
            "Tipe file tidak diizinkan. Unggah PDF, DOC/DOCX, PPT/PPTX, TXT, atau ZIP."
        )

    if uploaded_file.size > MAX_UPLOAD_SIZE:
        raise ValidationError("Ukuran file maksimal 5 MB.")

    if content_type and content_type not in ALLOWED_CONTENT_TYPES:
        raise ValidationError("Content-Type file tidak diizinkan.")

    header = uploaded_file.read(8)
    uploaded_file.seek(0)

    if extension == ".pdf" and not header.startswith(b"%PDF"):
        raise ValidationError("Isi file PDF tidak valid.")

    if extension in {".docx", ".pptx", ".zip"} and not header.startswith(b"PK"):
        raise ValidationError("Isi file arsip Office/ZIP tidak valid.")

    if extension in {".doc", ".ppt"} and header != b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
        raise ValidationError("Isi file Office lama tidak valid.")

    if extension == ".txt":
        try:
            uploaded_file.read().decode("utf-8")
        except UnicodeDecodeError as exc:
            uploaded_file.seek(0)
            raise ValidationError("Isi file TXT harus berupa teks UTF-8.") from exc
        uploaded_file.seek(0)

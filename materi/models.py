from django.db import models
from django.conf import settings

from elearning.upload_security import (
    secure_materi_upload_path,
    validate_secure_uploaded_file,
)


class Materi(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(
        upload_to=secure_materi_upload_path,
        validators=[validate_secure_uploaded_file],
        blank=True,
        null=True,
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="materi_uploaded",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

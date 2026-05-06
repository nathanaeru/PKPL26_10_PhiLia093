from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta


def validate_file(value):
    allowed_extensions = [".png", ".jpg", ".jpeg", ".pdf"]

    import os
    ext = os.path.splitext(value.name)[1].lower()

    if ext not in allowed_extensions:
        raise ValidationError("File harus PNG, JPG, JPEG, atau PDF")


class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()

    attachment = models.FileField(
        upload_to="forum_files/",
        null=True,
        blank=True,
        validators=[validate_file]
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def can_edit(self, user):
        if self.author != user:
            return False

        now = timezone.now()

        if user.role == "mahasiswa":
            return now <= self.created_at + timedelta(minutes=15)

        if user.role in ["dosen", "asdos"]:
            return now <= self.created_at + timedelta(minutes=30)

        return False

    def can_delete(self, user):
        return self.author == user

    def __str__(self):
        return self.title
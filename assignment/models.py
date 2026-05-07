from django.db import models
from django.conf import settings

from elearning.upload_security import (
    secure_tugas_upload_path,
    validate_secure_uploaded_file,
)


class Tugas(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(
        upload_to=secure_tugas_upload_path,
        validators=[validate_secure_uploaded_file],
        blank=True,
        null=True,
    )
    deadline = models.DateTimeField(null=True, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tugas_uploaded",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Submission(models.Model):
    tugas = models.ForeignKey(
        Tugas,
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    file = models.FileField(upload_to="submission_files/", blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("tugas", "student")
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.student.username} - {self.tugas.title}"


class Nilai(models.Model):
    submission = models.OneToOneField(Submission, on_delete=models.CASCADE)
    penilai = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    nilai_angka = models.IntegerField()
    feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Nilai {self.submission.student.username} - {self.nilai_angka}"

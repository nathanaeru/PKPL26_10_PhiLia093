from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class Submission(models.Model):
    # asumsi sudah ada
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    file = models.FileField(upload_to='submissions/')
    created_at = models.DateTimeField(auto_now_add=True)


class Nilai(models.Model):
    submission = models.OneToOneField(Submission, on_delete=models.CASCADE)
    penilai = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    nilai_angka = models.IntegerField()
    feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)



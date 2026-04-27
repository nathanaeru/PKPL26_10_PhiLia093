from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ("mahasiswa", "Mahasiswa"),
        ("asisten_dosen", "Asisten Dosen"),
        ("dosen", "Dosen"),
    )
    # Default aman: setiap pendaftar baru otomatis menjadi mahasiswa
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="mahasiswa")

    def __str__(self):
        return self.username

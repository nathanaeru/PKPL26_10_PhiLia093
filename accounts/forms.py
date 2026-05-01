from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser


class MahasiswaRegistrationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ("username", "email")
        # Field 'role' sengaja tidak dimasukkan agar tidak bisa dimanipulasi user


class CustomAuthenticationForm(AuthenticationForm):
    # Menimpa pesan error bawaan Django
    error_messages = {
        "invalid_login": "Nama pengguna atau kata sandi salah.",
        "inactive": "Akun ini tidak aktif.",
    }

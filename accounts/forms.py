from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser


class MahasiswaRegistrationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ("username", "email")
        # Field 'role' sengaja tidak dimasukkan agar tidak bisa dimanipulasi user

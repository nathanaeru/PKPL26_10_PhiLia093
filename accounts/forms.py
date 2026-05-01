from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.conf import settings
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

    def clean(self):
        # Jalankan validasi bawaan Django (cek kombinasi username & password)
        cleaned_data = super().clean()

        # Ambil objek user jika kombinasi username & password benar
        user = self.get_user()

        # Jika login valid, lakukan pengecekan role
        if user is not None:
            # Blokir akses jika yang login BUKAN mahasiswa
            if user.role != "mahasiswa":
                # Lempar error persis seperti error invalid_login bawaan
                raise forms.ValidationError(
                    self.error_messages["invalid_login"], code="invalid_login"
                )

        return cleaned_data


class StaffRegistrationForm(UserCreationForm):
    access_code = forms.CharField(
        label="Kode Akses Staf",
        widget=forms.PasswordInput(attrs={"placeholder": "Masukkan kode rahasia..."}),
        help_text="Kode ini akan menentukan otoritas Anda (Dosen/Asdos).",
    )

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ("username", "email")

    def clean_access_code(self):
        code = self.cleaned_data.get("access_code", "")

        # Validasi langsung membandingkan dengan variabel di settings
        if code not in [settings.DOSEN_ACCESS_CODE, settings.ASDOS_ACCESS_CODE]:
            raise forms.ValidationError("Kode akses tidak valid atau tidak dikenali.")

        return code

    def save(self, commit=True):
        user = super().save(commit=False)
        code = self.cleaned_data.get("access_code")

        # Penentuan role yang aman
        if code == settings.DOSEN_ACCESS_CODE:
            user.role = "dosen"
        elif code == settings.ASDOS_ACCESS_CODE:
            user.role = "asisten_dosen"

        if commit:
            user.save()
        return user


class StaffAuthenticationForm(AuthenticationForm):
    access_code = forms.CharField(
        label="Kode Akses Staf",
        widget=forms.PasswordInput(
            attrs={"placeholder": "Masukkan kode rahasia staf..."}
        ),
    )

    # Menimpa pesan error jika diperlukan
    error_messages = {
        "invalid_login": "Kredensial atau kode akses salah.",
        "inactive": "Akun ini tidak aktif.",
    }

    def clean(self):
        # Jalankan validasi bawaan (cek username dan password)
        cleaned_data = super().clean()
        access_code = cleaned_data.get("access_code")
        user = self.get_user()

        # Cek apakah kode akses sesuai dengan .env
        if access_code not in [settings.DOSEN_ACCESS_CODE, settings.ASDOS_ACCESS_CODE]:
            raise forms.ValidationError("Kode akses staf tidak valid.")

        # Pastikan user yang mencoba login benar-benar berstatus staf
        if user and user.role not in ["dosen", "asisten_dosen"]:
            raise forms.ValidationError(
                "Akses ditolak. Akun ini terdaftar sebagai Mahasiswa."
            )

        return cleaned_data

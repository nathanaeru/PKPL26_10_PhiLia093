from django import forms
from django.core.exceptions import ValidationError
from .models import Tugas, Submission


class TugasForm(forms.ModelForm):
    class Meta:
        model = Tugas
        fields = ["title", "description", "deadline", "file"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Judul tugas"}),
            "description": forms.Textarea(attrs={"rows": 4, "placeholder": "Instruksi tugas"}),
            "deadline": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                    "class": "w-full px-4 py-3 mt-1 text-black bg-white/50 border border-white/40 rounded-xl outline-none shadow-inner backdrop-blur-sm transition-all duration-300 focus:bg-white/80 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/50",
                }
            ),
        }


# ============================================================
# Mitigasi: Code Injection (CWE-434 - Unrestricted File Upload)
# Validasi ekstensi dan ukuran file dilakukan di sisi server
# agar tidak hanya bergantung pada validasi client-side.
# ============================================================
ALLOWED_SUBMISSION_EXTENSIONS = [".pdf", ".doc", ".docx", ".zip", ".rar", ".txt", ".py"]
MAX_SUBMISSION_SIZE_MB = 10
MAX_SUBMISSION_SIZE_BYTES = MAX_SUBMISSION_SIZE_MB * 1024 * 1024


class SubmissionForm(forms.ModelForm):
    """
    Form upload submisi untuk Mahasiswa.

    Keamanan yang diterapkan:
    - Validasi ekstensi file menggunakan allowlist (allowlist validation).
    - Validasi ukuran file untuk mencegah DoS melalui upload file besar.
    - Field `student` dan `tugas` tidak diekspos ke form agar tidak
      bisa dimanipulasi oleh pengguna (mass assignment prevention).
    """

    class Meta:
        model = Submission
        fields = ["file"]
        widgets = {
            "file": forms.ClearableFileInput(
                attrs={
                    "accept": ",".join(ALLOWED_SUBMISSION_EXTENSIONS),
                    "class": "block w-full text-sm text-gray-700 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer",
                }
            )
        }

    def clean_file(self):
        file = self.cleaned_data.get("file")

        if not file:
            raise ValidationError("File submisi wajib diunggah.")

        # Mitigasi: CWE-434 - Mencegah upload file berbahaya (misalnya .exe, .sh, .php)
        import os
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in ALLOWED_SUBMISSION_EXTENSIONS:
            raise ValidationError(
                f"Ekstensi file '{ext}' tidak diizinkan. "
                f"Format yang diterima: {', '.join(ALLOWED_SUBMISSION_EXTENSIONS)}."
            )

        # --- Validasi 2: Ukuran file ---
        # Mitigasi: Mencegah DoS via file berukuran sangat besar
        if file.size > MAX_SUBMISSION_SIZE_BYTES:
            raise ValidationError(
                f"Ukuran file melebihi batas maksimum {MAX_SUBMISSION_SIZE_MB} MB. "
                f"Ukuran file Anda: {file.size / (1024 * 1024):.2f} MB."
            )

        return file
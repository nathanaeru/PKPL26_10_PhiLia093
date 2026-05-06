from django import forms
from .models import Materi
from elearning.upload_security import validate_secure_uploaded_file


class MateriForm(forms.ModelForm):
    def clean_file(self):
        file = self.cleaned_data.get("file")
        validate_secure_uploaded_file(file)
        return file

    class Meta:
        model = Materi
        fields = ["title", "description", "file"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Judul materi"}),
            "description": forms.Textarea(attrs={"rows": 4, "placeholder": "Ringkasan materi"}),
            "file": forms.FileInput(
                attrs={"accept": ".pdf,.doc,.docx,.ppt,.pptx,.txt,.zip"}
            ),
        }

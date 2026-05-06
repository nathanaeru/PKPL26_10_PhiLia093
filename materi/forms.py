from django import forms
from .models import Materi


class MateriForm(forms.ModelForm):
    class Meta:
        model = Materi
        fields = ["title", "description", "file"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Judul materi"}),
            "description": forms.Textarea(attrs={"rows": 4, "placeholder": "Ringkasan materi"}),
        }

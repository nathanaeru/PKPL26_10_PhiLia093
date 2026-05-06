from django import forms
from .models import Tugas


class TugasForm(forms.ModelForm):
    class Meta:
        model = Tugas
        fields = ["title", "description", "deadline", "file"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Judul tugas"}),
            "description": forms.Textarea(attrs={"rows": 4, "placeholder": "Instruksi tugas"}),
            "deadline": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "w-full px-4 py-3 mt-1 text-black bg-white/50 border border-white/40 rounded-xl outline-none shadow-inner backdrop-blur-sm transition-all duration-300 focus:bg-white/80 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/50"}
            ),
        }

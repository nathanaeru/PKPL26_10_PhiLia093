from django import forms
from .models import Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "content", "attachment"]

        widgets = {
            "title": forms.TextInput(attrs={
                "placeholder": "Judul diskusi",
                "class": "w-full px-4 py-3 mt-1 text-black bg-white/50 border border-white/40 rounded-xl"
            }),

            "content": forms.Textarea(attrs={
                "rows": 6,
                "placeholder": "Tuliskan isi diskusi...",
                "class": "w-full px-4 py-3 mt-1 text-black bg-white/50 border border-white/40 rounded-xl"
            }),
        }
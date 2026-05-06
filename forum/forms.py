from django import forms
from .models import Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "content"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Judul diskusi", "class": "w-full px-4 py-3 mt-1 text-black bg-white/50 border border-white/40 rounded-xl outline-none shadow-inner backdrop-blur-sm transition-all duration-300 focus:bg-white/80 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/50"}),
            "content": forms.Textarea(attrs={"rows": 6, "placeholder": "Tuliskan isi diskusi...", "class": "w-full px-4 py-3 mt-1 text-black bg-white/50 border border-white/40 rounded-xl outline-none shadow-inner backdrop-blur-sm transition-all duration-300 focus:bg-white/80 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/50"}),
        }

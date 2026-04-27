from django.shortcuts import render
from .models import Post


def landing_page(request):
    # Mengambil semua post forum, diurutkan dari yang terbaru
    posts = Post.objects.all().order_by("-created_at")
    return render(request, "forum/landing.html", {"posts": posts})

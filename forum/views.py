from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Exists, OuterRef
from django.shortcuts import redirect, render

from .forms import PostForm
from .models import Post
from materi.models import Materi
from assignment.models import Submission, Tugas


def landing_page(request):
    materis = Materi.objects.all().order_by("uploaded_at")
    
    posts = Post.objects.filter(
        parent__isnull=True
    ).prefetch_related(
        "replies",
        "author"
    ).order_by("-created_at")

    tugas_filter = request.GET.get("tugas_filter", "all")
    if request.user.is_authenticated and request.user.role == "mahasiswa":
        submitted_qs = Submission.objects.filter(
            tugas=OuterRef("pk"), student=request.user
        )
        tugass = Tugas.objects.annotate(submitted=Exists(submitted_qs))
        if tugas_filter == "uncompleted":
            tugass = tugass.filter(submitted=False).order_by("uploaded_at")
        elif tugas_filter == "newest":
            tugass = tugass.order_by("-uploaded_at")
        else:
            tugass = tugass.order_by("uploaded_at")
    else:
        tugass = Tugas.objects.all()
        if tugas_filter == "newest":
            tugass = tugass.order_by("-uploaded_at")
        else:
            tugass = tugass.order_by("uploaded_at")

    return render(
        request,
        "forum/landing.html",
        {
            "materis": materis,
            "tugass": tugass,
            "tugas_filter": tugas_filter,
            "posts": posts,
        },
    )

@login_required(login_url="accounts:login")
def create_post(request):
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)

        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()

            messages.success(request, "Diskusi berhasil dibuat.")
            return redirect("forum:landing")

    else:
        form = PostForm()

    return render(request, "forum/create.html", {"form": form})

@login_required(login_url="accounts:login")
def reply_post(request, post_id):
    parent_post = Post.objects.get(id=post_id)

    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)

        if form.is_valid():
            reply = form.save(commit=False)
            reply.author = request.user
            reply.parent = parent_post
            reply.save()

            messages.success(request, "Balasan berhasil dibuat.")
            return redirect("forum:landing")

    else:
        form = PostForm()

    return render(request, "forum/reply.html", {
        "form": form,
        "parent_post": parent_post
    })

@login_required(login_url="accounts:login")
def edit_post(request, post_id):
    post = Post.objects.get(id=post_id)

    if not post.can_edit(request.user):
        messages.error(request, "Waktu edit sudah habis.")
        return redirect("forum:landing")

    if request.method == "POST":
        form = PostForm(request.POST, request.FILES, instance=post)

        if form.is_valid():
            form.save()
            messages.success(request, "Diskusi berhasil diupdate.")
            return redirect("forum:landing")

    else:
        form = PostForm(instance=post)

    return render(request, "forum/edit.html", {
        "form": form,
        "post": post
    })

@login_required(login_url="accounts:login")
def delete_post(request, post_id):
    post = Post.objects.get(id=post_id)

    if not post.can_delete(request.user):
        messages.error(request, "Tidak punya izin.")
        return redirect("forum:landing")

    post.delete()

    messages.success(request, "Diskusi berhasil dihapus.")
    return redirect("forum:landing")

from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import MateriForm
from .models import Materi


@login_required(login_url="accounts:login")
def upload_materi(request):
    if request.user.role not in ["dosen", "asisten_dosen"]:
        messages.error(request, "Hanya dosen dan asisten dosen yang dapat mengunggah materi.")
        return redirect("forum:landing")

    if request.method == "POST":
        form = MateriForm(request.POST, request.FILES)
        if form.is_valid():
            materi = form.save(commit=False)
            materi.uploaded_by = request.user
            materi.save()
            messages.success(request, "Materi berhasil diunggah.")
            return redirect("forum:landing")
    else:
        form = MateriForm()

    return render(request, "materi/upload.html", {"form": form})


@login_required(login_url="accounts:login")
def edit_materi(request, pk):
    materi = get_object_or_404(Materi, pk=pk)
    if request.user.role not in ["dosen", "asisten_dosen"]:
        messages.error(request, "Anda tidak memiliki izin untuk mengedit materi ini.")
        return redirect("forum:landing")

    if request.method == "POST":
        form = MateriForm(request.POST, request.FILES, instance=materi)
        if form.is_valid():
            form.save()
            messages.success(request, "Materi berhasil diperbarui.")
            return redirect("forum:landing")
    else:
        form = MateriForm(instance=materi)

    return render(request, "materi/upload.html", {"form": form, "edit_mode": True, "materi": materi})


@login_required(login_url="accounts:login")
def delete_materi(request, pk):
    materi = get_object_or_404(Materi, pk=pk)
    if request.user.role not in ["dosen", "asisten_dosen"]:
        messages.error(request, "Anda tidak memiliki izin untuk menghapus materi ini.")
        return redirect("forum:landing")

    if request.method == "POST":
        materi.delete()
        messages.success(request, "Materi berhasil dihapus.")
        return redirect("forum:landing")

    return render(request, "materi/confirm_delete.html", {"object": materi, "type": "materi"})

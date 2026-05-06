from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import TugasForm
from .models import Tugas


@login_required(login_url="accounts:login")
def upload_tugas(request):
    if request.user.role not in ["dosen", "asisten_dosen"]:
        messages.error(request, "Hanya dosen dan asisten dosen yang dapat mengunggah tugas.")
        return redirect("forum:landing")

    if request.method == "POST":
        form = TugasForm(request.POST, request.FILES)
        if form.is_valid():
            tugas = form.save(commit=False)
            tugas.uploaded_by = request.user
            tugas.save()
            messages.success(request, "Tugas berhasil diunggah.")
            return redirect("forum:landing")
    else:
        form = TugasForm()

    return render(request, "assignment/upload.html", {"form": form})


@login_required(login_url="accounts:login")
def edit_tugas(request, pk):
    tugas = get_object_or_404(Tugas, pk=pk)
    if request.user.role not in ["dosen", "asisten_dosen"]:
        messages.error(request, "Anda tidak memiliki izin untuk mengedit tugas ini.")
        return redirect("forum:landing")

    if request.method == "POST":
        form = TugasForm(request.POST, request.FILES, instance=tugas)
        if form.is_valid():
            form.save()
            messages.success(request, "Tugas berhasil diperbarui.")
            return redirect("forum:landing")
    else:
        form = TugasForm(instance=tugas)

    return render(request, "assignment/upload.html", {"form": form, "edit_mode": True, "tugas": tugas})


@login_required(login_url="accounts:login")
def delete_tugas(request, pk):
    tugas = get_object_or_404(Tugas, pk=pk)
    if request.user.role not in ["dosen", "asisten_dosen"]:
        messages.error(request, "Anda tidak memiliki izin untuk menghapus tugas ini.")
        return redirect("forum:landing")

    if request.method == "POST":
        tugas.delete()
        messages.success(request, "Tugas berhasil dihapus.")
        return redirect("forum:landing")

    return render(request, "assignment/confirm_delete.html", {"object": tugas, "type": "tugas"})

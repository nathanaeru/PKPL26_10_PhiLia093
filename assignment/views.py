from django.shortcuts import render
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .forms import TugasForm
from .models import Tugas, Submission, Nilai

# Create your views here.
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

def is_penilai(user):
    return user.role in ["dosen", "asisten_dosen"]

DUMMY_ASSIGNMENTS = [
    {"id": 1, "title": "Tugas 1 - SQL Query"},
    {"id": 2, "title": "Tugas 2 - Django Authentication"},
    {"id": 3, "title": "Final Project"},
]


@login_required
def daftar_tugas(request):
    return render(request, "assignment/daftar_tugas.html", {
        "assignments": DUMMY_ASSIGNMENTS
    })


@login_required
def daftar_submission(request, assignment_id):
    submissions = Submission.objects.all()

    return render(request, "assignment/daftar_submission.html", {
        "submissions": submissions,
        "assignment_id": assignment_id
    })

@login_required
def beri_nilai(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)

    # hanya dosen & asdos
    if not is_penilai(request.user):
        return HttpResponseForbidden(
            "Kamu tidak punya akses untuk memberi nilai."
        )

    try:
        nilai_obj = Nilai.objects.get(submission=submission)
    except Nilai.DoesNotExist:
        nilai_obj = None

    if request.method == "POST":
        nilai_angka = request.POST.get("nilai")
        feedback = request.POST.get("feedback")

        Nilai.objects.update_or_create(
            submission=submission,
            defaults={
                "penilai": request.user,
                "nilai_angka": nilai_angka,
                "feedback": feedback,
            },
        )

        return redirect("assignment:daftar_submission")

    return render(request, "assignment/beri_nilai.html", {
        "submission": submission,
        "nilai": nilai_obj
    })
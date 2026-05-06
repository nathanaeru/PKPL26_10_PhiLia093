from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .forms import TugasForm, SubmissionForm
from .models import Tugas, Submission, Nilai


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

    return render(
        request,
        "assignment/upload.html",
        {"form": form, "edit_mode": True, "tugas": tugas},
    )


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

    return render(
        request,
        "assignment/confirm_delete.html",
        {"object": tugas, "type": "tugas"},
    )


def is_penilai(user):
    return user.role in ["dosen", "asisten_dosen"]


@login_required
def daftar_tugas(request):
    assignments = Tugas.objects.all()
    return render(
        request,
        "assignment/daftar_tugas.html",
        {"assignments": assignments},
    )


@login_required
def daftar_submission(request, assignment_id):
    tugas = get_object_or_404(Tugas, id=assignment_id)
    submissions = Submission.objects.filter(tugas=tugas)

    return render(
        request,
        "assignment/daftar_submission.html",
        {
            "submissions": submissions,
            "assignment_id": assignment_id,
            "tugas": tugas,
        },
    )


@login_required
def beri_nilai(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)

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

        return redirect(
            "assignment:daftar_submission",
            assignment_id=submission.tugas.id,
        )

    return render(
        request,
        "assignment/beri_nilai.html",
        {
            "submission": submission,
            "nilai": nilai_obj,
        },
    )


def _require_role(user, *roles):
    return user.role in roles


@login_required(login_url="accounts:login")
def submission_status(request, tugas_id):
    if not _require_role(request.user, "mahasiswa"):
        messages.error(request, "Halaman ini hanya dapat diakses oleh mahasiswa.")
        return redirect("forum:landing")

    tugas = get_object_or_404(Tugas, pk=tugas_id)

    existing_submission = Submission.objects.filter(
        tugas=tugas, student=request.user
    ).first()

    nilai_obj = None
    if existing_submission:
        try:
            nilai_obj = Nilai.objects.get(submission=existing_submission)
        except Nilai.DoesNotExist:
            pass

    return render(
        request,
        "assignment/submission_status.html",
        {
            "tugas": tugas,
            "submission": existing_submission,
            "nilai": nilai_obj,
        },
    )


@login_required(login_url="accounts:login")
def upload_submisi(request, tugas_id):
    if not _require_role(request.user, "mahasiswa"):
        messages.error(request, "Hanya mahasiswa yang dapat mengumpulkan submisi.")
        return redirect("forum:landing")

    tugas = get_object_or_404(Tugas, pk=tugas_id)

    existing_submission = Submission.objects.filter(
        tugas=tugas, student=request.user
    ).first()

    if request.method == "POST":
        form = SubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            if existing_submission:
                existing_submission.file = form.cleaned_data["file"]
                existing_submission.save()
                messages.success(request, "Submisi Anda berhasil diperbarui.")
            else:
                submission = form.save(commit=False)
                submission.tugas = tugas
                submission.student = request.user
                submission.save()
                messages.success(request, "Submisi Anda berhasil diunggah!")

            return redirect("assignment:submission_status", tugas_id=tugas.pk)
    else:
        form = SubmissionForm()

    return render(
        request,
        "assignment/upload_submisi.html",
        {
            "form": form,
            "tugas": tugas,
            "existing_submission": existing_submission,
        },
    )


@login_required(login_url="accounts:login")
def delete_submisi(request, tugas_id):
    if not _require_role(request.user, "mahasiswa"):
        messages.error(request, "Akses ditolak.")
        return redirect("forum:landing")

    tugas = get_object_or_404(Tugas, pk=tugas_id)
    submission = get_object_or_404(
        Submission,
        tugas=tugas,
        student=request.user,
    )

    if request.method == "POST":
        submission.delete()
        messages.success(request, "Submisi berhasil dihapus.")
        return redirect("assignment:submission_status", tugas_id=tugas.pk)

    return render(
        request,
        "assignment/confirm_delete_submisi.html",
        {
            "tugas": tugas,
            "submission": submission,
        },
    )
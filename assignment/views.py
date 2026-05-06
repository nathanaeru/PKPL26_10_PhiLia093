from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

from .models import Submission, Nilai


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
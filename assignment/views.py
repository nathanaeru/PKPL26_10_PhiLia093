from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .forms import TugasForm, SubmissionForm
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

# Helper penjaga akses berbasis role
def _require_role(user, *roles):
    # Kembalikan True jika user memiliki salah satu role yang diizinkan.
    return user.role in roles

# Views: Mahasiswa Upload Submisi
# Mitigasi Broken Authentication (CWE-287):
# - @login_required memastikan hanya user terautentikasi yang bisa akses.
# - Pengecekan role 'mahasiswa' menerapkan prinsip Least Privilege:
#   staf (dosen/asdos) tidak boleh mengumpulkan submisi seperti mahasiswa
@login_required(login_url="accounts:login")
def submission_status(request, tugas_id):
    """
    Halaman status submisi mahasiswa untuk satu tugas.
    Menampilkan detail tugas dan apakah mahasiswa sudah mengumpulkan.
    Least Privilege: hanya role 'mahasiswa' yang boleh akses.
    """
    if not _require_role(request.user, "mahasiswa"):
        messages.error(request, "Halaman ini hanya dapat diakses oleh mahasiswa.")
        return redirect("forum:landing")
 
    tugas = get_object_or_404(Tugas, pk=tugas_id)
 
    # Mitigasi SQL Injection: menggunakan ORM (filter + first), bukan raw SQL
    existing_submission = Submission.objects.filter(
        tugas=tugas, student=request.user
    ).first()
 
    nilai_obj = None
    if existing_submission:
        try:
            nilai_obj = Nilai.objects.get(submission=existing_submission)
        except Nilai.DoesNotExist:
            pass
 
    return render(request, "assignment/submission_status.html", {
        "tugas": tugas,
        "submission": existing_submission,
        "nilai": nilai_obj,
    })
 
 
@login_required(login_url="accounts:login")
def upload_submisi(request, tugas_id):
    """
    View untuk mahasiswa mengunggah file submisi tugas.
    - Least Privilege (CWE-272): hanya role 'mahasiswa' yang boleh upload.
    - CSRF Protection: form menggunakan {% csrf_token %} di template.
    - Code Injection Prevention (CWE-434): validasi ekstensi & ukuran ada di SubmissionForm.
    - SQL Injection Prevention: semua DB operation via Django ORM.
    - Mencegah double submission: cek existing submission sebelum menyimpan.
    """
    if not _require_role(request.user, "mahasiswa"):
        messages.error(request, "Hanya mahasiswa yang dapat mengumpulkan submisi.")
        return redirect("forum:landing")
 
    tugas = get_object_or_404(Tugas, pk=tugas_id)
 
    # Cek apakah mahasiswa sudah mengumpulkan (mencegah duplikasi via ORM)
    existing_submission = Submission.objects.filter(
        tugas=tugas, student=request.user
    ).first()
 
    if request.method == "POST":
        form = SubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            if existing_submission:
                # Update file submisi yang sudah ada (re-submit)
                existing_submission.file = form.cleaned_data["file"]
                existing_submission.save()
                messages.success(request, "Submisi Anda berhasil diperbarui.")
            else:
                # Buat submisi baru, student & tugas di-set di server, tidak berasal dari input user (mencegah mass assignment)
                submission = form.save(commit=False)
                submission.tugas = tugas
                submission.student = request.user
                submission.save()
                messages.success(request, "Submisi Anda berhasil diunggah!")
 
            return redirect("assignment:submission_status", tugas_id=tugas.pk)
    else:
        form = SubmissionForm()
 
    return render(request, "assignment/upload_submisi.html", {
        "form": form,
        "tugas": tugas,
        "existing_submission": existing_submission,
    })
 
 
@login_required(login_url="accounts:login")
def delete_submisi(request, tugas_id):
    if not _require_role(request.user, "mahasiswa"):
        messages.error(request, "Akses ditolak.")
        return redirect("forum:landing")
 
    tugas = get_object_or_404(Tugas, pk=tugas_id)
    # Pastikan hanya submisi milik user sendiri yang bisa dihapus (ORM filter)
    submission = get_object_or_404(Submission, tugas=tugas, student=request.user)
 
    if request.method == "POST":
        submission.delete()
        messages.success(request, "Submisi berhasil dihapus.")
        return redirect("assignment:submission_status", tugas_id=tugas.pk)
 
    return render(request, "assignment/confirm_delete_submisi.html", {
        "tugas": tugas,
        "submission": submission,
    })
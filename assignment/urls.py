from django.urls import path
from . import views

app_name = "assignment"

urlpatterns = [
    path("", views.daftar_tugas, name="daftar_tugas"),

    # staf: manajemen tugas
    path("upload/", views.upload_tugas, name="upload"),
    path("<int:pk>/edit/", views.edit_tugas, name="edit"),
    path("<int:pk>/delete/", views.delete_tugas, name="delete"),

    # grading / lihat submissions
    path(
        "<int:assignment_id>/submissions/",
        views.daftar_submission,
        name="daftar_submission",
    ),
    path(
        "nilai/<int:submission_id>/",
        views.beri_nilai,
        name="beri_nilai",
    ),

    # mahasiswa: upload submisi
    path(
        "<int:tugas_id>/status/",
        views.submission_status,
        name="submission_status",
    ),
    path(
        "<int:tugas_id>/submit/",
        views.upload_submisi,
        name="upload_submisi",
    ),
    path(
        "<int:tugas_id>/submit/delete/",
        views.delete_submisi,
        name="delete_submisi",
    ),
]
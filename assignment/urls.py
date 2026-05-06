from django.urls import path
from . import views

app_name = "assignment"

urlpatterns = [
    # Staf: manajemen tugas
    path("upload/", views.upload_tugas, name="upload"),
    path("<int:pk>/edit/", views.edit_tugas, name="edit"),
    path("<int:pk>/delete/", views.delete_tugas, name="delete"),
    path("<int:assignment_id>/submissions/", views.daftar_submission, name="daftar_submission"),
    path("nilai/<int:submission_id>/", views.beri_nilai, name="beri_nilai"),

    # Mahasiswa: upload submisi
    path("<int:tugas_id>/status/", views.submission_status, name="submission_status"),
    path("<int:tugas_id>/submit/", views.upload_submisi, name="upload_submisi"),
    path("<int:tugas_id>/submit/delete/", views.delete_submisi, name="delete_submisi"),
]